import os
import shutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from .containers import get_install_path, stop_containers, start_containers

console: Console = Console()


def backup_data(destination: str | None = None, include_media: bool = False) -> None:
    """Backup configuration and optionally media data."""
    install_path: Path = get_install_path()

    if not install_path.exists():
        console.print(
            f"[red]Installation path {install_path} not found. Nothing to backup.[/red]"
        )
        return

    # 1. Stop containers first to ensure data consistency
    console.print("[yellow]Stopping containers for a safe backup...[/yellow]")
    stop_containers()

    try:
        # 2. Prepare backup path
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_base_dir: Path
        if destination:
            backup_base_dir = Path(destination)
        else:
            backup_base_dir = install_path / "backups"

        backup_base_dir.mkdir(parents=True, exist_ok=True)

        backup_filename: str = (
            f"pyams_backup_{'full_' if include_media else ''}{timestamp}"
        )
        backup_file_path: Path = backup_base_dir / backup_filename

        # 3. Perform backup
        # Define what to exclude (YAMS-like exclusions)
        ignore_patterns: list[str] = [
            "backups",
            "tmp_backup",
            "transcoding-temp",
            "config/jellyfin/cache",
            "jellyfin/cache",
        ]

        if not include_media:
            ignore_patterns.append("media")

        with console.status(f"[blue]Creating backup {backup_filename}.tar.gz..."):
            temp_backup_dir: Path = install_path / "tmp_backup"
            if temp_backup_dir.exists():
                shutil.rmtree(temp_backup_dir)
            temp_backup_dir.mkdir()

            def should_ignore(path: str, names: list[str]) -> list[str]:
                ignored: list[str] = []
                rel_path: str = os.path.relpath(path, install_path)
                for name in names:
                    full_rel_path: str = (
                        os.path.join(rel_path, name) if rel_path != "." else name
                    )
                    if any(p in full_rel_path for p in ignore_patterns):
                        ignored.append(name)
                return ignored

            item: Path
            for item in install_path.iterdir():
                if any(p == item.name for p in ignore_patterns):
                    continue

                target: Path = temp_backup_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, target, ignore=should_ignore)
                else:
                    shutil.copy2(item, target)

            shutil.make_archive(
                str(backup_file_path), "gztar", root_dir=str(temp_backup_dir)
            )
            shutil.rmtree(temp_backup_dir)

        console.print(
            f"[green]Backup created successfully: [bold]{backup_file_path}.tar.gz[/bold][/green]"
        )

    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")

    finally:
        console.print("[yellow]Restarting containers...[/yellow]")
        start_containers()


def restore_data(backup_file: str) -> None:
    """Restore configuration and data from a backup archive."""
    install_path: Path = get_install_path()
    backup_path: Path = Path(backup_file)

    if not backup_path.exists():
        console.print(f"[red]Backup file {backup_file} not found.[/red]")
        return

    if not Confirm.ask(
        f"[red]This will OVERWRITE your current configuration and data in {install_path}. Are you sure?[/red]",
        default=False,
    ):
        return

    # 1. Stop containers first
    console.print("[yellow]Stopping containers for a safe restore...[/yellow]")
    stop_containers()

    try:
        with console.status(f"[blue]Restoring from {backup_path.name}..."):
            # Ensure install path exists
            install_path.mkdir(parents=True, exist_ok=True)

            # Unpack the archive directly into the install path
            shutil.unpack_archive(str(backup_path), extract_dir=str(install_path))

        console.print(
            f"[green]Restore completed successfully from [bold]{backup_path.name}[/bold][/green]"
        )

    except Exception as e:
        console.print(f"[red]Restore failed: {e}[/red]")

    finally:
        # 2. Restart containers
        console.print("[yellow]Restarting containers...[/yellow]")
        start_containers()
