import os
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .config import settings, INSTALL_PATH, IS_WINDOWS

console: Console = Console()


def run_doctor() -> None:
    """Run a health check on the PYAMS installation and system."""
    console.print(
        "[bold blue]PYAMS System Doctor - Diagnosing your setup...[/bold blue]\n"
    )

    table: Table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Check", width=30)
    table.add_column("Status", width=15)
    table.add_column("Details")

    # 1. Check Podman
    podman_path: str | None = shutil.which("podman")
    if podman_path:
        try:
            subprocess.run(["podman", "info"], capture_output=True, check=True)
            table.add_row(
                "Podman Engine", "[green]Healthy[/green]", f"Found at {podman_path}"
            )
        except Exception:
            table.add_row(
                "Podman Engine",
                "[red]Error[/red]",
                "Podman is installed but the service is not running",
            )
    else:
        table.add_row("Podman Engine", "[red]Missing[/red]", "Podman not found in PATH")

    # 2. Check Podman-Compose
    if shutil.which("podman-compose"):
        table.add_row(
            "Podman-Compose", "[green]Healthy[/green]", "Installed and available"
        )
    else:
        table.add_row(
            "Podman-Compose", "[red]Missing[/red]", "podman-compose not found"
        )

    # 3. Check Install Directory & Permissions
    install_path: Path = INSTALL_PATH
    if install_path.exists():
        is_writable: bool = os.access(install_path, os.W_OK)
        status: str = "[green]Healthy[/green]" if is_writable else "[red]Locked[/red]"
        table.add_row("Install Directory", status, str(install_path))
    else:
        table.add_row(
            "Install Directory", "[yellow]Missing[/yellow]", "Not installed yet"
        )

    # 4. Check IDs (Linux only)
    if not IS_WINDOWS:
        current_uid: int = os.getuid()
        puid: str = str(settings.get("PUID", ""))

        if puid and puid != str(current_uid):
            table.add_row(
                "User ID Match",
                "[yellow]Warning[/yellow]",
                f"Current UID {current_uid} != Configured PUID {puid}",
            )
        else:
            table.add_row(
                "User ID Match",
                "[green]Healthy[/green]",
                f"Running as UID {current_uid}",
            )

    # 5. Disk Space
    try:
        total: int
        used: int
        free: int
        total, used, free = shutil.disk_usage(
            install_path if install_path.exists() else Path.home()
        )
        free_gb: int = free // (2**30)
        disk_status: str = (
            "[green]Healthy[/green]" if free_gb > 5 else "[yellow]Low[/yellow]"
        )
        table.add_row("Disk Space", disk_status, f"{free_gb}GB free")
    except Exception:
        pass

    console.print(table)
    console.print(
        "\n[dim]If you see any [red]Error[/red] or [yellow]Warning[/yellow], please resolve them before running PYAMS.[/dim]\n"
    )
