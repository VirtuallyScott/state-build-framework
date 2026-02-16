"""
CLI commands for managing Image Variants.
"""
import typer
from rich.console import Console
import uuid

from ...client import BuildStateAPIError
from ...models import ImageVariantCreate, ImageVariantUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Image Variants")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the image variant"),
    display_name: str = typer.Option(..., "--display-name", help="Display name for the image variant"),
    description: str = typer.Option(None, "--description", help="Description of the image variant"),
):
    """Create a new image variant."""
    async def _create():
        async with await get_client() as client:
            try:
                data = ImageVariantCreate(name=name, display_name=display_name, description=description)
                response = await client.create_image_variant(data)
                console.print(f"[green]✅ Image Variant created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the image variant to retrieve.")):
    """Get an image variant by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_image_variant(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List image variants."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_image_variants(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the image variant to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    display_name: str = typer.Option(None, "--display-name", help="New display name"),
    description: str = typer.Option(None, "--description", help="New description"),
):
    """Update an image variant."""
    async def _update():
        async with await get_client() as client:
            try:
                data = ImageVariantUpdate(name=name, display_name=display_name, description=description)
                response = await client.update_image_variant(item_id, data)
                console.print(f"[green]✅ Image Variant updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: uuid.UUID = typer.Argument(..., help="ID of the image variant to delete.")):
    """Delete an image variant (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_image_variant(item_id)
                console.print(f"[green]✅ Image Variant with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
