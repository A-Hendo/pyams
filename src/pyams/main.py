import typer
import yaml
from typing import Any
from . import __version__
from .config import INSTALL_PATH
from .install import Installer
from .containers import (
    create_containers,
    start_containers,
    stop_containers,
    restart_containers,
    remove_containers,
    destroy_containers,
    recycle_containers,
    show_status,
    show_logs,
    update_containers,
)
from .vpn import check_vpn as vpn_check
from .utils import backup_data, restore_data
from .doctor import run_doctor

app: typer.Typer = typer.Typer(
    help="PYAMS - Python Yet Another Media Server CLI",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"PYAMS version: {__version__}")
        raise typer.Exit()


def get_service_names(ctx: typer.Context, incomplete: str) -> list[str]:
    """Autocompletion for service names from the compose file."""
    compose_file: Any = INSTALL_PATH / "podman-compose.yml"
    if not compose_file.exists():
        return []
    try:
        with open(compose_file, "r") as f:
            data: dict[str, Any] = yaml.safe_load(f)
        services: list[str] = list(data.get("services", {}).keys())
        return [s for s in services if s.startswith(incomplete)]
    except Exception:
        return []


@app.callback()
def common(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit.",
    ),
) -> None:
    pass


@app.command(help="Install and configure PYAMS on your system.")
def install() -> None:
    installer: Installer = Installer()
    installer.run()
    # After install, we should probably create/start them
    create_containers()


@app.command(help="Start the media server containers.")
def start(
    services: list[str] = typer.Argument(
        None, help="Specific services to start", autocompletion=get_service_names
    ),
) -> None:
    start_containers(services)


@app.command(help="Stop the media server containers.")
def stop(
    services: list[str] = typer.Argument(
        None, help="Specific services to stop", autocompletion=get_service_names
    ),
) -> None:
    stop_containers(services)


@app.command(help="Restart the media server containers.")
def restart(
    services: list[str] = typer.Argument(
        None, help="Specific services to restart", autocompletion=get_service_names
    ),
) -> None:
    restart_containers(services)


@app.command(help="Remove all containers and networks (data is preserved).")
def remove() -> None:
    remove_containers()


@app.command(help="Destroy all containers, networks, AND VOLUMES (DATA LOSS!).")
def destroy() -> None:
    destroy_containers()


@app.command(help="Show the current status of all services.")
def status(
    services: list[str] = typer.Argument(
        None, help="Specific services to check", autocompletion=get_service_names
    ),
) -> None:
    show_status(services)


@app.command(help="Stop, destroy, and recreate containers.")
def recycle(
    services: list[str] = typer.Argument(
        None, help="Specific services to recycle", autocompletion=get_service_names
    ),
) -> None:
    recycle_containers(services)


@app.command(name="check-vpn", help="Verify if the VPN is correctly masking your IP.")
def check_vpn() -> None:
    vpn_check()


@app.command(help="Create a compressed backup of your configuration and data.")
def backup(
    destination: str | None = typer.Argument(None, help="Directory to save the backup"),
    media: bool = typer.Option(
        False, "--media", help="Include media directory in backup"
    ),
) -> None:
    backup_data(destination, media)


@app.command(help="Restore your configuration and data from a backup archive.")
def restore(
    backup_file: str = typer.Argument(..., help="Path to the backup file to restore"),
) -> None:
    restore_data(backup_file)


@app.command(help="Pull the latest images and restart containers.")
def update(
    services: list[str] = typer.Argument(
        None, help="Specific services to update", autocompletion=get_service_names
    ),
) -> None:
    update_containers(services)


@app.command(help="Show logs for a specific service.")
def logs(
    service: str = typer.Argument(
        ...,
        help="The name of the service to show logs for",
        autocompletion=get_service_names,
    ),
) -> None:
    show_logs(service)


@app.command(help="Run a system health check to diagnose setup issues.")
def doctor() -> None:
    run_doctor()


if __name__ == "__main__":
    app()
