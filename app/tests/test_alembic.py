import pytest
from alembic import command
from alembic.config import Config
from app.models import engine


@pytest.fixture
def alembic_cfg():
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(engine.url))  # Or in-memory
    return cfg


def test_migrate(alembic_cfg):
    """Test applying migrations."""
    command.upgrade(alembic_cfg, "head")  # Apply all
    # Verify tables exist (query DB)
    assert SuperHero.__table__.exists().run(engine)  # SQLAlchemy check
