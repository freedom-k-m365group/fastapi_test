from typing import Optional
from sqlmodel import SQLModel, Field


class SuperHero(SQLModel, table=True):
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
