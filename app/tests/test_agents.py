import json
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock
from app.models import SuperHero, SuperVillain, ComicSummary
from sqlmodel import Session, create_engine, SQLModel, select
from app.agents import (
    parse_attributes,
    find_heroes_details,
    find_villains_details,
    generate_comic_summary,
    analyze_name_and_create_hero,
    analyze_name_and_create_villain,
)


@pytest.fixture(name="session")
def in_memory_engine() -> Generator[Session, None, None]:
    """SQLite :memory: engine that is torn down after each test."""

    sqlite_url = "sqlite:///:memory:"
    connect_args = {"check_same_thread": False}

    engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

    SQLModel.metadata.create_all(engine)          # <-- creates tables

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)            # <-- clean up


@pytest.fixture
def mock_llm():
    """Patch the global `llm.invoke` used by the agent and creation helpers."""

    with patch("app.agents.llm.invoke") as mock:
        yield mock


@pytest.fixture
def mock_redis_manager():
    """Patch the socket.io RedisManager used inside the Celery task."""

    with patch("app.agents.redis_manager") as mock:
        yield mock


def seed_db(session: Session):
    """Insert a few heroes & villains and return their IDs."""

    hero1 = SuperHero(
        hero_name="Batman",
        real_name="Bruce Wayne",
        age=38,
        powers="Martial Arts, Gadgets",
        strength_level=85,
    )

    hero2 = SuperHero(
        hero_name="Superman",
        real_name="Clark Kent",
        age=35,
        powers="Flight, Super Strength, Heat Vision",
        strength_level=100,
    )

    villain1 = SuperVillain(
        villain_name="Joker",
        real_name="Unknown",
        age=40,
        powers="Chaos, Intelligence",
        intelligence_level=98,
    )

    villain2 = SuperVillain(
        villain_name="Lex Luthor",
        real_name="Lex Luthor",
        age=45,
        powers="Genius, Technology",
        intelligence_level=99,
    )

    session.add_all([hero1, hero2, villain1, villain2])
    session.commit()

    for obj in (hero1, hero2, villain1, villain2):
        session.refresh(obj)

    return {
        "hero_ids": [hero1.id, hero2.id],
        "villain_ids": [villain1.id, villain2.id],
    }


def test_parse_attributes():
    """Test parsing LLM response (LangChain message handling)."""

    # Normal JSON wrapped in markdown
    raw = '```json\n{"hero_name":"IronMan","age":45}\n```'
    assert parse_attributes(raw) == {"hero_name": "IronMan", "age": 45}

    # Plain JSON (no fences)
    raw = '{"hero_name":"Spider-Man","age":20}'
    assert parse_attributes(raw) == {"hero_name": "Spider-Man", "age": 20}

    # Invalid JSON → ValueError
    with pytest.raises(ValueError, match="No JSON object found"):
        parse_attributes("not json at all")

    with pytest.raises(ValueError, match="Failed to parse JSON"):
        parse_attributes('{"broken": "json"')


def test_analyze_name_and_create_hero(mock_llm, session: Session):
    """Test hero creation with mocked LangChain model."""

    # Mock the LLM response
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {
            "hero_name": "Wolverine",
            "real_name": "Logan",
            "age": 150,
            "powers": "Healing, Claws",
            "strength_level": 90,
        }
    )
    mock_llm.return_value = mock_resp

    hero = analyze_name_and_create_hero("Wolverine")

    # Assert model fields
    assert hero.hero_name == "Wolverine"
    assert hero.real_name == "Logan"
    assert hero.age == 150
    assert hero.powers == "Healing, Claws"
    assert hero.strength_level == 90

    # Verify it was persisted
    stmt = select(SuperHero).where(SuperHero.id == hero.id)
    persisted = session.exec(stmt).one()
    assert persisted.hero_name == "Wolverine"


def test_analyze_name_and_create_villain(mock_llm, session: Session):
    """Test villain creation with mocked LangChain model."""

    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {
            "villain_name": "Magneto",
            "real_name": "Erik Lehnsherr",
            "age": 85,
            "powers": "Magnetism",
            "intelligence_level": 95,
        }
    )
    mock_llm.return_value = mock_resp

    villain = analyze_name_and_create_villain("Magneto")

    assert villain.villain_name == "Magneto"
    assert villain.real_name == "Erik Lehnsherr"
    assert villain.age == 85
    assert villain.powers == "Magnetism"

    stmt = select(SuperVillain).where(SuperVillain.id == villain.id)
    persisted = session.exec(stmt).one()
    assert persisted.villain_name == "Magneto"


