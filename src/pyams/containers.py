import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Any
import yaml
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from .config import settings, INSTALL_PATH, IS_WINDOWS

console: Console = Console()


def get_compose_env() -> dict[str, str]:
    """Get environment variables for podman-compose, handling Windows named pipes."""
    return os.environ.copy()


def get_install_path() -> Path:
    """Helper to get the standard installation path."""
    return INSTALL_PATH


def print_container_summary(services: list[str] | None = None) -> None:
    """Print a simple summary of the container statuses using a Rich table."""
    install_path: Path = get_install_path()
    compose_file: Path = install_path / "podman-compose.yml"

    if not compose_file.exists():
        return

    # 1. Get expected services from compose file
    try:
        with open(compose_file, "r") as f:
            compose_data: dict[str, Any] = yaml.safe_load(f)
        all_services: list[str] = list(compose_data.get("services", {}).keys())
    except Exception:
        all_services = []

    # Filter by requested services if provided
    expected_services: list[str] = [
        s for s in all_services if not services or s in services
    ]

    # 2. Get actual container status from podman
    try:
        result: subprocess.CompletedProcess = subprocess.run(
            [
                "podman",
                "ps",
                "-a",
                "--filter",
                "label=io.podman.compose.project=pyams",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        containers: list[dict[str, Any]] = json.loads(result.stdout)
    except Exception:
        containers = []

    # Map service names to their status
    service_status: dict[str, str] = {}
    container: dict[str, Any]
    for container in containers:
        labels: dict[str, Any] = container.get("Labels", {})
        service_name: str = (
            labels.get("com.docker.compose.service")
            or container.get("Names", ["unknown"])[0]
        )
        service_status[service_name] = container.get("State", "unknown")

    # 3. Create and display the table
    table: Table = Table(title="Container Status Summary", title_justify="left")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Result", justify="center")

    for service in expected_services:
        status: str = service_status.get(service, "not created")

        if status == "running":
            result_icon: str = "[green]✓ Started[/green]"
        elif status == "not created":
            result_icon = "[red]✗ Failed to create[/red]"
        else:
            result_icon = f"[yellow]! {status.capitalize()}[/yellow]"

        table.add_row(service, status, result_icon)

    console.print(table)


def show_status(services: list[str] | None = None) -> None:
    """Public command to show container status with a nicely formatted Rich table."""
    try:
        # Get actual container status from podman
        result: subprocess.CompletedProcess = subprocess.run(
            [
                "podman",
                "ps",
                "-a",
                "--filter",
                "label=io.podman.compose.project=pyams",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        containers: list[dict[str, Any]] = json.loads(result.stdout)

        if not containers:
            console.print("[yellow]No containers found for this project.[/yellow]")
            return

        table: Table = Table(
            title="PYAMS Service Status",
            title_justify="left",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Service", style="cyan")
        table.add_column("Status")
        table.add_column("Ports")

        container: dict[str, Any]
        for container in containers:
            labels: dict[str, Any] = container.get("Labels") or {}
            service_name: str = labels.get("com.docker.compose.service", "unknown")

            # Filter if services are specified
            if services and service_name not in services:
                continue

            status: str = container.get("Status", "unknown")
            state: str = container.get("State", "unknown")

            # Colorize status based on state
            if state == "running":
                display_status: str = f"[green]{status}[/green]"
            elif state == "exited":
                display_status = f"[red]{status}[/red]"
            else:
                display_status = f"[yellow]{status}[/yellow]"

            # Format ports - safely handle None
            ports_list: list[dict[str, Any]] = container.get("Ports") or []
            port_mappings: list[str] = []
            p: dict[str, Any]
            for p in ports_list:
                if p and p.get("host_port"):
                    port_mappings.append(
                        f"{p['host_port']}->{p['container_port']}/{p['protocol']}"
                    )
            ports_str: str = ", ".join(port_mappings)

            table.add_row(service_name, display_status, ports_str)

        console.print(table)

    except subprocess.CalledProcessError:
        console.print("[bold red]Failed to check services[/bold red]")
    except Exception as e:
        console.print(
            f"[bold red]An error occurred while formatting status:[/bold red] {str(e)}"
        )


def create_containers() -> None:
    """Check if containers exist and create them if they don't."""
    install_path: Path = get_install_path()
    compose_file: Path = install_path / "podman-compose.yml"

    if not compose_file.exists():
        console.print(
            f"[red]Compose file not found at {compose_file}. Please run install first.[/red]"
        )
        return

    try:
        # Check if containers are already running or created
        with console.status("[bold blue]Checking for existing containers..."):
            result: subprocess.CompletedProcess = subprocess.run(
                ["podman-compose", "ps", "--quiet"],
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
        if result.stdout.strip():
            console.print(
                "[yellow]Containers already exist. Skipping creation.[/yellow]"
            )
            return
    except subprocess.CalledProcessError:
        pass

    # If they don't exist, start them
    start_containers()


def start_containers(services: list[str] | None = None) -> None:
    """Start containers defined in the compose file."""
    install_path: Path = get_install_path()
    compose_file: Path = install_path / "podman-compose.yml"

    if not compose_file.exists():
        console.print(
            f"[red]Compose file not found at {compose_file}. Please run install first.[/red]"
        )
        return

    msg: str = (
        "Starting containers"
        if not services
        else f"Starting services: {', '.join(services)}"
    )
    console.print(f"[blue]{msg} using podman-compose...[/blue]")

    cmd: list[str] = ["podman-compose", "up", "-d"]
    if services:
        cmd.extend(services)

    try:
        with console.status(
            "[bold green]Processing containers... (this may take a minute)"
        ):
            subprocess.run(
                cmd,
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
        console.print("[green]Containers started successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to start containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")
    except FileNotFoundError:
        console.print("[red]podman-compose command not found.[/red]")


def stop_containers(services: list[str] | None = None) -> None:
    """Stop containers defined in the compose file."""
    install_path: Path = get_install_path()

    msg: str = (
        "Stopping containers"
        if not services
        else f"Stopping services: {', '.join(services)}"
    )
    console.print(f"[blue]{msg} using podman-compose...[/blue]")

    cmd: list[str] = ["podman-compose", "stop"]
    if services:
        cmd.extend(services)

    try:
        with console.status("[bold red]Stopping containers..."):
            subprocess.run(
                cmd,
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
        console.print("[green]Containers stopped successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to stop containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")


def restart_containers(services: list[str] | None = None) -> None:
    """Restart containers defined in the compose file."""
    install_path: Path = get_install_path()

    msg: str = (
        "Restarting containers"
        if not services
        else f"Restarting services: {', '.join(services)}"
    )
    console.print(f"[blue]{msg} using podman-compose...[/blue]")

    cmd: list[str] = ["podman-compose", "restart"]
    if services:
        cmd.extend(services)

    try:
        with console.status("[bold yellow]Restarting containers..."):
            subprocess.run(
                cmd,
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
        console.print("[green]Containers restarted successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to restart containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")


def remove_containers() -> None:
    """Stop and remove all containers and networks defined in the compose file."""
    install_path: Path = get_install_path()
    if not Confirm.ask(
        "[red]Are you sure you want to remove all containers? This will not delete your data, but it will remove the container instances.[/red]",
        default=False,
    ):
        return

    console.print("[blue]Removing containers using podman-compose...[/blue]")
    try:
        with console.status("[bold red]Removing containers and networks..."):
            subprocess.run(
                ["podman-compose", "down"],
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
        console.print("[green]Containers removed successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to remove containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")


def destroy_containers() -> None:
    """Stop and remove all containers, networks, AND VOLUMES, then clean up host files."""
    install_path: Path = get_install_path()
    if not Confirm.ask(
        "[bold red]WARNING: This will destroy all containers, networks, VOLUMES, and LOCAL CONFIGURATION (including the 'config' and 'media' folders). Your media and database data will be PERMANENTLY DELETED. Are you sure?[/bold red]",
        default=False,
    ):
        return

    if not Confirm.ask(
        "[bold red]Are you REALLY sure? This action is IRREVERSIBLE and all your media will be lost.[/bold red]",
        default=False,
    ):
        return

    # 1. Pull directory paths from current settings
    media_dir: Path | None = settings.get("MEDIA_DIRECTORY")
    config_dir: Path = settings.get("INSTALL_DIRECTORY", install_path)

    console.print(
        "[bold red]Destroying everything (containers + volumes) using podman-compose...[/bold red]"
    )
    try:
        with console.status(
            "[bold red]Destroying containers, networks, and volumes..."
        ):
            subprocess.run(
                ["podman-compose", "down", "--volumes"],
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )

        # 2. Clean up host directories
        with console.status("[bold red]Cleaning up host directories..."):
            # Remove media directory if it exists and is different from config_dir
            if media_dir and media_dir.exists():
                shutil.rmtree(media_dir, ignore_errors=True)
                console.print(f"[dim]Removed media directory: {media_dir}[/dim]")

            # Remove the entire installation/config directory (contains .env, podman-compose.yml, and config/ folder)
            if config_dir.exists():
                shutil.rmtree(config_dir, ignore_errors=True)
                console.print(
                    f"[dim]Removed configuration directory: {config_dir}[/dim]"
                )

            # Fallback for standard path if config_dir was custom
            if install_path.exists() and install_path != config_dir:
                shutil.rmtree(install_path, ignore_errors=True)
                console.print(
                    f"[dim]Removed standard configuration directory: {install_path}[/dim]"
                )

        console.print(
            "[green]Everything destroyed and cleaned up successfully![/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to destroy containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")
    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")


def recycle_containers(services: list[str] | None = None) -> None:
    """Stop, remove, and restart containers."""
    msg: str = (
        "Recycling all containers"
        if not services
        else f"Recycling services: {', '.join(services)}"
    )
    console.print(f"[bold blue]{msg}...[/bold blue]")

    # 1. Stop
    stop_containers(services)

    # 2. Remove (podman-compose down)
    install_path: Path = get_install_path()
    try:
        with console.status("[bold red]Removing containers..."):
            # Note: podman-compose down removes everything in the project
            subprocess.run(
                ["podman-compose", "down"],
                cwd=install_path,
                capture_output=True,
                text=True,
                check=True,
                env=get_compose_env(),
            )
    except Exception:
        pass

    # 3. Start (which will recreate)
    start_containers(services)


def show_logs(service: str, follow: bool = True) -> None:
    """Show logs for a specific service."""
    install_path: Path = get_install_path()

    cmd: list[str] = ["podman-compose", "logs"]
    if follow:
        cmd.append("-f")
    cmd.append(service)

    console.print(f"[blue]Showing logs for {service}... (Press Ctrl+C to exit)[/blue]")
    try:
        # We don't capture output here so the user sees the live stream
        subprocess.run(cmd, cwd=install_path, env=get_compose_env())
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to fetch logs for {service}[/red]")


def update_containers(services: list[str] | None = None) -> None:
    """Pull the latest images and restart containers."""
    install_path: Path = get_install_path()

    msg: str = (
        "Updating all services"
        if not services
        else f"Updating services: {', '.join(services)}"
    )
    console.print(f"[bold blue]{msg}...[/bold blue]")

    cmd_pull: list[str] = ["podman-compose", "pull"]
    if services:
        cmd_pull.extend(services)

    try:
        with console.status("[bold green]Pulling latest images..."):
            subprocess.run(
                cmd_pull,
                cwd=install_path,
                check=True,
                capture_output=True,
                env=get_compose_env(),
            )

        console.print(
            "[green]Images pulled successfully. Restarting containers...[/green]"
        )
        start_containers(services)

    except subprocess.CalledProcessError as e:
        console.print("[red]Failed to update containers:[/red]")
        console.print(f"[dim]{e.stderr if e.stderr else e.stdout}[/dim]")
