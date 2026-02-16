"""
Main CLI entry point for BuildState CLI.

Uses Typer for command-line interface with auto-completion and rich formatting.
"""

from typing import Optional
from pathlib import Path
import typer

from .commands import (
    auth,
    builds,
    cloud_providers,
    config,
    health,
    image_types,
    image_variants,
    os_distributions,
    os_versions,
    platforms,
    projects,
    state_codes,
    users,
)
from .utils import format_response

# Initialize Typer app
app = typer.Typer(
    name="bldst",
    help="BuildState CLI - A clean interface to the Build State API",
    add_completion=True,
    rich_markup_mode="rich",
)

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Path to config file"),
    output: str = typer.Option("table", "--output", "-o", help="Output format (table, json)"),
):
    """
    BuildState CLI - A clean interface to the Build State API.
    """
    ctx.obj = {"verbose": verbose, "config_file": config_file, "output": output, "format_response": format_response}

# Add subcommands
app.add_typer(auth.app, name="auth")
app.add_typer(builds.app, name="build")
app.add_typer(cloud_providers.app, name="cloud-provider")
app.add_typer(config.app, name="config")
app.add_typer(health.app, name="health")
app.add_typer(image_types.app, name="image-type")
app.add_typer(image_variants.app, name="image-variant")
app.add_typer(os_distributions.app, name="os-distribution")
app.add_typer(os_versions.app, name="os-version")
app.add_typer(platforms.app, name="platform")
app.add_typer(projects.app, name="project")
app.add_typer(state_codes.app, name="state-code")
app.add_typer(users.app, name="user")


if __name__ == "__main__":
    app()