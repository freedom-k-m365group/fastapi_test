import os
import re
import json
import logging
import socketio
from .celery import celery
from typing import Any, List
from dotenv import load_dotenv
from langchain.tools import tool
from fastapi import HTTPException
from .schemas import ComicPlotOutput
from sqlmodel import Session, select
from langchain.agents import create_agent
from celery.exceptions import MaxRetriesExceededError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.structured_output import ToolStrategy
from .models import engine, SuperHero, ComicSummary, SuperVillain

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# OUTPUT_DIR = "comics_output"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

redis_manager = socketio.RedisManager(
    'redis://localhost:6379', write_only=True)


def analyze_name_and_create_hero(hero_name: str) -> SuperHero:
    """
    Generate hero attributes using a LangChain agent with structured output,
    validate via Pydantic, save to the database, and return the created hero.

    This uses LangChain's create_agent with no tools (since generation is pure
    LLM), but leverages response_format for structured SuperHero output.
    This ensures:
    - Automatic validation and retries on schema errors.
    - Better functionality: Handles LLM inconsistencies via ToolStrategy's
    error handling.

    Args:
        hero_name (str): Name of the superhero.

    Raises:
        HTTPException: If agent fails or parsing/validation fails after
        retries.

    Returns:
        SuperHero: The newly created SuperHero instance.
    """

    system_prompt = """
    You are a comic book hero generator. Your task is to create a
    complete, valid profile for the given superhero name.

    ### STRICT RULES:

    - Analyze the name and generate creative, fitting attributes.
    - Output ONLY the structured response matching the 'SuperHero' schema.
    - ALL fields MUST be present, truthy, and match types/ranges:
      - hero_name: string (exact input name)
      - real_name: string (full name, non-empty)
      - age: int (18–10000)
      - origin: string (non-empty, e.g., city/planet)
      - height_cm: float (150.0–550.0)
      - weight_kg: float (50.0–550.0)
      - eye_color: string (non-empty, descriptive)
      - hair_color: string (non-empty, descriptive)
      - powers: string (comma-separated, at least 2)
      - strength_level: int (20–100)
      - speed_level: int (20–100)
      - durability_level: int (20–100)
      - intelligence_level: int (30–100)
      - weaknesses: string (comma-separated, at least one)
      - strengths: string (comma-separated, at least one)
      - description: string (2–3 sentences, non-empty)
    - Use a bright, inspiring tone.
    - NOTE: No extras, explanations, or invalid data.
    """

    agent = create_agent(
        llm,
        tools=[],
        system_prompt=system_prompt,
        response_format=ToolStrategy(
            SuperHero,
            handle_errors="Fix to match SuperHero schema exactly."
        )
    )

    user_message = f"Generate profile for superhero: {hero_name}"

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]})

        structured_hero = result.get("structured_response")
        if not structured_hero:
            raise ValueError(
                "Agent failed to generate structured hero profile")

        with Session(engine) as session:
            session.add(structured_hero)
            session.commit()
            session.refresh(structured_hero)

        return structured_hero

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate hero: {str(e)}")


