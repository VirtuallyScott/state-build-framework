"""
CLI commands for managing Projects.
"""
import typer
from rich.console import Console
import uuid

from ...client import BuildStateAPIError
from ...models import ProjectCreate, ProjectUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Projects")
console = Console()

@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Unique name for the project"),
    description: str = typer.Option(None, "--description", help="Description of the project"),
    parent_project_id: uuid.UUID = typer.Option(None, "--parent-id", help="ID of the parent project"),
):
    """Create a new project."""
    async def _create():
        async with await get_client() as client:
            try:
                data = ProjectCreate(name=name, description=description, parent_project_id=parent_project_id)
                response = await client.create_project(data)
                console.print(f"[green]✅ Project created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the project to retrieve.")):
    """Get a project by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_project(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List projects."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_projects(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the project to update."),
    name: str = typer.Option(None, "--name", help="New unique name"),
    description: str = typer.Option(None, "--description", help="New description"),
    parent_project_id: uuid.UUID = typer.Option(None, "--parent-id", help="New ID of the parent project"),
):
    """Update a project."""
    async def _update():
        async with await get_client() as client:
            try:
                data = ProjectUpdate(name=name, description=description, parent_project_id=parent_project_id)
                response = await client.update_project(item_id, data)
                console.print(f"[green]✅ Project updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("delete")
def delete(item_id: uuid.UUID = typer.Argument(..., help="ID of the project to delete.")):
    """Delete a project (soft delete)."""
    async def _delete():
        async with await get_client() as client:
            try:
                await client.delete_project(item_id)
                console.print(f"[green]✅ Project with ID '{item_id}' marked for deletion.[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())
