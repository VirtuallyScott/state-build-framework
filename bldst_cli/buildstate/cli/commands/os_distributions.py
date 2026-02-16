"""
CLI commands for managing OS Distributions.
"""
import typer
from rich.console import Console
import uuid

from ...client import BuildStateAPIError
from ...models import OSDistributionCreate, OSDistributionUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage OS Distributions")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the OS distribution"),
    display_name: str = typer.Option(..., "--display-name", help="Display name for the OS distribution"),
    description: str = typer.Option(None, "--description", help="Description of the OS distribution"),
):
    """Create a new OS distribution."""
    async def _create():
        async with await get_client() as client:
            try:
                data = OSDistributionCreate(name=name, display_name=display_name, description=description)
                response = await client.create_os_distribution(data)
                console.print(f"[green]✅ OS Distribution created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the OS distribution to retrieve.")):
    """Get an OS distribution by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_os_distribution(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List OS distributions."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_os_distributions(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the OS distribution to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    display_name: str = typer.Option(None, "--display-name", help="New display name"),
    description: str = typer.Option(None, "--description", help="New description"),
):
    """Update an OS distribution."""
    async def _update():
        async with await get_client() as client:
            try:
                data = OSDistributionUpdate(name=name, display_name=display_name, description=description)
                response = await client.update_os_distribution(item_id, data)
                console.print(f"[green]✅ OS Distribution updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: uuid.UUID = typer.Argument(..., help="ID of the OS distribution to delete.")):
    """Delete an OS distribution (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_os_distribution(item_id)
                console.print(f"[green]✅ OS Distribution with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
