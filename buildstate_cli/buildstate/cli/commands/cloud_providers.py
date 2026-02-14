"""
CLI commands for managing Cloud Providers.
"""
import typer
from rich.console import Console
from rich.table import Table
import uuid

from ...client import BuildStateAPIError
from ...models import CloudProviderCreate, CloudProviderUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Cloud Providers")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the cloud provider"),
    display_name: str = typer.Option(..., "--display-name", help="Display name for the cloud provider"),
    description: str = typer.Option(None, "--description", help="Description of the cloud provider"),
):
    """Create a new cloud provider."""
    async def _create():
        async with await get_client() as client:
            try:
                data = CloudProviderCreate(name=name, display_name=display_name, description=description)
                response = await client.create_cloud_provider(data)
                console.print(f"[green]✅ Cloud Provider created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the cloud provider to retrieve.")):
    """Get a cloud provider by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_cloud_provider(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List cloud providers."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_cloud_providers(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the cloud provider to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    display_name: str = typer.Option(None, "--display-name", help="New display name"),
    description: str = typer.Option(None, "--description", help="New description"),
):
    """Update a cloud provider."""
    async def _update():
        async with await get_client() as client:
            try:
                data = CloudProviderUpdate(name=name, display_name=display_name, description=description)
                response = await client.update_cloud_provider(item_id, data)
                console.print(f"[green]✅ Cloud Provider updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: uuid.UUID = typer.Argument(..., help="ID of the cloud provider to delete.")):
    """Delete a cloud provider (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_cloud_provider(item_id)
                console.print(f"[green]✅ Cloud Provider with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
