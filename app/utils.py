import os
import re
import json
from typing import Any, List
from dotenv import load_dotenv
from langchain.tools import tool
from fastapi import HTTPException
from sqlmodel import Session, select
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .models import engine, SuperHero, ComicSummary, SuperVilian

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


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

    print(llm_response.content)

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


def analyze_name_and_create_vilian(vilian_name: str) -> SuperVilian:
    """
    Generate hero attributes by prompting Gemini AI with the hero's name,
    parse the response, save the hero to the database,
    and return the created hero.

    Args:
        vilian_name (str): Name of the superhero.

    Raises:
        HTTPException: If parsing the AI response fails.

    Returns:
        SuperHero: The newly created SuperHero instance.
    """

    prompt = f"""
    Here is a superhero name '{vilian_name}',
    Create a JSON object describing the hero's key attributes:
    vilian_name,
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

    print(llm_response.content)

    try:
        attributes = parse_attributes(llm_response.content)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    super_vilian = SuperVilian(**attributes)

    with Session(engine) as session:
        session.add(super_vilian)
        session.commit()
        session.refresh(super_vilian)

    return super_vilian


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
def find_vilians_details(vilian_ids_str: str) -> str:
    """
    LangChain tool to find supervilian details by their IDs.

    Args:
        vilian_ids_str (str): Comma-separated string of vilian IDs
        (e.g., "1,2,3").

    Returns:
        str: JSON string containing list of superhero details.
    """

    try:
        vilian_ids = [int(id.strip())
                      for id in vilian_ids_str.split(',') if id.strip()]
    except ValueError:
        return json.dumps({"error": "Invalid hero IDs format."
                           "Use comma-separated integers."})

    with Session(engine) as session:
        statement = select(SuperVilian).where(
            SuperVilian.id.in_(vilian_ids))  # type: ignore
        vilians = session.exec(statement).all()

    if not vilians:
        return json.dumps({"error": "No vilians found with the provided IDs."})

    vilians_data = [vilian.model_dump() for vilian in vilians]

    return json.dumps(vilians_data, indent=2)


def generate_comic_summary(hero_ids: List[int],
                           vilian_ids: List[int]) -> ComicSummary:
    """
    Use a LangChain tool-calling agent to fetch hero and vilian details
    and generate a comic book plot summary.

    Args:
        hero_ids (List[int]): List of hero IDs to include in the comic.
        vilian_ids (List[int]): List of vilian IDs to include in the comic.

    Returns:
        CommicSummary: An instance of medel CommicSummary.
    """

    prompt = """
    You are a creative comic book writer AI.
    Your task is to generate an exciting comic book plot summary
    based on the selected superheroes.

    Steps:
    1. Use these 'find_heroes_details' and 'find_vilians_details' tool
    to fetch the details of the heroes using the provided hero IDs.
    2. Analyze the heroes' or vilian's attributes, powers, weaknesses,
    strengths, and descriptions.
    3. Create a cohesive, engaging plot summary where these
    heroes and vilians team up or interact in a story.
    Make it 800-1600 words, with a beginning, middle, and an end.
    Include conflict, action, betreyal, friendships, and resolution.
    4. Ensure the plot incorporates elements from each hero's and vilian's
    profile naturally.

    NOTE: Do not add any extra explanations outside the plot summary
    in your final output.
    """

    tools = [find_heroes_details, find_vilians_details]

    agent = create_agent(llm, tools, system_prompt=prompt)

    input_messages = (f"""Generate a comic plot summary for hero IDs:
        {','.join(map(str, hero_ids))}, and vilian IDs:
        {','.join(map(str, vilian_ids))}""")

    result = agent.invoke({"messages": [{"role": "user",
                                        "content": input_messages}]})

    comic = ComicSummary(
        hero_ids=json.dumps(hero_ids),
        vilian_ids=json.dumps(vilian_ids),
        summary=result['messages'][-1].content
    )

    with Session(engine) as session:
        session.add(comic)
        session.commit()
        session.refresh(comic)

    return comic
