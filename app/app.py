from .models import engine
from fastapi import FastAPI
from sqlmodel import SQLModel
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown code (optional)

app = FastAPI(lifespan=lifespan)
