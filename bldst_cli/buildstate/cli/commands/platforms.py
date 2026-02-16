"""
CLI commands for managing Platforms.
"""
import typer
from rich.console import Console

from ...client import BuildStateAPIError
from ...models import PlatformCreate, PlatformUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Platforms")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the platform"),
    cloud_provider: str = typer.Option(..., "--cloud-provider", help="Name of the cloud provider"),
    region: str = typer.Option(None, "--region", help="Cloud provider region"),
):
    """Create a new platform."""
    async def _create():
        async with await get_client() as client:
            try:
                data = PlatformCreate(name=name, cloud_provider=cloud_provider, region=region)
                response = await client.create_platform(data)
                console.print(f"[green]✅ Platform created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: str = typer.Argument(..., help="ID of the platform to retrieve.")):
    """Get a platform by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_platform(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List platforms."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_platforms(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: str = typer.Argument(..., help="ID of the platform to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    cloud_provider: str = typer.Option(None, "--cloud-provider", help="New cloud provider name"),
    region: str = typer.Option(None, "--region", help="New cloud provider region"),
):
    """Update a platform."""
    async def _update():
        async with await get_client() as client:
            try:
                data = PlatformUpdate(name=name, cloud_provider=cloud_provider, region=region)
                response = await client.update_platform(item_id, data)
                console.print(f"[green]✅ Platform updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: str = typer.Argument(..., help="ID of the platform to delete.")):
    """Delete a platform (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_platform(item_id)
                console.print(f"[green]✅ Platform with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
