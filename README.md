# FastAPI SuperHero AI Project

This project is a small FastAPI application integrating SQLModel for database modeling and Google's Gemini AI through LangChain to generate and store fictional superhero attributes based on a given hero name.

## Features

- Create and store superheroes with rich attributes including physical traits, powers, strengths, weaknesses, and more.
- Automatically generate hero attributes using Gemini AI via LangChain.
- Use SQLModel as an ORM layer with SQLite by default (PostgreSQL configurable).
- FastAPI REST endpoints for creating and listing superheroes.
- Clean, Pydantic-validated API request and response models.
- Robust handling of AI output, parsing JSON responses safely.

## Tech Stack

- **FastAPI**: Async web framework for building the REST API.
- **SQLModel**: ORM and database modeling with Pydantic integration.
- **LangChain**: Integration framework for large language models.
- **Google Gemini AI**: Language model backend for generating hero attributes.
- **SQLite**: Default embedded database (switchable to PostgreSQL).
- **Poetry**: Dependency and packaging management.

## Installation

1. Clone the repository.

2. Create a virtual environment and install dependencies via Poetry:

```poetry install```

3. Configure environment variables in a `.env` file:

```GOOGLE_API_KEY="your_gemini_ai_key_here"```

4. Run the development server:

```fastapi dev .\app\app.py``` or ```poetry run fastapi dev .\app\app.py```


## API Usage

### List Heroes

- Endpoint: `GET /heroes/`
- Description: Returns a list of all superheroes in the database.

### Create Hero with AI

- Endpoint: `POST /heroes/`
- Payload example:

```json
{
"hero_name": "Night Cat"
}
```

- Description: Creates a new superhero by prompting Gemini AI for attributes based on the `hero_name`.
- Response: Returns the newly created superhero record, e.g.:

```json
{
    "id": 1,
    "real_name": "Elara Vance",
    "origin": "Orphaned at a young age, Elara Vance honed her survival skills on the streets. A mysterious encounter with an ancient feline artifact granted her enhanced agility, senses, and night vision, which she then combined with rigorous training in martial arts and parkour to become Night Cat.",
    "weight_kg": 58,
    "hair_color": "Black",
    "strength_level": 45,
    "durability_level": 35,
    "weaknesses": "Loud, sudden noises; strong, overwhelming scents; emotional attachments to her past; vulnerability to conventional attacks",
    "description": "Elara Vance, once a shadow of the city's underbelly, now stalks the night as Night Cat. With her extraordinary agility, enhanced senses, and cunning intellect, she operates as a vigilant protector of the innocent, often blurring the lines between hero and anti-hero. She uses her unique abilities and martial arts prowess to dismantle criminal organizations and bring justice to the forgotten, all while maintaining her mysterious and elusive persona.",
    "age": 28,
    "hero_name": "Night Cat",
    "height_cm": 170,
    "eye_color": "Amber",
    "powers": "Enhanced agility, superhuman reflexes, night vision, heightened senses (hearing, smell), exceptional balance, silent movement",
    "speed_level": 75,
    "intelligence_level": 80,
    "strengths": "Master of stealth, exceptional hand-to-hand combatant, tactical genius, unparalleled agility and acrobatics, highly observant"
  }
  ```

## Important Notes

- The AI prompt instructs Gemini to return a JSON-only response, parsed safely by the backend.
- The backend strips markdown and extraneous text from LLM responses to parse valid JSON.
- The project uses FastAPI lifespan context for startup initialization instead of deprecated event handlers.
- Default DB is SQLite.

## Development Standards

- Python 3.14 compatible.
- Uses pep8 for code formatting with a max line length of 88.
- Type hints are mandatory.
- Google-style docstrings for public methods.
- Code organized into `app.py`, `models.py`, and `utils.py`.
