"""
CLI commands for managing Image Types.
"""
import typer
from rich.console import Console

from ...client import BuildStateAPIError
from ...models import ImageTypeCreate, ImageTypeUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Image Types")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the image type"),
    description: str = typer.Option(None, "--description", help="Description of the image type"),
):
    """Create a new image type."""
    async def _create():
        async with await get_client() as client:
            try:
                data = ImageTypeCreate(name=name, description=description)
                response = await client.create_image_type(data)
                console.print(f"[green]✅ Image Type created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: str = typer.Argument(..., help="ID of the image type to retrieve.")):
    """Get an image type by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_image_type(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List image types."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_image_types(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: str = typer.Argument(..., help="ID of the image type to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    description: str = typer.Option(None, "--description", help="New description"),
):
    """Update an image type."""
    async def _update():
        async with await get_client() as client:
            try:
                data = ImageTypeUpdate(name=name, description=description)
                response = await client.update_image_type(item_id, data)
                console.print(f"[green]✅ Image Type updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: str = typer.Argument(..., help="ID of the image type to delete.")):
    """Delete an image type (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_image_type(item_id)
                console.print(f"[green]✅ Image Type with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
