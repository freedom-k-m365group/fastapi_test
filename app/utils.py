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
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.messages import HumanMessage
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


class ComicPlotOutput(BaseModel):
    """Structured output for the generated comic plot summary."""

    summary: str = Field(
        description="The full comic book plot summary (800-1600 words)."
    )


def analyze_name_and_create_hero(hero_name: str) -> SuperHero:
    """
    Generate hero attributes by prompting Gemini AI with the hero's name,
    parse the response, save the hero to the database,
    and return the created hero.

    Args:
        hero_name (str): Name of the superhero.

    Raises:
        HTTPException: If parsing the AI response fails.

    Returns:
        SuperHero: The newly created SuperHero instance.
    """

    prompt = f"""
    Here is a superhero name '{hero_name}',
    Create a JSON object describing the hero's key attributes:
    hero_name,
    real_name,
    age, origin,
    height_cm,
    weight_kg,
    eye_color,
    hair_color,
    powers (comma separated string),
    strength_level (0-100),
    speed_level (0-100),
    durability_level (0-100),
    intelligence_level (0-100),
    weaknesses,
    strengths,
    description.

    NOTE: Do NOT include any explanation or extra text. Only output JSON.
    """

    message = HumanMessage(content=prompt)

    llm_response = llm.invoke([message])

    # print(llm_response.content)

    try:
        attributes = parse_attributes(llm_response.content)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    super_hero = SuperHero(**attributes)

    with Session(engine) as session:
        session.add(super_hero)
        session.commit()
        session.refresh(super_hero)

    return super_hero


def analyze_name_and_create_villain(villain_name: str) -> SuperVillain:
    """
    Generate villain attributes by prompting Gemini AI with the villain's name,
    parse the response, save the villain to the database,
    and return the created villain.

    Args:
        villain_name (str): Name of the supervillain.

    Raises:
        HTTPException: If parsing the AI response fails.

    Returns:
        SuperVillain: The newly created SuperVillain instance.
    """

    prompt = f"""
    Here is a supervillain name '{villain_name}',
    Create a JSON object describing the villain's key attributes:
    villain_name,
    real_name,
    age, origin,
    height_cm,
    weight_kg,
    eye_color,
    hair_color,
    powers (comma separated string),
    strength_level (0-100),
    speed_level (0-100),
    durability_level (0-100),
    intelligence_level (0-100),
    weaknesses,
    strengths,
    description.

    NOTE: Do NOT include any explanation or extra text. Only output JSON.
    """

    message = HumanMessage(content=prompt)

    llm_response = llm.invoke([message])

    # print(llm_response.content)

    try:
        attributes = parse_attributes(llm_response.content)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    super_villain = SuperVillain(**attributes)

    with Session(engine) as session:
        session.add(super_villain)
        session.commit()
        session.refresh(super_villain)

    return super_villain


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
    - Format: `{"summary": "<your full 800–1600 words story here>"}`
    - **NO explanations, no tool results, no metadata, no extra text.**
    """

    tools = [find_heroes_details, find_villains_details]

    agent = create_agent(
        llm,
        tools,
        system_prompt=prompt,
        response_format=ToolStrategy(
            ComicPlotOutput,
            handle_errors=True
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

        summary = structured_response.summary

        comic = ComicSummary(
            hero_ids=json.dumps(hero_ids),
            villain_ids=json.dumps(villain_ids),
            summary=summary
        )

        with Session(engine) as session:
            session.add(comic)
            session.commit()
            session.refresh(comic)

        extracted_comic_id = comic.id

        payload = {
            "task_id": self.request.id,
            "status": "success",
            "comic_id": extracted_comic_id,
        }
        redis_manager.emit('comic_generated', payload, room=self.request.id)

        return summary

    except Exception as e:
        logger.error(f"Error in comic generation: {str(e)}")
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=5)
        else:
            raise MaxRetriesExceededError("Max retries reached")
