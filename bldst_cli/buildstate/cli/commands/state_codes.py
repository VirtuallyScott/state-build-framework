"""
CLI commands for managing State Codes.
"""
import typer
from rich.console import Console
import uuid

from ...client import BuildStateAPIError
from ...models import StateCodeCreate, StateCodeUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage State Codes")
console = Console()

@app.command("create")
def create(
    project_id: uuid.UUID = typer.Option(..., "--project-id", help="ID of the project"),
    code: int = typer.Option(..., "--code", help="State code"),
    name: str = typer.Option(..., "--name", help="Unique name for the state code"),
    display_name: str = typer.Option(..., "--display-name", help="Display name for the state code"),
    description: str = typer.Option(None, "--description", help="Description of the state code"),
    color: str = typer.Option(None, "--color", help="Hex color code"),
    is_terminal: bool = typer.Option(False, "--is-terminal", help="Is this a terminal state?"),
    sort_order: int = typer.Option(0, "--sort-order", help="Sort order"),
):
    """Create a new state code."""
    async def _create():
        async with await get_client() as client:
            try:
                data = StateCodeCreate(
                    project_id=project_id,
                    code=code,
                    name=name,
                    display_name=display_name,
                    description=description,
                    color=color,
                    is_terminal=is_terminal,
                    sort_order=sort_order,
                )
                response = await client.create_state_code(data)
                console.print(f"[green]✅ State Code created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the state code to retrieve.")):
    """Get a state code by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_state_code(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List state codes."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_state_codes(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the state code to update."),
    project_id: uuid.UUID = typer.Option(None, "--project-id", help="New ID of the project"),
    code: int = typer.Option(None, "--code", help="New state code"),
    name: str = typer.Option(None, "--name", help="New unique name"),
    display_name: str = typer.Option(None, "--display-name", help="New display name"),
    description: str = typer.Option(None, "--description", help="New description"),
    color: str = typer.Option(None, "--color", help="New hex color code"),
    is_terminal: bool = typer.Option(None, "--is-terminal", help="Is this a terminal state?"),
    sort_order: int = typer.Option(None, "--sort-order", help="New sort order"),
):
    """Update a state code."""
    async def _update():
        async with await get_client() as client:
            try:
                data = StateCodeUpdate(
                    project_id=project_id,
                    code=code,
                    name=name,
                    display_name=display_name,
                    description=description,
                    color=color,
                    is_terminal=is_terminal,
                    sort_order=sort_order,
                )
                response = await client.update_state_code(item_id, data)
                console.print(f"[green]✅ State Code updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: uuid.UUID = typer.Argument(..., help="ID of the state code to delete.")):
    """Delete a state code (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_state_code(item_id)
                console.print(f"[green]✅ State Code with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
