import os
from typing import Any
from sqlmodel import Session
from dotenv import load_dotenv
from fastapi import HTTPException
from .models import engine, SuperHero
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

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
    NOTE: Respond ONLY with the JSON.
    """

    message = HumanMessage(content=prompt)

    llm_response = llm.invoke([message])

    print(llm_response.content)

    try:
        attributes = parse_hero_attributes(llm_response.content)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Create SuperHero instance and save to DB
    super_hero = SuperHero(**attributes)

    with Session(engine) as session:
        session.add(super_hero)
        session.commit()
        session.refresh(super_hero)

    return super_hero


def parse_hero_attributes(llm_response: str | Any = None) -> dict:
    """
    Parse the JSON string response from the language model into a dictionary.

    Args:
        llm_response (str | Any): The JSON string received from the AI LLM.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.

    Returns:
        dict: Parsed hero attributes suitable for SuperHero creation.
    """

    import json
    try:
        # Assuming the LLM will output JSON with attributes
        attributes = json.loads(llm_response)
        return attributes
    except json.JSONDecodeError:
        raise ValueError("Failed to parse attributes JSON from LLM response")
