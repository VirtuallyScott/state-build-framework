"""
CLI utility functions.
"""
import asyncio
import json
from typing import List, Union

import typer
from rich.console import Console
from rich.table import Table
from pydantic import BaseModel

from ..client import BuildStateClient, BuildStateAPIError, create_client_from_config

console = Console()

def run_async(coro):
    """Run an async coroutine, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply(loop)

    return loop.run_until_complete(coro)


def handle_api_error(error: BuildStateAPIError):
    """Handle API errors with rich formatting."""
    if error.status_code == 401:
        console.print("[red]❌ Authentication failed. Please check your API key or login again.[/red]")
        console.print("[dim]Run 'bldst auth login' or 'bldst auth set-key <key>'[/dim]")
    elif error.status_code == 403:
        console.print("[red]❌ Access forbidden. Please check your permissions.[/red]")
    elif error.status_code == 404:
        console.print("[red]❌ Resource not found.[/red]")
    else:
        console.print(f"[red]❌ API Error (HTTP {error.status_code}): {error.message}[/red]")

    if error.errors and 'detail' in error.errors:
        details = error.errors['detail']
        if isinstance(details, list):
            console.print("[dim]Details:[/dim]")
            for err in details:
                loc = " -> ".join(map(str, err.get('loc', [])))
                msg = err.get('msg')
                console.print(f"  [yellow]{loc}:[/yellow] {msg}")
        elif isinstance(details, str):
             console.print(f"  [yellow]Detail:[/yellow] {details}")


    raise typer.Exit(1)


async def get_client() -> BuildStateClient:
    """Get authenticated client."""
    try:
        return await create_client_from_config()
    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        console.print("[dim]Run 'bldst config set-url <url>' to configure the API URL[/dim]")
        raise typer.Exit(1)

def format_response(response: Union[BaseModel, List[BaseModel]], output_format: str = "table"):
    """Format a Pydantic model or list of models for CLI output."""
    if isinstance(response, list):
        if not response:
            console.print("[dim]No items found.[/dim]")
            return
        # For lists, always use a table for now
        items = [item.dict() for item in response]
        headers = items[0].keys()
        table = Table(title=f"{response[0].__class__.__name__}s")
        for header in headers:
            table.add_column(header.replace('_', ' ').title(), style="cyan" if header == 'id' else "green")
        
        for item in items:
            table.add_row(*[str(v) for v in item.values()])
        console.print(table)

    elif isinstance(response, BaseModel):
        item = response.dict()
        table = Table(title=response.__class__.__name__)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        for key, value in item.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            elif isinstance(value, list):
                 value = json.dumps(value, indent=2)
            table.add_row(key.replace('_', ' ').title(), str(value))
        console.print(table)
    else:
        console.print(response)