def analyze_name_and_create_villain(villain_name: str) -> SuperVillain:
    """
    Generate villain attributes using a LangChain agent with structured output,
    validate via Pydantic, save to the database, and return the created
    villain.

    Similar to hero function: Uses agent for structured output to ensure
    reliability, with automatic retries on schema mismatches.

    Args:
        villain_name (str): Name of the supervillain.

    Raises:
        HTTPException: If agent fails or parsing/validation fails after
        retries.

    Returns:
        SuperVillain: The newly created SuperVillain instance.
    """

    system_prompt = """
    You are a comic book villain generator. Your task is to create a complete,
    valid profile for the given supervillain name.

    ### STRICT RULES:

    - Analyze the name and generate creative, fitting attributes.
    - Output ONLY the structured response matching the SuperVillain schema.
    - ALL fields MUST be present, truthy, and match types/ranges:
      - villain_name: string (exact input name)
      - real_name: string (full name, non-empty)
      - age: int (18–10000)
      - origin: string (non-empty, e.g., dimension/tragedy)
      - height_cm: float (160.0–700.0)
      - weight_kg: float (60.0–700.0)
      - eye_color: string (non-empty, descriptive)
      - hair_color: string (non-empty, descriptive)
      - powers: string (comma-separated, at least 2)
      - strength_level: int (20–100)
      - speed_level: int (20–100)
      - durability_level: int (20–100)
      - intelligence_level: int (30–100)
      - weaknesses: string (comma-separated, at least one)
      - strengths: string (comma-separated, at least one)
      - description: string (2–3 sentences, non-empty)
    - Use a dark, menacing tone.
    - NO extras, explanations, or invalid data.
    """

    agent = create_agent(
        llm,
        tools=[],
        system_prompt=system_prompt,
        response_format=ToolStrategy(
            SuperVillain,
            handle_errors="Fix to match SuperVillain schema exactly."
        )
    )

    user_message = f"Generate profile for supervillain: {villain_name}"

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]})

        structured_villain = result.get("structured_response")
        if not structured_villain:
            raise ValueError(
                "Agent failed to generate structured villain profile")

        with Session(engine) as session:
            session.add(structured_villain)
            session.commit()
            session.refresh(structured_villain)

        return structured_villain

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate villain: {str(e)}")


def parse_attributes(llm_response: str | Any = None) -> dict:
    """
    Parse the JSON string response from the language model into a dictionary.

    Args:
        llm_response (str | Any): The JSON string received from the AI LLM.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.

    Returns:
        dict: Parsed hero attributes suitable for SuperHero creation.
    """

    # Remove markdown code fences like ```json or ```
    cleaned_response = re.sub(
        r"(?s)```.*?\n", "", llm_response)  # Remove opening ```
    cleaned_response = re.sub(
        r"```", "", cleaned_response)  # Remove closing ```
    cleaned_response = cleaned_response.strip()

    # Extract JSON object using regex to find {...}
    json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)

    if not json_match:
        raise ValueError("No JSON object found in LLM response")

    json_str = json_match.group(0)

    try:
        attributes = json.loads(json_str)
        return attributes
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")


@tool
def find_heroes_details(hero_ids_str: str) -> str:
    """
    LangChain tool to find superhero details by their IDs.

    Args:
        hero_ids_str (str): Comma-separated string of hero IDs (e.g., "1,2,3").

    Returns:
        str: JSON string containing list of superhero details.
    """

    try:
        hero_ids = [int(id.strip())
                    for id in hero_ids_str.split(',') if id.strip()]
    except ValueError:
        return json.dumps({"error": "Invalid hero IDs format."
                           "Use comma-separated integers."})

    with Session(engine) as session:
        statement = select(SuperHero).where(
            SuperHero.id.in_(hero_ids))  # type: ignore
        heroes = session.exec(statement).all()

    if not heroes:
        return json.dumps({"error": "No heroes found with the provided IDs."})

    heroes_data = [hero.model_dump() for hero in heroes]

    return json.dumps(heroes_data, indent=2)


@tool
def find_villains_details(villain_ids_str: str) -> str:
    """
    LangChain tool to find supervillain details by their IDs.

    Args:
        villain_ids_str (str): Comma-separated string of villain IDs
        (e.g., "1,2,3").

    Returns:
        str: JSON string containing list of superhero details.
    """

    try:
        villain_ids = [int(id.strip())
                       for id in villain_ids_str.split(',') if id.strip()]
    except ValueError:
        return json.dumps({"error": "Invalid hero IDs format."
                           "Use comma-separated integers."})

    with Session(engine) as session:
        statement = select(SuperVillain).where(
            SuperVillain.id.in_(villain_ids))  # type: ignore
        villains = session.exec(statement).all()

    if not villains:
        return json.dumps({"error":
                           "No villains found with the provided IDs."})

    villains_data = [villain.model_dump() for villain in villains]

    return json.dumps(villains_data, indent=2)


