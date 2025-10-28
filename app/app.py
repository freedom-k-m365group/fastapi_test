import socketio
from typing import List
from .socketio import sio
from .models import engine
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session, select
from fastapi.templating import Jinja2Templates
from .models import SuperHero, ComicSummary, SuperVillain
from .utils import (
    analyze_name_and_create_hero,
    generate_comic_summary,
    analyze_name_and_create_villain,
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
    villain_ids: List[int]


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
    print("FastAPI + Socket.IO started")
    yield
    # Shutdown code (optional)


app = FastAPI(lifespan=lifespan)


socketio_app = socketio.ASGIApp(sio, app)

app.mount("/socket.io", socketio_app)


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


@app.get("/villains/")
def read_villains():
    """
    Retrieve all supervillains from the database.

    Returns:
        List of SuperVillain instances representing all stored heroes.
    """

    with Session(engine) as session:
        villains = session.exec(select(SuperVillain)).all()
        return villains


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


@app.post("/villains/")
def create_villain(request: HeroRequest):
    """
    Create a supervillain by analyzing the villain name with AI
    and saving the result.

    Args:
        request (HeroRequest):
        The villain creation request containing the villain name.

    Returns:
        SuperVillain: The created SuperVillain instance with
        generated attributes.
    """

    super_villain = analyze_name_and_create_villain(request.hero_name)

    return super_villain


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
    summary = generate_comic_summary.delay(  # type: ignore
        request.hero_ids,
        request.villain_ids)

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


@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('message', {'data': 'Welcome to the server!'}, to=sid)


@sio.event
async def join_task(sid, data):
    task_id = data.get('task_id')
    if task_id:
        await sio.enter_room(sid, task_id)
        print(f"Client {sid} joined room '{task_id}'")
        # Confirm join
        await sio.emit('joined', {'task_id': task_id}, to=sid)


@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
