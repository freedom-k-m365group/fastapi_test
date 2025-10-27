from typing import Optional
from sqlmodel import SQLModel, Field, create_engine


class SuperHero(SQLModel, table=True):
    """
    SQLModel representing a superhero with detailed attributes.

    Attributes:
        id (Optional[int]): Primary key of the hero.
        hero_name (str): Alias of the superhero; indexed for quick lookup.
        real_name (Optional[str]): Civillian or real name.
        age (Optional[int]): Age of the hero.
        origin (Optional[str]): Place or origin story of the hero.

        height_cm (Optional[float]): Height in centimeters.
        weight_kg (Optional[float]): Weight in kilograms.
        eye_color (Optional[str]): Eye color description.
        hair_color (Optional[str]): Hair color description.

        powers (Optional[str]): Comma-separated powers list.
        strength_level (Optional[int]): Strength value (0-100 scale).
        speed_level (Optional[int]): Speed value (0-100 scale).
        durability_level (Optional[int]): Durability value (0-100 scale).
        intelligence_level (Optional[int]): Intelligence value (0-100 scale).

        weaknesses (Optional[str]): Known weaknesses.
        strengths (Optional[str]): Known strengths or specialties.

        description (Optional[str]): Free text description or additional notes.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    # Basic Info
    hero_name: str = Field(index=True)
    real_name: Optional[str] = None
    age: Optional[int] = None
    origin: Optional[str] = None

    # Physical attributes
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None

    # Power attributes
    powers: Optional[str] = Field(
        default=None, description="Comma-separated list of powers"
    )
    strength_level: Optional[int] = Field(default=0, description="Scale 0-100")
    speed_level: Optional[int] = Field(default=0, description="Scale 0-100")
    durability_level: Optional[int] = Field(
        default=0, description="Scale 0-100")
    intelligence_level: Optional[int] = Field(
        default=0, description="Scale 0-100")

    # Weaknesses and strengths
    weaknesses: Optional[str] = Field(
        default=None, description="Known weaknesses")
    strengths: Optional[str] = Field(
        default=None, description="Known strengths or specialties"
    )

    # Additional notes
    description: Optional[str] = None


class SuperVillian(SQLModel, table=True):
    """
    SQLModel representing a supervillian with detailed attributes.

    Attributes:
        id (Optional[int]): Primary key of the hero.
        villian_name (str): Alias of the supervillian; indexed for quick
        lookup. real_name (Optional[str]): Civillian or real name.
        age (Optional[int]): Age of the hero.
        origin (Optional[str]): Place or origin story of the hero.

        height_cm (Optional[float]): Height in centimeters.
        weight_kg (Optional[float]): Weight in kilograms.
        eye_color (Optional[str]): Eye color description.
        hair_color (Optional[str]): Hair color description.

        powers (Optional[str]): Comma-separated powers list.
        strength_level (Optional[int]): Strength value (0-100 scale).
        speed_level (Optional[int]): Speed value (0-100 scale).
        durability_level (Optional[int]): Durability value (0-100 scale).
        intelligence_level (Optional[int]): Intelligence value (0-100 scale).

        weaknesses (Optional[str]): Known weaknesses.
        strengths (Optional[str]): Known strengths or specialties.

        description (Optional[str]): Free text description or additional notes.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    # Basic Info
    villian_name: str = Field(index=True)
    real_name: Optional[str] = None
    age: Optional[int] = None
    origin: Optional[str] = None

    # Physical attributes
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    eye_color: Optional[str] = None
    hair_color: Optional[str] = None

    # Power attributes
    powers: Optional[str] = Field(
        default=None, description="Comma-separated list of powers"
    )
    strength_level: Optional[int] = Field(default=0, description="Scale 0-100")
    speed_level: Optional[int] = Field(default=0, description="Scale 0-100")
    durability_level: Optional[int] = Field(
        default=0, description="Scale 0-100")
    intelligence_level: Optional[int] = Field(
        default=0, description="Scale 0-100")

    # Weaknesses and strengths
    weaknesses: Optional[str] = Field(
        default=None, description="Known weaknesses")
    strengths: Optional[str] = Field(
        default=None, description="Known strengths or specialties"
    )

    # Additional notes
    description: Optional[str] = None


class ComicSummary(SQLModel, table=True):
    """
    SQLModel representing a generated comic book plot summary.

    Attributes:
        id (Optional[int]): Primary key.
        hero_ids (str): Comma-separated string of hero IDs used in the summary.
        summary (str): The generated comic plot summary text.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    hero_ids: str
    villian_ids: str
    summary: str


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
