import pytest
from app.app import app, lifespan
from fastapi.testclient import TestClient


@pytest.fixture
async def client():
    """Fixture with lifespan for DB setup."""
    async with lifespan(app):  # Triggers table creation
        yield TestClient(app)


def test_read_root(client):
    """Test root endpoint with template rendering."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Superhero API Tester" in response.text  # Jinja2 template content


def test_create_hero(client):
    """Test POST /heroes/ with request model."""
    response = client.post("/heroes/", json={"hero_name": "NewHero"})
    assert response.status_code == 200
    data = response.json()
    assert data["hero_name"] == "NewHero"  # Pydantic model validation


def test_create_comic(client):
    """Test comic generation (Celery integration)."""
    response = client.post(
        "/comics/", json={"hero_ids": [1], "villain_ids": [2]})
    assert response.status_code == 200
    assert "task_id" in response.json()  # Returns Celery task ID
