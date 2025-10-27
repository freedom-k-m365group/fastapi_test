from typing import List
from .models import engine
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, select
from .models import SuperHero, ComicSummary, SuperVilian
from .utils import (
    analyze_name_and_create_hero,
    generate_comic_summary,
    analyze_name_and_create_vilian,
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
    vilian_ids: List[int]


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


@app.get("/vilians/")
def read_vilians():
    """
    Retrieve all supervilians from the database.

    Returns:
        List of SuperVilian instances representing all stored heroes.
    """

    with Session(engine) as session:
        vilians = session.exec(select(SuperVilian)).all()
        return vilians


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


@app.post("/vilians/")
def create_vilian(request: HeroRequest):
    """
    Create a supervilian by analyzing the vilian name with AI
    and saving the result.

    Args:
        request (HeroRequest):
        The vilian creation request containing the vilian name.

    Returns:
        SuperVilian: The created SuperVilian instance with
        generated attributes.
    """

    super_vilian = analyze_name_and_create_vilian(request.hero_name)

    return super_vilian


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
    summary = generate_comic_summary(request.hero_ids, request.vilian_ids)

    return summary


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
