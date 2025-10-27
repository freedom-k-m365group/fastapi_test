from typing import List
from .models import engine
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, select
from .models import SuperHero, ComicSummary, SuperVillian
from .utils import (
    analyze_name_and_create_hero,
    generate_comic_summary,
    analyze_name_and_create_villian,
)


class HeroRequest(BaseModel):
    """
    Request body model for hero creation API.

    Attributes:
        hero_name (str): The name of the superhero to generate attributes for.
    """

    hero_name: str


class ComicRequest(BaseModel):
    """
    Request body model for comic summary generation API.

    Attributes:
        hero_ids (List[int]): List of hero IDs to generate the comic for.
    """

    hero_ids: List[int]
    villian_ids: List[int]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI app.

    Performs resource setup before the app starts serving requests,
    and cleanup after shutdown.

    In this case, creates database tables on startup.
    """

    # Startup code: create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown code (optional)


app = FastAPI(lifespan=lifespan)


@app.get("/heroes/")
def read_heroes():
    """
    Retrieve all superheroes from the database.

    Returns:
        List of SuperHero instances representing all stored heroes.
    """

    with Session(engine) as session:
        heroes = session.exec(select(SuperHero)).all()
        return heroes


@app.get("/villians/")
def read_villians():
    """
    Retrieve all supervillians from the database.

    Returns:
        List of SuperVillian instances representing all stored heroes.
    """

    with Session(engine) as session:
        villians = session.exec(select(SuperVillian)).all()
        return villians


@app.post("/heroes/")
def create_hero(request: HeroRequest):
    """
    Create a superhero by analyzing the hero name with AI
    and saving the result.

    Args:
        request (HeroRequest):
        The hero creation request containing the hero name.

    Returns:
        SuperHero: The created SuperHero instance with generated attributes.
    """

    super_hero = analyze_name_and_create_hero(request.hero_name)

    return super_hero


@app.post("/villians/")
def create_villian(request: HeroRequest):
    """
    Create a supervillian by analyzing the villian name with AI
    and saving the result.

    Args:
        request (HeroRequest):
        The villian creation request containing the villian name.

    Returns:
        SuperVillian: The created SuperVillian instance with
        generated attributes.
    """

    super_villian = analyze_name_and_create_villian(request.hero_name)

    return super_villian


@app.post("/comics/")
def create_comic(request: ComicRequest):
    """
    Generate a comic book plot summary based on selected hero IDs using
    LangChain agent, save it to the database, and return the comic book entry.

    Args:
        request (ComicRequest): The request containing the list of hero IDs.

    Returns:
        ComicBook: The created ComicBook instance with
        the generated plot summary.
    """

    # Generate the summary using LangChain agent
    summary = generate_comic_summary.delay(request.hero_ids,  # type: ignore
                                           request.villian_ids)

    return {"task_id": summary.id}
    # return summary


@app.get("/comics/")
def read_comics():
    """
    Retrieve all comic book summaries from the database.

    Returns:
        List of ComicBook instances representing all stored comics.
    """

    with Session(engine) as session:
        comics = session.exec(select(ComicSummary)).all()
        return comics
