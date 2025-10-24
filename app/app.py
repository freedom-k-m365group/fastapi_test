from .models import engine
from fastapi import FastAPI
from .models import SuperHero
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Session, select
from .utils import analyze_name_and_create_hero


class HeroRequest(BaseModel):
    """
    Request body model for hero creation API.

    Attributes:
        hero_name (str): The name of the superhero to generate attributes for.
    """

    hero_name: str


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
