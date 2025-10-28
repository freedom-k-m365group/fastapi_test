import os
import click
from alembic import command
from alembic.config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALEMBIC_INI_PATH = os.path.join(BASE_DIR, "alembic.ini")


def _get_alembic_config() -> Config:
    """
    Create and configure an Alembic Config object.
    Sets the correct sqlalchemy.url from your models.py or alembic.ini.
    """

    if not os.path.exists(ALEMBIC_INI_PATH):
        raise click.ClickException(
            f"Alembic config not found at {ALEMBIC_INI_PATH}")

    cfg = Config(ALEMBIC_INI_PATH)

    from app.models import engine
    cfg.set_main_option("sqlalchemy.url", str(engine.url))

    return cfg


@click.group()
def cli():
    """Management CLI for FastAPI + SQLModel project [using alembic]."""
    pass


@cli.command()
@click.option(
    "--first-time",
    is_flag=True,
    help="Generate initial schema migration and apply it."
)
@click.option(
    "--revision",
    type=str,
    help="Generate a migration with the given message and apply it."
)
def migrate(first_time: bool, revision: str):
    """Run Alembic migrations."""
    cfg = _get_alembic_config()

    if first_time and revision:
        raise click.UsageError(
            "Cannot use --first-time and --revision together.")

    try:
        if first_time:
            click.echo("Generating initial schema migration...")
            command.revision(
                cfg,
                message="initial schema",
                autogenerate=True,
                head="head"
            )
            click.echo("Applying migrations...")
            command.upgrade(cfg, "head")
            click.echo("Initial schema migration complete.")
        elif revision:
            click.echo(f"Generating migration: {revision}...")
            command.revision(
                cfg,
                message=revision,
                autogenerate=True,
                head="head"
            )
            click.echo("Applying migrations...")
            command.upgrade(cfg, "head")
            click.echo(f"Migration '{revision}' complete.")
        else:
            raise click.UsageError(
                "Must specify either --first-time or --revision <message>.")
    except Exception as e:
        click.echo(f"Migration failed: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
