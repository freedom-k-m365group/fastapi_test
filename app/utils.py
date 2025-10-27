import os
import re
import json
from .celery import celery
from typing import Any, List
from dotenv import load_dotenv
from langchain.tools import tool
from fastapi import HTTPException
from sqlmodel import Session, select
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .models import engine, SuperHero, ComicSummary, SuperVillian

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# OUTPUT_DIR = "comics_output"
# os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def analyze_name_and_create_villian(villian_name: str) -> SuperVillian:
    """
    Generate hero attributes by prompting Gemini AI with the hero's name,
    parse the response, save the hero to the database,
    and return the created hero.

    Args:
        villian_name (str): Name of the superhero.

    Raises:
        HTTPException: If parsing the AI response fails.

    Returns:
        SuperHero: The newly created SuperHero instance.
    """

    prompt = f"""
    Here is a superhero name '{villian_name}',
    Create a JSON object describing the hero's key attributes:
    villian_name,
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

    super_villian = SuperVillian(**attributes)

    with Session(engine) as session:
        session.add(super_villian)
        session.commit()
        session.refresh(super_villian)

    return super_villian


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
def find_villians_details(villian_ids_str: str) -> str:
    """
    LangChain tool to find supervillian details by their IDs.

    Args:
        villian_ids_str (str): Comma-separated string of villian IDs
        (e.g., "1,2,3").

    Returns:
        str: JSON string containing list of superhero details.
    """

    try:
        villian_ids = [int(id.strip())
                       for id in villian_ids_str.split(',') if id.strip()]
    except ValueError:
        return json.dumps({"error": "Invalid hero IDs format."
                           "Use comma-separated integers."})

    with Session(engine) as session:
        statement = select(SuperVillian).where(
            SuperVillian.id.in_(villian_ids))  # type: ignore
        villians = session.exec(statement).all()

    if not villians:
        return json.dumps({"error":
                           "No villians found with the provided IDs."})

    villians_data = [villian.model_dump() for villian in villians]

    return json.dumps(villians_data, indent=2)


@tool
def save_comic(hero_ids: List[int],
               villian_ids: List[int], result: dict[str, str]) -> str:
    """
    Save a comic summary to the database.

    Args:
        hero_ids (List[int]): List of hero IDs.
        villain_ids (List[int]): List of villain IDs.
        summary (str): The comic plot summary.

    Returns:
        str: JSON string with the saved comic ID.
    """

    print({"hero_ids": hero_ids, "villian_ids": villian_ids,
           "summary": result.get("summary")})

    comic = ComicSummary(
        hero_ids=json.dumps(hero_ids),
        villian_ids=json.dumps(villian_ids),
        summary=result["summary"]
    )

    with Session(engine) as session:
        session.add(comic)
        session.commit()
        session.refresh(comic)

    return json.dumps({"comic_id": comic.id})


@celery.task(bind=True)
def generate_comic_summary(self,
                           hero_ids: List[int],
                           villian_ids: List[int]) -> str:
    """
    Use a LangChain tool-calling agent to fetch hero and villian details
    and generate a comic book plot summary.

    Args:
        hero_ids (List[int]): List of hero IDs to include in the comic.
        villian_ids (List[int]): List of villian IDs to include in the comic.

    Returns:
        CommicSummary: An instance of medel CommicSummary.
    """

    prompt = """
    You are a creative comic book writer AI.
    Your task is to generate an exciting comic book plot summary
    based on the selected superheroes and supervillains.

    Steps:
    1. Use the 'find_heroes_details' tool to fetch details of heroes using
    the provided hero IDs.
    2. Use the 'find_vilians_details' tool to fetch details of villains using
    the provided villain IDs.
    3. Analyze the heroes' and villains' attributes, powers, weaknesses,
    strengths, and descriptions.
    4. Create a cohesive, engaging plot summary where these heroes confront
    the villains in a story.
        Make it 800-1600 words, with a beginning, middle, and end.
        Include conflict, action, betrayal, friendships, and resolution.
    5. Ensure the plot incorporates elements from each hero's and villain's
    profile naturally.
    6. Use the 'save_comic' tool to save the generated summary, hero IDs, and
    villain IDs to the database.
    7. Return the plot summary as a single string, with no extra explanations
    or metadata.

    NOTE: ONLY RETURN THE PLOT SUMMARY AS A STRING! NOTHING ELSE!
    """

    tools = [find_heroes_details, find_villians_details, save_comic]

    agent = create_agent(llm, tools, system_prompt=prompt)

    input_messages = (f"""Generate a comic plot summary for hero IDs:
        {','.join(map(str, hero_ids))}, and villian IDs:
        {','.join(map(str, villian_ids))}""")

    result = agent.invoke({"messages": [{"role": "user",
                                         "content": input_messages}]})

    final_message = result["messages"][-1]
    if (isinstance(final_message.content, list) and
            len(final_message.content) > 0 and
            isinstance(final_message.content[0], dict) and
            "text" in final_message.content[0]):
        summary = final_message.content[0]["text"]
    elif isinstance(final_message.content, str):
        summary = final_message.content
    else:
        raise ValueError(
            f"Unexpected AIMessage content format: {final_message.content}")

    # print(summary)

    # output_file = os.path.join(OUTPUT_DIR, f"comic_{self.request.id}.py")

    # with open(output_file, 'w') as f:
    #     f.write("# Comic book plot summary\n\n")
    #     f.write(f"plot_summary = {repr(result)}\n")

    return summary
