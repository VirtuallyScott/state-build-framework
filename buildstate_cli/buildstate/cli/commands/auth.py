"""
CLI commands for authentication.
"""
import typer
from rich.console import Console

from ...client import BuildStateClient, BuildStateAPIError
from ...config import config
from ..utils import run_async, handle_api_error

app = typer.Typer(help="Manage authentication")
console = Console()

@app.command("login")
def auth_login(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Login with username/password to get JWT token."""
    async def _login():
        # API URL must be set to login
        if not config.api_url:
            console.print("[red]❌ API URL not configured. Please run 'buildctl config set-url <url>' first.[/red]")
            raise typer.Exit(1)
            
        async with BuildStateClient(config.api_url) as client:
            try:
                token_response = await client.login(username, password)
                config.jwt_token = token_response.access_token
                console.print("[green]✅ Login successful, JWT token stored.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_login())


@app.command("logout")
def auth_logout():
    """Clear stored JWT token."""
    config.clear_jwt_token()
    console.print("[green]✅ JWT token cleared.[/green]")

@app.command("set-key")
def auth_set_key(api_key: str = typer.Argument(..., help="The API key to use for authentication.")):
    """Set and store the API key for authenticating with the Build State API."""
    config.set_api_key(api_key)
    console.print("[green]✅ API key has been set and stored securely.[/green]")

@app.command("clear-key")
def auth_clear_key():
    """Clear the stored API key."""
    config.clear_api_key()
    console.print("[green]✅ Stored API key has been cleared.[/green]")
