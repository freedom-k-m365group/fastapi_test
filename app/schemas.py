from typing import List
from pydantic import BaseModel, Field


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


class ComicPlotOutput(BaseModel):
    """Structured output for the generated comic plot summary."""

    summary_title: str = Field(
        description="The title of the comic book plot summary."
    )
    summary: str = Field(
        description="The full comic book plot summary (800-1600 words)."
    )
