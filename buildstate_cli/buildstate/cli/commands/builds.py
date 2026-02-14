"""
CLI commands for managing Builds.
"""
import typer
from rich.console import Console
import uuid
from typing import Optional

from ...client import BuildStateAPIError
from ...models import BuildCreate, BuildUpdate, BuildStateCreate, BuildFailureCreate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Builds")
console = Console()

@app.command("create")
def create(
    build_number: str = typer.Option(..., "--build-number", help="Build number or identifier"),
    project_id: uuid.UUID = typer.Option(..., "--project-id", help="ID of the project"),
    platform_id: uuid.UUID = typer.Option(..., "--platform-id", help="ID of the platform"),
    os_version_id: uuid.UUID = typer.Option(..., "--os-version-id", help="ID of the OS version"),
    image_type_id: uuid.UUID = typer.Option(..., "--image-type-id", help="ID of the image type"),
    created_by: Optional[str] = typer.Option(None, "--created-by", help="User or process that created the build"),
    concourse_pipeline_url: Optional[str] = typer.Option(None, "--concourse-url", help="URL to the Concourse pipeline"),
    concourse_job_name: Optional[str] = typer.Option(None, "--concourse-job", help="Name of the Concourse job"),
):
    """Create a new build."""
    async def _create():
        async with await get_client() as client:
            try:
                data = BuildCreate(
                    build_number=build_number,
                    project_id=project_id,
                    platform_id=platform_id,
                    os_version_id=os_version_id,
                    image_type_id=image_type_id,
                    created_by=created_by,
                    concourse_pipeline_url=concourse_pipeline_url,
                    concourse_job_name=concourse_job_name,
                )
                response = await client.create_build(data)
                console.print(f"[green]✅ Build created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())

@app.command("get")
def get(item_id: uuid.UUID = typer.Argument(..., help="ID of the build to retrieve.")):
    """Get a build by ID."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_build(item_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())

@app.command("list")
def list_items(
    skip: int = typer.Option(0, "--skip", help="Number of items to skip"),
    limit: int = typer.Option(100, "--limit", help="Number of items to return"),
):
    """List builds."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_builds(skip=skip, limit=limit)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())

@app.command("update")
def update(
    item_id: uuid.UUID = typer.Argument(..., help="ID of the build to update."),
    current_state: Optional[int] = typer.Option(None, "--current-state", help="New current state code"),
    status: Optional[str] = typer.Option(None, "--status", help="New status"),
    ami_id: Optional[str] = typer.Option(None, "--ami-id", help="AMI ID"),
    image_id: Optional[str] = typer.Option(None, "--image-id", help="Image ID"),
):
    """Update a build."""
    async def _update():
        async with await get_client() as client:
            try:
                data = BuildUpdate(current_state=current_state, status=status, ami_id=ami_id, image_id=image_id)
                response = await client.update_build(item_id, data)
                console.print(f"[green]✅ Build updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())

@app.command("add-state")
def add_state(
    build_id: uuid.UUID = typer.Argument(..., help="ID of the build to add a state to."),
    state: int = typer.Option(..., "--state", help="State code"),
    status: str = typer.Option(..., "--status", help="Status of the state"),
):
    """Add a state to a build."""
    async def _add_state():
        async with await get_client() as client:
            try:
                from datetime import datetime
                data = BuildStateCreate(build_id=build_id, state=state, status=status, start_time=datetime.now())
                response = await client.add_build_state(build_id, data)
                console.print(f"[green]✅ Build state added successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_add_state())

@app.command("add-failure")
def add_failure(
    build_id: uuid.UUID = typer.Argument(..., help="ID of the build to add a failure to."),
    state: int = typer.Option(..., "--state", help="State code where failure occurred"),
    failure_type: str = typer.Option(..., "--type", help="Type of failure"),
    error_message: str = typer.Option(..., "--message", help="Error message"),
):
    """Add a failure to a build."""
    async def _add_failure():
        async with await get_client() as client:
            try:
                data = BuildFailureCreate(build_id=build_id, state=state, failure_type=failure_type, error_message=error_message)
                response = await client.add_build_failure(build_id, data)
                console.print(f"[green]✅ Build failure added successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_add_failure())
