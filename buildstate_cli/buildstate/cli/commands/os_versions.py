"""
CLI commands for managing OS Versions.
"""
import typer
from rich.console import Console

from ...client import BuildStateAPIError
from ...models import OSVersionCreate, OSVersionUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage OS Versions")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="OS name (e.g., 'Red Hat Enterprise Linux', 'Ubuntu')"),
    version: str = typer.Option(..., "--version", help="Version string (e.g., '8.8', '20.04')"),
):
    """Create a new OS version."""
    async def _create():
        async with await get_client() as client:
            try:
                data = OSVersionCreate(name=name, version=version)
                response = await client.create_os_version(data)
                console.print(f"[green]✅ OS Version created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: str = typer.Argument(..., help="ID of the OS version to retrieve.")):
    """Get an OS version by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_os_version(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List OS versions."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_os_versions(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: str = typer.Argument(..., help="ID of the OS version to update."),
    name: str = typer.Option(None, "--name", help="New OS name"),
    version: str = typer.Option(None, "--version", help="New version string"),
):
    """Update an OS version."""
    async def _update():
        async with await get_client() as client:
            try:
                data = OSVersionUpdate(name=name, version=version)
                response = await client.update_os_version(item_id, data)
                console.print(f"[green]✅ OS Version updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: str = typer.Argument(..., help="ID of the OS version to delete.")):
    """Delete an OS version (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_os_version(item_id)
                console.print(f"[green]✅ OS Version with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
