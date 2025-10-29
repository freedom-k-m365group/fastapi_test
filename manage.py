# manage.py
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
    "--autogenerate",
    is_flag=True,
    default=True,
    help="Autogenerate the migration based on model changes (default: True)."
)
@click.option(
    "--message", "-m",
    type=str,
    required=True,
    help="The message for the new revision."
)
@click.option(
    "--depends-on",
    type=str,
    help="""Specify parent revision(s) for branching/merging
    (supports partial identifiers)."""
)
def revision(autogenerate: bool, message: str, depends_on: str):
    """Generate a new Alembic revision file (without applying it)."""
    cfg = _get_alembic_config()

    try:
        click.echo(
            f"""Generating revision: {message}
            (autogenerate: {autogenerate})...""")
        command.revision(
            cfg,
            message=message,
            autogenerate=autogenerate,
            depends_on=depends_on,
            head="head"
        )
        click.echo(f"Revision '{message}' generated successfully.")
    except Exception as e:
        click.echo(f"Revision generation failed: {e}", err=True)
        raise click.Abort()


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
@click.option(
    "--upgrade",
    type=str,
    help="""Upgrade to the given target
    (supports partial/relative identifiers, e.g., +2, head, ae1)."""
)
@click.option(
    "--downgrade",
    type=str,
    help="""Downgrade to the given target
    (supports partial/relative identifiers, e.g., -1, base, ae1)."""
)
def migrate(first_time: bool, revision: str, upgrade: str, downgrade: str):
    """Run Alembic migrations, upgrades, or downgrades."""
    cfg = _get_alembic_config()

    options = [first_time, bool(revision), bool(upgrade), bool(downgrade)]
    if options.count(True) > 1:
        raise click.UsageError(
            """Options --first-time, --revision, --upgrade,
            and --downgrade are mutually exclusive.""")

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
        elif upgrade:
            click.echo(f"Upgrading to target: {upgrade}...")
            command.upgrade(cfg, upgrade)
            click.echo(f"Upgrade to '{upgrade}' complete.")
        elif downgrade:
            click.echo(f"Downgrading to target: {downgrade}...")
            command.downgrade(cfg, downgrade)
            click.echo(f"Downgrade to '{downgrade}' complete.")
        else:
            raise click.UsageError(
                """Must specify one of: --first-time, --revision <message>,
                --upgrade <target>, or --downgrade <target>.""")
    except Exception as e:
        click.echo(f"Migration failed: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--current",
    is_flag=True,
    help="Show the current revision (default if no options specified)."
)
@click.option(
    "--history",
    is_flag=True,
    help="Show migration history."
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show verbose details for history or current."
)
@click.option(
    "--rev-range", "-r",
    type=str,
    help="""Specify a revision range for history
    (supports partial/relative, e.g., -3:current)."""
)
def info(current: bool, history: bool, verbose: bool, rev_range: str):
    """Get information about the current state or history of migrations."""
    cfg = _get_alembic_config()

    if not current and not history:
        # Default to showing current if no flags
        current = True

    try:
        if current:
            click.echo("Showing current revision...")
            command.current(cfg)
        if history:
            click.echo(
                f"""Showing history (range: {rev_range or 'all'},
                verbose: {verbose})...""")
            command.history(cfg, rev_range=rev_range, verbose=verbose)
    except Exception as e:
        click.echo(f"Info command failed: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
