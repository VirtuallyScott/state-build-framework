"""
CLI commands for managing Build Artifacts.
"""
import typer
from rich.console import Console
from typing import Optional
from datetime import datetime

from ...client import BuildStateAPIError
from ...models import BuildArtifactCreate, BuildArtifactUpdate
from ..utils import run_async, get_client, handle_api_error, format_response

app = typer.Typer(help="Manage Build Artifacts")
console = Console()


@app.command("create")
def create(
    build_id: str = typer.Argument(..., help="ID of the build"),
    artifact_name: str = typer.Option(..., "--name", help="Name of the artifact"),
    artifact_type: str = typer.Option(..., "--type", help="Type of artifact (e.g., vm_snapshot, ami, disk_image)"),
    artifact_path: str = typer.Option(..., "--path", help="Full path or URL to the artifact"),
    state_code: int = typer.Option(..., "--state", help="State code at which this artifact was created"),
    storage_backend: str = typer.Option(..., "--backend", help="Storage backend (s3, azure_blob, gcp_storage, local, vsphere)"),
    storage_region: Optional[str] = typer.Option(None, "--region", help="Storage region"),
    storage_bucket: Optional[str] = typer.Option(None, "--bucket", help="Storage bucket name"),
    storage_key: Optional[str] = typer.Option(None, "--key", help="Storage key/path within bucket"),
    size_bytes: Optional[int] = typer.Option(None, "--size", help="Size of artifact in bytes"),
    checksum: Optional[str] = typer.Option(None, "--checksum", help="SHA256 checksum"),
    checksum_algorithm: str = typer.Option("sha256", "--checksum-algorithm", help="Checksum algorithm"),
    is_resumable: bool = typer.Option(True, "--resumable/--not-resumable", help="Can this artifact be used to resume?"),
    is_final: bool = typer.Option(False, "--final/--not-final", help="Is this the final deliverable?"),
):
    """Create a new artifact for a build."""
    async def _create():
        async with await get_client() as client:
            try:
                data = BuildArtifactCreate(
                    artifact_name=artifact_name,
                    artifact_type=artifact_type,
                    artifact_path=artifact_path,
                    state_code=state_code,
                    storage_backend=storage_backend,
                    storage_region=storage_region,
                    storage_bucket=storage_bucket,
                    storage_key=storage_key,
                    size_bytes=size_bytes,
                    checksum=checksum,
                    checksum_algorithm=checksum_algorithm,
                    is_resumable=is_resumable,
                    is_final=is_final,
                )
                response = await client.create_artifact(build_id, data)
                console.print(f"[green]✅ Artifact created successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_create())


@app.command("list")
def list_artifacts(
    build_id: str = typer.Argument(..., help="ID of the build"),
    state_code: Optional[int] = typer.Option(None, "--state", help="Filter by state code"),
    artifact_type: Optional[str] = typer.Option(None, "--type", help="Filter by artifact type"),
    resumable: Optional[bool] = typer.Option(None, "--resumable", help="Filter by resumable flag"),
    final: Optional[bool] = typer.Option(None, "--final", help="Filter by final flag"),
):
    """List artifacts for a build."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_artifacts(
                    build_id=build_id,
                    state_code=state_code,
                    artifact_type=artifact_type,
                    is_resumable=resumable,
                    is_final=final
                )
                if not response:
                    console.print("[yellow]No artifacts found.[/yellow]")
                else:
                    format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())


@app.command("get")
def get(
    build_id: str = typer.Argument(..., help="ID of the build"),
    artifact_id: str = typer.Argument(..., help="ID of the artifact"),
):
    """Get details of a specific artifact."""
    async def _get():
        async with await get_client() as client:
            try:
                response = await client.get_artifact(build_id, artifact_id)
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_get())


@app.command("update")
def update(
    build_id: str = typer.Argument(..., help="ID of the build"),
    artifact_id: str = typer.Argument(..., help="ID of the artifact"),
    artifact_name: Optional[str] = typer.Option(None, "--name", help="New name"),
    artifact_type: Optional[str] = typer.Option(None, "--type", help="New type"),
    artifact_path: Optional[str] = typer.Option(None, "--path", help="New path"),
    is_resumable: Optional[bool] = typer.Option(None, "--resumable", help="Update resumable flag"),
    is_final: Optional[bool] = typer.Option(None, "--final", help="Update final flag"),
):
    """Update an artifact."""
    async def _update():
        async with await get_client() as client:
            try:
                data = BuildArtifactUpdate(
                    artifact_name=artifact_name,
                    artifact_type=artifact_type,
                    artifact_path=artifact_path,
                    is_resumable=is_resumable,
                    is_final=is_final,
                )
                response = await client.update_artifact(build_id, artifact_id, data)
                console.print(f"[green]✅ Artifact updated successfully![/green]")
                format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_update())


@app.command("delete")
def delete(
    build_id: str = typer.Argument(..., help="ID of the build"),
    artifact_id: str = typer.Argument(..., help="ID of the artifact"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete an artifact (soft delete)."""
    async def _delete():
        if not confirm:
            confirm_delete = typer.confirm(
                f"Are you sure you want to delete artifact {artifact_id}?"
            )
            if not confirm_delete:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return
        
        async with await get_client() as client:
            try:
                await client.delete_artifact(build_id, artifact_id)
                console.print(f"[green]✅ Artifact deleted successfully![/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_delete())


@app.command("list-resumable")
def list_resumable(
    build_id: str = typer.Argument(..., help="ID of the build"),
):
    """List only resumable artifacts for a build."""
    async def _list():
        async with await get_client() as client:
            try:
                response = await client.list_artifacts(build_id=build_id, is_resumable=True)
                if not response:
                    console.print("[yellow]No resumable artifacts found.[/yellow]")
                else:
                    console.print(f"[cyan]Found {len(response)} resumable artifact(s):[/cyan]")
                    format_response(response)
            except BuildStateAPIError as e:
                handle_api_error(e)
    run_async(_list())
