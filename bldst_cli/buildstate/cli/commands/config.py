"""
CLI commands for managing configuration.
"""
import typer
from rich.console import Console
from rich.table import Table

from ...config import config

app = typer.Typer(help="Manage CLI configuration")
console = Console()

@app.command("set-url")
def config_set_url(url: str = typer.Argument(..., help="The base URL of the Build State API.")):
    """Set the API base URL."""
    config.api_url = url
    console.print(f"[green]✅ API URL set to: {url}[/green]")


@app.command("get-url")
def config_get_url():
    """Get the current API URL."""
    url = config.api_url
    if url:
        console.print(f"API URL: {url}")
    else:
        console.print("[red]❌ API URL not configured[/red]")
        console.print("[dim]Run 'bldst config set-url <url>' to configure[/dim]")


@app.command("show")
def config_show():
    """Show all configuration values."""
    cfg = config.get_all()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in cfg.items():
        if 'has_' in key:
            value = "✓" if value else "✗"
        elif 'token' in key and value:
            value = f"****{value[-4:]}" # Mask tokens
        table.add_row(key.replace('_', ' ').title(), str(value))

    console.print(table)


@app.command("reset")
def config_reset():
    """Reset all configuration."""
    config.reset()
    console.print("[green]✅ Configuration reset[/green]")