def test_find_heroes_details_tool(session: Session):
    """Test LangChain @tool for fetching heroes."""

    # Seed DB
    ids = seed_db(session)["hero_ids"]
    hero_ids_str = ",".join(map(str, ids))

    result_json = find_heroes_details(hero_ids_str)
    data = json.loads(result_json)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["hero_name"] == "Batman"
    assert data[1]["hero_name"] == "Superman"


def test_find_villains_details_tool(session: Session):
    """Test LangChain @tool for fetching villains."""

    ids = seed_db(session)["villain_ids"]
    villain_ids_str = ",".join(map(str, ids))

    result_json = find_villains_details(villain_ids_str)
    data = json.loads(result_json)

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["villain_name"] == "Joker"
    assert data[1]["villain_name"] == "Lex Luthor"


def test_find_heroes_details_tool_invalid_ids(session: Session):
    from app.agents import find_heroes_details

    assert json.loads(find_heroes_details("999,998")) == {
        "error": "No heroes found with the provided IDs."
    }

    assert json.loads(find_heroes_details("not,a,number")) == {
        "error": "Invalid hero IDs format. Use comma-separated integers."
    }


@pytest.mark.celery
def test_generate_comic_summary(
    celery_session_worker,
    session: Session,
    mock_llm,
    mock_redis_manager,
):
    """
    Full end-to-end test of the Celery task:
      • tools are called,
      • LLM is asked,
      • comic is saved,
      • socket.io emits the result.
    """

    # ------------------------------------------------------------------- #
    # 1. Seed DB with known entities
    # ------------------------------------------------------------------- #
    ids = seed_db(session)
    hero_ids = ids["hero_ids"]
    villain_ids = ids["villain_ids"]

    # ------------------------------------------------------------------- #
    # 2. Mock the *agent* (create_agent → invoke)
    # ------------------------------------------------------------------- #
    mock_agent = MagicMock()
    with patch("app.agents.create_agent", return_value=mock_agent):
        # The agent will receive a dict with a "messages" key.
        # We will make it return a structure that mimics a real LangChain run.
        final_message = MagicMock()
        final_message.content = [
            {"type": "text", "text": "The heroes win the day!"}
        ]
        mock_agent.invoke.return_value = {"messages": [final_message]}

        # ----------------------------------------------------------------
        # 3. Run the task *synchronously* inside the test worker
        # ----------------------------------------------------------------
        task = generate_comic_summary.delay(hero_ids,  # type: ignore
                                            villain_ids)
        summary = task.get(timeout=10)          # blocks until worker finishes

        assert summary == "The heroes win the day!"

    # ------------------------------------------------------------------- #
    # 4. Verify that the *save_comic* tool was called
    # ------------------------------------------------------------------- #
    save_call = None
    for call_args in mock_agent.invoke.call_args_list:
        # The agent receives {"messages": [...]}
        msgs = call_args[0][0]["messages"]
        for m in msgs:
            if isinstance(m, dict) and m.get("role") == "assistant":
                # The assistant message contains tool calls; we look for save_comic
                content = m.get("content", "")
                if "save_comic" in content:
                    # In a real run the tool call is a structured dict – we just check it was attempted
                    save_call = True
                    break
        if save_call:
            break

    # If the agent never called save_comic, the test would fail earlier because
    # the task raises MaxRetriesExceededError when comic_id cannot be extracted.
    assert save_call is True

    # ------------------------------------------------------------------- #
    # 5. Verify DB contains the comic
    # ------------------------------------------------------------------- #
    comics = session.exec(select(ComicSummary)).all()
    assert len(comics) == 1
    comic = comics[0]
    assert json.loads(comic.hero_ids) == hero_ids
    assert json.loads(comic.villain_ids) == villain_ids
    assert comic.summary == "The heroes win the day!"

    # ------------------------------------------------------------------- #
    # 6. Verify socket.io emission
    # ------------------------------------------------------------------- #
    mock_redis_manager.emit.assert_called_once_with(
        "comic_generated",
        {
            "task_id": task.id,
            "status": "success",
            "comic_id": comic.id,
        },
        room=task.id,
    )