@celery.task(bind=True)
def generate_comic_summary(self, hero_ids: List[int],
                           villain_ids: List[int]) -> str:
    """
    Use a LangChain tool-calling agent to fetch hero and villain details
    and generate a comic book plot summary.

    Args:
        hero_ids (List[int]): List of hero IDs to include in the comic.
        villain_ids (List[int]): List of villain IDs to include in the comic.

    Returns:
        str: The generated plot summary (for Celery result).
    """

    if not hero_ids or not villain_ids:
        raise ValueError("Must provide at least one hero and one villain")

    prompt = """
    You are a creative comic book writer AI. Your task is to generate an
    exciting, dramatic comic book plot summary based on the selected
    superheroes and supervillains.

    ### STRICT INSTRUCTIONS (FOLLOW EXACTLY):

    1. **FIRST**: Call the `find_heroes_details` tool with the provided hero
    IDs to get full hero profiles.

    2. **SECOND**: Call the `find_villains_details` tool with the provided
    villain IDs to get full villain profiles.

    3. **DO NOT** assume or invent any hero/villain details. Use **only** the
    data returned from the tools.

    4. **THEN**: Analyze all fetched profiles to determine:
    - **Average Power Level** = (strength + speed + durability + intelligence)
    / 4 per character
    - **Team Power** = average of all heroes vs. average of all villains
    - **Strategic Matchups**: How powers, strengths, and weaknesses interact
    (e.g., fire vs. ice, tech vs. magic)

    5. **DECIDE WINNER**:
    - Heroes win if: higher team power + better synergy + exploiting villain
    weaknesses
    - Villains win if: significantly higher team power + better synergy +
    exploiting heroe weaknesses OR major hero betrayal
    - But: **Good ultimately triumphs in spirit** — even if villains win a
    battle, heroes show resilience, hope, or set up future victory

    6. **WRITE THE PLOT**:
    - 800–1600 words
    - Structure: **Beginning** (setup, stakes), **Middle** (conflict, action,
    betrayal), **End** (climax, resolution)
    - Include: action, hope/despair, friendship/family bonds, moral struggle,
    dramatic twists
    - Naturally weave in **every** hero and villain’s powers, personality, and
    backstory.

    7. **FINAL OUTPUT**:
    - Return **ONLY** the structured response using the `ComicPlotOutput`
    schema.
    - Format: `{"summary_title": "<the title for this plot summary>",
    "summary": "<your full 800–1600 words story here>"}`
    - **NO explanations, no tool results, no metadata, no extra text.**
    """

    tools = [find_heroes_details, find_villains_details]

    agent = create_agent(
        llm,
        tools,
        system_prompt=prompt,
        response_format=ToolStrategy(
            ComicPlotOutput,
            handle_errors="Fix to match ComicPlotOutput schema exactly."
        )
    )

    input_messages = (f"""Generate a comic plot summary for hero IDs:
        {','.join(map(str, hero_ids))}, and villain IDs:
        {','.join(map(str, villain_ids))}""")

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": input_messages}]})

        structured_response = result.get("structured_response")
        if not structured_response:
            raise ValueError("No structured response generated by agent")

        summary_title = structured_response.summary_title
        summary = structured_response.summary

        comic = ComicSummary(
            hero_ids=json.dumps(hero_ids),
            villain_ids=json.dumps(villain_ids),
            summary_title=summary_title,
            summary=summary
        )

        with Session(engine) as session:
            session.add(comic)
            session.commit()
            session.refresh(comic)

        payload = {
            "task_id": self.request.id,
            "status": "success",
            "comic_id": comic.id,
            "comic_title": comic.summary_title,
        }
        redis_manager.emit('comic_generated', payload, room=self.request.id)

        return summary

    except Exception as e:
        logger.error(f"Error in comic generation: {str(e)}")
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=5)
        else:
            raise MaxRetriesExceededError("Max retries reached")
