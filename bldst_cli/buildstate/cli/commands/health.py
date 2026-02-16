"""
CLI commands for health checks.
"""
import typer
from rich.console import Console

from ...client import BuildStateAPIError
from ..utils import run_async, get_client, handle_api_error

app = typer.Typer(help="Health check commands")
console = Console()

@app.command("liveness")
def liveness_check():
    """Check if the API is running (liveness probe)."""
    async def _health():
        async with await get_client() as client:
            try:
                response = await client.health_check()
                console.print(f"[green]✅ API is live.[/green] Status: [bold]{response.get('status', 'UNKNOWN')}[/bold]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_health())

@app.command("readiness")
def readiness_check():
    """Check if the API is ready to serve traffic (readiness probe)."""
    async def _readiness():
        async with await get_client() as client:
            try:
                response = await client.readiness_check()
                db_status = response.get('database', 'UNKNOWN')
                cache_status = response.get('cache', 'UNKNOWN')
                
                if db_status == 'ok' and cache_status == 'ok':
                    console.print("[green]✅ API is ready.[/green]")
                else:
                    console.print("[yellow]⚠️ API is live but may not be fully ready.[/yellow]")

                console.print(f"  Database: {'[green]ok[/green]' if db_status == 'ok' else '[red]error[/red]'}")
                console.print(f"  Cache: {'[green]ok[/green]' if cache_status == 'ok' else '[red]error[/red]'}")

            except BuildStateAPIError as e:
                handle_api_error(e)

    run_async(_readiness())
