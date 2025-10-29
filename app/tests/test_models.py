import pytest
from sqlmodel import Session
from typing import Generator
from sqlmodel import create_engine, SQLModel
from app.models import SuperHero, SuperVillain, ComicSummary


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


def test_create_hero_model(session: Session):
    """Test creating and saving a SuperHero instance."""

    hero = SuperHero(
        hero_name="TestHero",
        real_name="John Doe",
        age=30,
        powers="Flight, Super Strength",
        strength_level=80
    )

    session.add(hero)
    session.commit()
    session.refresh(hero)

    assert hero.id is not None

    assert hero.age == 30
    assert hero.strength_level == 80

    assert hero.hero_name == "TestHero"
    assert hero.real_name == "John Doe"
    assert hero.powers == "Flight, Super Strength"


def test_create_villain_model(session: Session):
    """Test creating and saving a SuperVillain instance."""

    villain = SuperVillain(
        villain_name="TestVillain",
        real_name="Jane Doe",
        age=30,
        powers="Flight, Super Strength",
        strength_level=80
    )

    session.add(villain)
    session.commit()
    session.refresh(villain)

    assert villain.id is not None

    assert villain.age == 30
    assert villain.strength_level == 80

    assert villain.villain_name == "TestVillain"
    assert villain.real_name == "Jane Doe"
    assert villain.powers == "Flight, Super Strength"


def test_create_comic_summary_model(session: Session):
    """Test creating and saving a CommicSummary instance."""

    summary = ComicSummary(
        hero_ids="[1, 2]",
        villain_ids="[1, 2]",
        summary_title="Comic itle",
        summary="Comic summary"
    )

    session.add(summary)
    session.commit()
    session.refresh(summary)

    assert summary.id is not None

    assert summary.hero_ids == "[1, 2]"
    assert summary.villain_ids == "[1, 2]"

    assert summary.summary_title == "Comic itle"
    assert summary.summary == "Comic summary"
