"""
Main CLI entry point for BuildState CLI.

Uses Typer for command-line interface with auto-completion and rich formatting.
"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..config import config
from ..client import BuildStateClient, BuildStateAPIError, create_client_from_config
from ..models import BuildCreate, StateTransition, FailureRecord

# Initialize Typer app
app = typer.Typer(
    name="buildctl",
    help="BuildState CLI - Clean interface to Build State API",
    add_completion=True,
    rich_markup_mode="rich",
)

# Initialize Rich console
console = Console()


def handle_api_error(error: BuildStateAPIError):
    """Handle API errors with rich formatting."""
    if error.status_code == 401:
        console.print("[red]❌ Authentication failed. Please check your API key or login again.[/red]")
        console.print("[dim]Run 'buildctl auth login' or 'buildctl auth set-key <key>'[/dim]")
    elif error.status_code == 403:
        console.print("[red]❌ Access forbidden. Please check your permissions.[/red]")
    elif error.status_code == 404:
        console.print("[red]❌ Resource not found.[/red]")
    else:
        console.print(f"[red]❌ API Error: {error.message}[/red]")

    if error.errors:
        console.print("[dim]Details:[/dim]")
        for field, messages in error.errors.items():
            console.print(f"  [yellow]{field}:[/yellow] {', '.join(messages)}")

    raise typer.Exit(1)


async def get_client() -> BuildStateClient:
    """Get authenticated client."""
    try:
        return await create_client_from_config()
    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        console.print("[dim]Run 'bldst_cli config set-url <url>' to configure the API URL[/dim]")
        raise typer.Exit(1)


def format_build_table(builds: list, title: str = "Builds"):
    """Format builds as a rich table."""
    if not builds:
        console.print("[dim]No builds found.[/dim]")
        return

    table = Table(title=title)
    table.add_column("Build ID", style="cyan")
    table.add_column("Platform", style="green")
    table.add_column("OS Version", style="yellow")
    table.add_column("Type", style="magenta")
    table.add_column("State", style="blue")
    table.add_column("Created", style="dim")

    for build in builds:
        state = build.get('state_code', 'N/A')
        if state == 100:
            state_style = "[green]✓ Complete[/green]"
        elif build.get('error_message'):
            state_style = "[red]✗ Failed[/red]"
        else:
            state_style = f"[blue]{state}[/blue]"

        table.add_row(
            build['build_id'],
            build.get('platform_id', 'N/A'),
            build.get('os_version_id', 'N/A'),
            build.get('image_type_id', 'N/A'),
            state_style,
            build.get('created_at', 'N/A')[:19]  # Truncate timestamp
        )

    console.print(table)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Path to config file"),
):
    """
    BuildState CLI - Clean interface to Build State API

    Examples:
        buildctl config set-url http://localhost:8080
        buildctl auth set-key your-api-key
        buildctl build create --platform aws --os rhel-8.8 --type base --id my-build
        buildctl state update <build-uuid> --state 25 --message "Packer complete"
    """
    ctx.obj = {"verbose": verbose, "config_file": config_file}


# Configuration commands
config_app = typer.Typer(help="Manage CLI configuration")
app.add_typer(config_app, name="config")


@config_app.command("set-url")
def config_set_url(url: str):
    """Set the API base URL."""
    config.api_url = url
    console.print(f"[green]✅ API URL set to: {url}[/green]")


@config_app.command("get-url")
def config_get_url():
    """Get the current API URL."""
    url = config.api_url
    if url:
        console.print(f"API URL: {url}")
    else:
        console.print("[red]❌ API URL not configured[/red]")
        console.print("[dim]Run 'buildctl config set-url <url>' to configure[/dim]")


@config_app.command("show")
def config_show():
    """Show all configuration values."""
    cfg = config.get_all()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in cfg.items():
        if 'has_' in key:
            value = "✓" if value else "✗"
        table.add_row(key.replace('_', ' ').title(), str(value))

    console.print(table)


@config_app.command("reset")
def config_reset():
    """Reset all configuration."""
    config.reset()
    console.print("[green]✅ Configuration reset[/green]")


# Authentication commands
auth_app = typer.Typer(help="Manage authentication")
app.add_typer(auth_app, name="auth")


@auth_app.command("set-key")
def auth_set_key(api_key: str):
    """Set API key for authentication."""
    config.set_api_key(api_key)
    console.print("[green]✅ API key set securely[/green]")


@auth_app.command("clear-key")
def auth_clear_key():
    """Clear stored API key."""
    config.clear_api_key()
    console.print("[green]✅ API key cleared[/green]")


@auth_app.command("login")
def auth_login(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Login with username/password to get JWT token."""
    async def _login():
        async with BuildStateClient(config.api_url) as client:
            try:
                token_response = await client.login(username, password)
                config.jwt_token = token_response.access_token
                console.print("[green]✅ Login successful, JWT token stored[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_login())


@auth_app.command("idm-login")
def auth_idm_login(
    username: str = typer.Option(..., prompt=True),
    idm_token: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Login with IDM token."""
    async def _idm_login():
        async with BuildStateClient(config.api_url) as client:
            try:
                token_response = await client.idm_login(username, idm_token)
                config.jwt_token = token_response.access_token
                console.print("[green]✅ IDM login successful, JWT token stored[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_idm_login())


@auth_app.command("logout")
def auth_logout():
    """Clear stored JWT token."""
    config.clear_jwt_token()
    console.print("[green]✅ JWT token cleared[/green]")


# User management commands
user_app = typer.Typer(help="Manage users")
app.add_typer(user_app, name="user")


@user_app.command("create")
def user_create(
    username: str = typer.Option(..., "--username", "-u", help="Username"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    first_name: Optional[str] = typer.Option(None, "--first-name", help="First name"),
    last_name: Optional[str] = typer.Option(None, "--last-name", help="Last name"),
    employee_id: Optional[str] = typer.Option(None, "--employee-id", help="Employee ID"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="Password"),
    superuser: bool = typer.Option(False, "--superuser", help="Make user a superuser"),
):
    """Create a new user (admin only)."""
    async def _create():
        async with await get_client() as client:
            try:
                user_id = await client.create_user(username, email, password, first_name, last_name, employee_id, superuser)
                console.print(f"[green]✅ User created successfully![/green]")
                console.print(f"User ID: [cyan]{user_id}[/cyan]")
                console.print(f"Username: [cyan]{username}[/cyan]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_create())


@user_app.command("get")
def user_get(user_id: str):
    """Get user details."""
    async def _get():
        async with await get_client() as client:
            try:
                user = await client.get_user(user_id)
                console.print(f"[bold]User Details:[/bold]")
                console.print(f"ID: {user.id}")
                console.print(f"Username: {user.username}")
                console.print(f"Email: {user.email}")
                if user.first_name or user.last_name:
                    console.print(f"Name: {user.first_name or ''} {user.last_name or ''}".strip())
                if user.employee_id:
                    console.print(f"Employee ID: {user.employee_id}")
                console.print(f"Active: {'Yes' if user.is_active else 'No'}")
                console.print(f"Superuser: {'Yes' if user.is_superuser else 'No'}")
                console.print(f"Created: {user.created_at}")
                console.print(f"Updated: {user.updated_at}")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_get())


@user_app.command("update")
def user_update(
    user_id: str,
    email: Optional[str] = typer.Option(None, "--email", "-e", help="New email address"),
    first_name: Optional[str] = typer.Option(None, "--first-name", help="New first name"),
    last_name: Optional[str] = typer.Option(None, "--last-name", help="New last name"),
    employee_id: Optional[str] = typer.Option(None, "--employee-id", help="New employee ID"),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set active status"),
    superuser: Optional[bool] = typer.Option(None, "--superuser/--regular", help="Set superuser status"),
):
    """Update user details (admin only)."""
    async def _update():
        async with await get_client() as client:
            try:
                await client.update_user(user_id, email, first_name, last_name, employee_id, active, superuser)
                console.print(f"[green]✅ User updated successfully![/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_update())


@user_app.command("profile")
def user_profile(user_id: str):
    """Get user profile."""
    async def _profile():
        async with await get_client() as client:
            try:
                profile = await client.get_user_profile(user_id)
                console.print(f"[bold]User Profile:[/bold]")
                console.print(f"User ID: {profile.user_id}")
                console.print(f"Name: {profile.first_name} {profile.last_name}")
                console.print(f"Employee ID: {profile.employee_id}")
                console.print(f"Email: {profile.email}")
                console.print(f"Start Date: {profile.start_date}")
                if profile.end_date:
                    console.print(f"End Date: {profile.end_date}")
                console.print(f"Created: {profile.created_at}")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_profile())


# API Token commands
token_app = typer.Typer(help="Manage API tokens")
app.add_typer(token_app, name="token")


@token_app.command("create")
def token_create(
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
    name: str = typer.Option(..., "--name", "-n", help="Token name"),
    scopes: list[str] = typer.Option([], "--scope", "-s", help="Permission scopes (can specify multiple)"),
    expires_days: Optional[int] = typer.Option(None, "--expires", help="Days until expiration"),
):
    """Create API token for user."""
    async def _create():
        expires_at = None
        if expires_days:
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        async with await get_client() as client:
            try:
                token_response = await client.create_api_token(user_id, name, scopes, expires_at)
                console.print(f"[green]✅ API token created successfully![/green]")
                console.print(f"Token: [red]{token_response.token}[/red]")
                console.print(f"Name: {token_response.name}")
                console.print("[yellow]⚠️  Save this token securely - it will not be shown again![/yellow]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_create())


@token_app.command("list")
def token_list(user_id: str = typer.Option(..., "--user", "-u", help="User ID")):
    """List API tokens for user."""
    async def _list():
        async with await get_client() as client:
            try:
                tokens = await client.get_api_tokens(user_id)
                if not tokens:
                    console.print("[dim]No tokens found.[/dim]")
                    return

                table = Table(title=f"API Tokens for User {user_id}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Scopes", style="yellow")
                table.add_column("Active", style="blue")
                table.add_column("Expires", style="magenta")
                table.add_column("Created", style="dim")

                for token in tokens:
                    scopes_str = ", ".join(token.scopes) if token.scopes else "None"
                    active_str = "✓" if token.is_active else "✗"
                    expires_str = token.expires_at[:19] if token.expires_at else "Never"

                    table.add_row(
                        token.id,
                        token.name,
                        scopes_str,
                        active_str,
                        expires_str,
                        token.created_at[:19]
                    )

                console.print(table)
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_list())


@token_app.command("revoke")
def token_revoke(
    token_id: str = typer.Option(..., "--token", "-t", help="Token ID"),
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
):
    """Revoke API token."""
    async def _revoke():
        async with await get_client() as client:
            try:
                await client.revoke_api_token(token_id, user_id)
                console.print(f"[green]✅ API token revoked successfully![/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_revoke())


@auth_app.command("logout")
def auth_logout():
    """Clear stored JWT token."""
    config.clear_jwt_token()
    console.print("[green]✅ JWT token cleared[/green]")


# User management commands
user_app = typer.Typer(help="Manage users")
app.add_typer(user_app, name="user")


# Build management commands
build_app = typer.Typer(help="Manage builds")
app.add_typer(build_app, name="build")


@build_app.command("create")
def build_create(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform (aws-commercial, azure, gcp, etc.)"),
    os_version: str = typer.Option(..., "--os", "-o", help="OS version (rhel-8.8, ubuntu-22.04, etc.)"),
    image_type: str = typer.Option(..., "--type", "-t", help="Image type (base, hana, sapapp, openvpn)"),
    build_id: str = typer.Option(..., "--id", "-i", help="Unique build identifier"),
    pipeline_url: Optional[str] = typer.Option(None, "--pipeline-url", help="CI/CD pipeline URL"),
    commit_hash: Optional[str] = typer.Option(None, "--commit", help="Git commit hash"),
):
    """Create a new build."""
    async def _create():
        build = BuildCreate(
            platform=platform,
            os_version=os_version,
            image_type=image_type,
            build_id=build_id,
            pipeline_url=pipeline_url,
            commit_hash=commit_hash,
        )

        async with await get_client() as client:
            try:
                build_uuid = await client.create_build(build)
                console.print(f"[green]✅ Build created successfully![/green]")
                console.print(f"Build UUID: [cyan]{build_uuid}[/cyan]")
                console.print(f"Build ID: [cyan]{build_id}[/cyan]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_create())


@build_app.command("get")
def build_get(build_id: str):
    """Get build details."""
    async def _get():
        async with await get_client() as client:
            try:
                build = await client.get_build(build_id)
                console.print(f"[bold]Build Details:[/bold]")
                console.print(f"UUID: {build.id}")
                console.print(f"Build ID: {build.build_id}")
                console.print(f"Platform: {build.platform}")
                console.print(f"OS Version: {build.os_version}")
                console.print(f"Image Type: {build.image_type}")
                console.print(f"Current State: {build.current_state}")
                console.print(f"Created: {build.created_at}")
                console.print(f"Updated: {build.updated_at}")
                if build.pipeline_url:
                    console.print(f"Pipeline URL: {build.pipeline_url}")
                if build.commit_hash:
                    console.print(f"Commit Hash: {build.commit_hash}")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_get())


@build_app.command("list")
def build_list(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of builds to show"),
):
    """List builds."""
    async def _list():
        async with await get_client() as client:
            try:
                if platform:
                    builds = await client.list_builds_by_platform(platform, limit)
                    format_build_table(builds, f"Builds for {platform}")
                else:
                    # Get recent builds from dashboard
                    builds = await client.get_recent_builds(limit)
                    format_build_table(builds, "Recent Builds")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_list())


# State commands
state_app = typer.Typer(help="Manage build states")
app.add_typer(state_app, name="state")


@state_app.command("update")
def state_update(
    build_id: str,
    state: int = typer.Option(..., "--state", "-s", help="State code (0-100, multiple of 5)"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Optional message"),
):
    """Update build state."""
    async def _update():
        transition = StateTransition(state_code=state, message=message)

        async with await get_client() as client:
            try:
                await client.transition_state(build_id, transition)
                console.print(f"[green]✅ State updated to {state}[/green]")
                if message:
                    console.print(f"Message: {message}")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_update())


@state_app.command("get")
def state_get(build_id: str):
    """Get current build state."""
    async def _get():
        async with await get_client() as client:
            try:
                state = await client.get_current_state(build_id)
                console.print(f"[bold]Current State:[/bold]")
                console.print(f"Build ID: {state.build_id}")
                console.print(f"State Code: {state.current_state}")
                if state.message:
                    console.print(f"Message: {state.message}")
                console.print(f"Transitioned At: {state.transitioned_at}")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_get())


# Failure commands
failure_app = typer.Typer(help="Manage build failures")
app.add_typer(failure_app, name="failure")


@failure_app.command("record")
def failure_record(
    build_id: str,
    error_message: str = typer.Option(..., "--error", "-e", help="Error message"),
    error_code: Optional[str] = typer.Option(None, "--code", "-c", help="Error code"),
    component: Optional[str] = typer.Option(None, "--component", help="Component that failed"),
):
    """Record a build failure."""
    async def _record():
        failure = FailureRecord(
            error_message=error_message,
            error_code=error_code,
            component=component,
        )

        async with await get_client() as client:
            try:
                await client.record_failure(build_id, failure)
                console.print("[green]✅ Failure recorded[/green]")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_record())


# Dashboard commands
dashboard_app = typer.Typer(help="View dashboard and summaries")
app.add_typer(dashboard_app, name="dashboard")


@dashboard_app.command("summary")
def dashboard_summary():
    """Show dashboard summary."""
    async def _summary():
        async with await get_client() as client:
            try:
                summary = await client.get_dashboard_summary()

                # Create a nice summary display
                console.print("[bold]📊 Build State Dashboard[/bold]")
                console.print(f"Total Builds: [cyan]{summary.total_builds}[/cyan]")

                status_table = Table(title="Status Breakdown")
                status_table.add_column("Status", style="cyan")
                status_table.add_column("Count", style="green")

                for status, count in summary.status_counts.items():
                    status_table.add_row(status.replace('_', ' ').title(), str(count))

                console.print(status_table)

                if summary.recent_builds:
                    console.print("\n[bold]Recent Builds:[/bold]")
                    format_build_table(summary.recent_builds[:5], "")

            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_summary())


@dashboard_app.command("recent")
def dashboard_recent(limit: int = typer.Option(10, "--limit", "-l", help="Number of recent builds to show")):
    """Show recent builds."""
    async def _recent():
        async with await get_client() as client:
            try:
                builds = await client.get_recent_builds(limit)
                format_build_table(builds, f"Recent {len(builds)} Builds")
            except BuildStateAPIError as e:
                handle_api_error(e)

    asyncio.run(_recent())


@app.command("health")
def health_check():
    """Check API health."""
    async def _health():
        async with await get_client() as client:
            try:
                is_healthy = await client.health_check()
                if is_healthy:
                    console.print("[green]✅ API is healthy[/green]")
                else:
                    console.print("[red]❌ API is not healthy[/red]")
                    raise typer.Exit(1)
            except BuildStateAPIError as e:
                console.print(f"[red]❌ Health check failed: {e}[/red]")
                raise typer.Exit(1)

    asyncio.run(_health())


if __name__ == "__main__":
    app()