"""
CLI commands for managing users.
"""
import typer
from rich.console import Console
from rich.table import Table
import uuid

from ...client import BuildStateAPIError
from ...models import UserCreate, UserUpdate
from ..utils import run_async, get_client, handle_api_error

app = typer.Typer(help="Manage users")
console = Console()

@app.command("create")
def user_create(
    username: str = typer.Option(..., "--username", "-u", help="Username"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    full_name: str = typer.Option(None, "--full-name", help="Full name"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="Password"),
):
    """Create a new user."""
    async def _create():
        async with await get_client() as client:
            try:
                user_data = UserCreate(username=username, email=email, full_name=full_name, password=password)
                user = await client.create_user(user_data)
                console.print(f"[green]✅ User created successfully![/green]")
                console.print(f"User ID: [cyan]{user.id}[/cyan]")
                console.print(f"Username: [cyan]{user.username}[/cyan]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_create())


@app.command("get")
def user_get(user_id: int = typer.Argument(..., help="ID of the user to retrieve.")):
    """Get user details."""
    async def _get():
        async with await get_client() as client:
            try:
                user = await client.get_user(user_id)
                table = Table(title=f"User Details for {user.username}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("ID", str(user.id))
                table.add_row("Username", user.username)
                table.add_row("Email", user.email)
                table.add_row("Full Name", user.full_name or "N/A")
                table.add_row("Is Active", "Yes" if user.is_active else "No")
                table.add_row("Created At", str(user.created_at))
                table.add_row("Updated At", str(user.updated_at))
                console.print(table)
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_get())

@app.command("me")
def user_me():
    """Get details for the currently authenticated user."""
    async def _get():
        async with await get_client() as client:
            try:
                user = await client.get_current_user()
                table = Table(title=f"User Details for {user.username}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("ID", str(user.id))
                table.add_row("Username", user.username)
                table.add_row("Email", user.email)
                table.add_row("Full Name", user.full_name or "N/A")
                table.add_row("Is Active", "Yes" if user.is_active else "No")
                table.add_row("Created At", str(user.created_at))
                table.add_row("Updated At", str(user.updated_at))
                console.print(table)
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_get())


@app.command("update")
def user_update(
    user_id: int = typer.Argument(..., help="ID of the user to update."),
    email: str = typer.Option(None, "--email", "-e", help="New email address"),
    full_name: str = typer.Option(None, "--full-name", help="New full name"),
    is_active: bool = typer.Option(None, "--active/--inactive", help="Set active status"),
):
    """Update user details."""
    async def _update():
        async with await get_client() as client:
            try:
                update_data = UserUpdate(email=email, full_name=full_name, is_active=is_active)
                user = await client.update_user(user_id, update_data)
                console.print(f"[green]✅ User '{user.username}' updated successfully![/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_update())
