import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .config import INSTALL_PATH, IS_LINUX, IS_WINDOWS, OS, settings

console: Console = Console()


class Installer:
    def __init__(self) -> None:
        self.os: str = OS
        self.is_linux: bool = IS_LINUX
        self.is_windows: bool = IS_WINDOWS
        self.install_path: Path = INSTALL_PATH

        if not self.is_linux and not self.is_windows:
            console.print(
                f"[yellow]Warning: Unsupported OS '{self.os}' detected. Defaulting to Windows settings.[/yellow]"
            )

        # Use the global settings but keep a local reference we can modify during run()
        # before saving back to .env
        self.config: dict[str, Any] = settings.copy()

    def install_podman(self) -> bool:
        """Attempt to install Podman based on the OS."""
        if self.is_linux:
            try:
                with console.status(
                    "[yellow]Attempting to install Podman and Podman-Compose...[/yellow]"
                ):
                    subprocess.run(
                        "sudo apt-get update && sudo apt-get install -y podman",
                        shell=True,
                        check=True,
                        capture_output=True,
                    )
                console.print("[green]Podman installed successfully![/green]")
                return True
            except Exception:
                console.print(
                    "[red]Failed to install Podman automatically. Please install it manually.[/red]"
                )
                return False
        elif self.is_windows:
            try:
                with console.status(
                    "[yellow]Attempting to install Podman via winget...[/yellow]"
                ):
                    subprocess.run(
                        [
                            "winget",
                            "install",
                            "-e",
                            "--id",
                            "RedHat.Podman",
                            "--accept-source-agreements",
                            "--accept-package-agreements",
                            "--silent",
                        ],
                        check=True,
                        capture_output=True,
                    )
                console.print(
                    "[green]Podman installation started! Please follow the installer prompts.[/green]"
                )
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                console.print(
                    "[red]winget not found or installation failed. Please install Podman manually: https://podman-desktop.io/[/red]"
                )
                return False
        else:
            console.print(f"[red]Auto-installation not supported for {self.os}.[/red]")
        return False

    def check_windows_virtualization(self) -> bool:
        """Check if WSL or Hyper-V is enabled on Windows."""
        if not self.is_windows:
            return True

        with console.status("[bold blue]Checking Windows Virtualization features..."):
            # Check for WSL
            wsl_installed = shutil.which("wsl.exe") is not None

            # Check for Hyper-V (Virtual Machine Management Service)
            hyperv_enabled = False
            try:
                # Attempt to check for the Hyper-V service
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-Service -Name vmms -ErrorAction SilentlyContinue",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and "Running" in result.stdout:
                    hyperv_enabled = True
            except Exception:
                pass

        if not wsl_installed and not hyperv_enabled:
            console.print(
                "[yellow]Warning: Neither WSL nor Hyper-V appears to be fully enabled.[/yellow]"
            )
            console.print(
                "[yellow]Podman requires one of these to function on Windows.[/yellow]"
            )
            if Confirm.ask(
                "WSL is a required dependency. Would you like to attempt to install it?",
                default=True,
            ):
                try:
                    with console.status(
                        "[yellow]Attempting to install WSL...[/yellow]"
                    ):
                        subprocess.run(["wsl", "--install"], check=True)
                    console.print(
                        "[green]WSL installation initiated! You will likely need to restart your computer to complete the setup.[/green]"
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    console.print(
                        "[red]Failed to install WSL automatically. Please run 'wsl --install' in an Administrator PowerShell window.[/red]"
                    )
                    return False

            return False

        if wsl_installed:
            console.print("[green]WSL detected![/green]")
        elif hyperv_enabled:
            console.print("[green]Hyper-V detected![/green]")

        return True

    def ensure_podman_machine(self) -> bool:
        """Initialize and start Podman machine on Windows."""
        if not self.is_windows:
            return True

        try:
            # Check if any machine exists
            result = subprocess.run(
                ["podman", "machine", "list", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0 or not result.stdout.strip():
                with console.status("[bold blue]Initializing Podman machine..."):
                    console.print(
                        "[yellow]No Podman machine found. Initializing...[/yellow]"
                    )
                    subprocess.run(["podman", "machine", "init"], check=True)

            # Check if machine is running
            result = subprocess.run(
                ["podman", "machine", "list", "--format", "{{.Running}}"],
                capture_output=True,
                text=True,
                check=False,
            )

            # If "true" is not in the output, start it
            if "true" not in result.stdout.lower():
                with console.status("[bold blue]Starting Podman machine..."):
                    console.print(
                        "[yellow]Podman machine is not running. Starting...[/yellow]"
                    )
                    subprocess.run(["podman", "machine", "start"], check=True)

            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error managing Podman machine: {e}[/red]")
            return False
        except FileNotFoundError:
            return False

    def check_dependencies(self) -> bool:
        """Check if Podman and Podman-Compose are installed."""
        with console.status("[bold blue]Checking dependencies..."):
            podman_installed: bool = shutil.which("podman") is not None
            podman_compose_installed: bool = shutil.which("podman-compose") is not None

        if not podman_installed:
            console.print("[yellow]Podman is not installed.[/yellow]")
            if Confirm.ask(
                "Would you like to attempt to install Podman automatically?",
                default=True,
            ):
                if self.install_podman():
                    podman_installed = shutil.which("podman") is not None
                    if not podman_installed:
                        console.print(
                            "[yellow]Podman was installed but is not yet in your PATH. You may need to restart your terminal to continue.[/yellow]"
                        )
                        return False
                else:
                    return False
            else:
                return False
        else:
            console.print("[green]Podman detected![/green]")

        if podman_compose_installed:
            console.print("[green]Podman-Compose detected![/green]")

        if self.is_windows:
            if not self.ensure_podman_machine():
                return False

        if not podman_compose_installed:
            console.print("[yellow]Podman-Compose is not installed.[/yellow]")
            if Confirm.ask(
                "Would you like to attempt to install podman-compose via using uv?",
                default=True,
            ):
                try:
                    subprocess.run(
                        ["uv", "tool", "install", "podman-compose"], check=True
                    )
                    podman_compose_installed: bool = (
                        shutil.which("podman-compose") is not None
                    )
                except Exception:
                    console.print("[red]Failed to install podman-compose via uv.[/red]")

            if not podman_compose_installed:
                console.print(
                    "[red]Podman-Compose is required. Please install it manually.[/red]"
                )
                return False

        console.print("[green]Podman and Podman-Compose are available![/green]")
        return True

    def get_user_info(self) -> tuple[int, int]:
        """Get PUID and PGID (for Linux)."""
        if self.is_linux:
            return os.getuid(), os.getgid()
        return 1000, 1000

    def run(self) -> None:
        console.print("[bold green]Welcome to the PYAMS Installer![/bold green]")

        if self.is_windows:
            if not self.check_windows_virtualization():
                return

        if not self.check_dependencies():
            return

        # Ensure configuration directory exists
        if not self.install_path.exists():
            self.install_path.mkdir(parents=True, exist_ok=True)
            console.print(
                f"[blue]Created configuration directory at {self.install_path}[/blue]"
            )

        self.config["INSTALL_DIRECTORY"] = self.install_path

        # 2. Basic Info
        self.config["PUID"] = int(
            Prompt.ask("Enter PUID", default=str(self.config["PUID"]))
        )

        self.config["PGID"] = int(
            Prompt.ask("Enter PGID", default=str(self.config["PGID"]))
        )

        self.config["TZ"] = Prompt.ask("Enter Timezone", default=self.config["TZ"])

        # Set PODMAN_SOCK based on OS and PUID
        if self.is_linux:
            if self.config["PUID"] == 0:
                default_sock: str = "/run/podman/podman.sock"
            else:
                default_sock: str = (
                    f"/run/user/{self.config['PUID']}/podman/podman.sock"
                )
            self.config["PODMAN_SOCK"] = self.config["PODMAN_SOCK"] or default_sock
        else:
            self.config["PODMAN_SOCK"] = r"//./pipe/podman-machine-default"

        # 3. Media Directory
        if self.is_linux:
            self.config["MEDIA_DIRECTORY"] = Path(
                Prompt.ask(
                    "Where is your media stored?",
                    default=str(self.config["MEDIA_DIRECTORY"]),
                )
            )
        else:
            self.config["MEDIA_DIRECTORY"] = INSTALL_PATH / "media"

        # 5. VPN Configuration (Optional)
        vpn_configured: bool = bool(self.config["VPN_SERVICE"])
        if Confirm.ask(
            "Would you like to configure VPN (GluTun)?",
            default=self.config["USE_VPN"] or vpn_configured,
        ):
            self.config["USE_VPN"] = True
            self.config["VPN_SERVICE"] = Prompt.ask(
                "VPN Provider (e.g. protonvpn, mullvad, expressvpn)",
                default=self.config["VPN_SERVICE"],
            )

            self.config["VPN_TYPE"] = Prompt.ask(
                "VPN Type",
                choices=["openvpn", "wireguard"],
                default=self.config["VPN_TYPE"] or "openvpn",
            )

            if self.config["VPN_TYPE"] == "openvpn":
                self.config["VPN_USER"] = Prompt.ask(
                    "VPN Username", default=self.config["VPN_USER"]
                )
                self.config["VPN_PASSWORD"] = Prompt.ask(
                    "VPN Password", password=True, default=self.config["VPN_PASSWORD"]
                )
                self.config["WIREGUARD_PRIVATE_KEY"] = ""  # Clear if switching types
            else:
                self.config["WIREGUARD_PRIVATE_KEY"] = Prompt.ask(
                    "WireGuard Private Key",
                    password=True,
                    default=self.config["WIREGUARD_PRIVATE_KEY"],
                )
                self.config["VPN_USER"] = ""
                self.config["VPN_PASSWORD"] = ""

            # Port Forwarding
            self.config["VPN_PORT_FORWARDING"] = Confirm.ask(
                "Enable VPN Port Forwarding?",
                default=self.config["VPN_PORT_FORWARDING"],
            )

            if self.config["VPN_PORT_FORWARDING"]:
                self.config["PORT_FORWARDING"] = True
                self.config["VPN_PORT_FORWARDING_PROVIDER"] = Prompt.ask(
                    "Port Forwarding Provider",
                    default=self.config["VPN_PORT_FORWARDING_PROVIDER"]
                    or self.config["VPN_SERVICE"],
                )
            else:
                self.config["PORT_FORWARDING"] = False

            self.config["USE_PROWLARR_VPN"] = Confirm.ask(
                "Put Prowlarr behind VPN?", default=self.config["USE_PROWLARR_VPN"]
            )
        else:
            self.config["USE_VPN"] = False
            self.config["USE_PROWLARR_VPN"] = False
            self.config["VPN_PORT_FORWARDING"] = False
            self.config["PORT_FORWARDING"] = False

        # 6. Generate API Keys if they don't exist
        for key in [
            "SONARR_API_KEY",
            "RADARR_API_KEY",
            "PROWLARR_API_KEY",
            "BAZARR_API_KEY",
        ]:
            if not self.config[key]:
                self.config[key] = secrets.token_hex(16)
                console.print(f"[dim]Generated new {key}[/dim]")

        # 7. Save Files & Create Directories
        self.save_files()
        self.create_directories()

        console.print(
            f"\n[bold green]PYAMS configured at {self.install_path}![/bold green]"
        )
        console.print(
            f"[bold green]Media directory set to {self.config['MEDIA_DIRECTORY']}[/bold green]"
        )

    def save_files(self) -> None:
        """Load the template compose file and save it along with the .env file."""
        from importlib.resources import files

        with console.status("[blue]Saving configuration files..."):
            template_name: str = (
                "linux-podman-compose.yml"
                if self.is_linux
                else "windows-podman-compose.yml"
            )

            try:
                # 1. Save .env file
                env_content: str = ""
                for k, v in self.config.items():
                    val: str
                    if k in ["VPN_PORT_FORWARDING", "PORT_FORWARDING"]:
                        val = "on" if v else "off"
                    elif k in ["MEDIA_DIRECTORY", "INSTALL_DIRECTORY"]:
                        val = v.as_posix() if isinstance(v, Path) else v
                    else:
                        val = (
                            ("true" if v else "false")
                            if isinstance(v, bool)
                            else str(v)
                        )
                    env_content += f"{k}={val}\n"

                with open(self.install_path / ".env", "w") as f:
                    f.write(env_content)

                # 2. Modify and Save podman-compose.yml
                template_path: Any = files("pyams.templates").joinpath(template_name)
                compose_data: dict[str, Any]
                with template_path.open("r") as f:
                    compose_data = yaml.safe_load(f)

                if self.config["USE_VPN"]:
                    gluetun: dict[str, Any] | None = compose_data["services"].get(
                        "gluetun"
                    )
                    if gluetun:
                        if "ports" not in gluetun:
                            gluetun["ports"] = []

                        # Route qBittorrent
                        qbit: dict[str, Any] | None = compose_data["services"].get(
                            "qbittorrent"
                        )
                        if qbit:
                            p: str
                            for p in qbit.pop("ports", []):
                                if p not in gluetun["ports"]:
                                    gluetun["ports"].append(p)
                            qbit["network_mode"] = "service:gluetun"
                            qbit.setdefault("depends_on", []).append("gluetun")
                            s: str
                            for s in ["sonarr", "radarr", "prowlarr", "bazarr"]:
                                if s in compose_data["services"]:
                                    compose_data["services"][s].setdefault(
                                        "environment", []
                                    ).append("QBITTORRENT_HOST=gluetun")

                        # Route Prowlarr
                        if self.config["USE_PROWLARR_VPN"]:
                            prowlarr: dict[str, Any] | None = compose_data[
                                "services"
                            ].get("prowlarr")
                            if prowlarr:
                                for p in prowlarr.pop("ports", []):
                                    if p not in gluetun["ports"]:
                                        gluetun["ports"].append(p)
                                prowlarr["network_mode"] = "service:gluetun"
                                prowlarr.setdefault("depends_on", []).append("gluetun")
                                for s in ["sonarr", "radarr", "bazarr"]:
                                    if s in compose_data["services"]:
                                        compose_data["services"][s].setdefault(
                                            "environment", []
                                        ).append("PROWLARR_HOST=gluetun")
                                prowlarr.setdefault("environment", []).append(
                                    "PROWLARR_HOST=gluetun"
                                )
                else:
                    if "gluetun" in compose_data.get("services", {}):
                        del compose_data["services"]["gluetun"]

                # 3. Add initialization scripts
                scripts_dir: Any = files("pyams.templates").joinpath("scripts")
                target_scripts_base: Path = self.install_path / "scripts"
                target_scripts_base.mkdir(parents=True, exist_ok=True)

                for svc in [
                    "sonarr",
                    "radarr",
                    "prowlarr",
                    "qbittorrent",
                    "bazarr",
                    "jellyfin",
                ]:
                    script_name: str = f"{svc}-init.sh"
                    script_source: Any = scripts_dir.joinpath(script_name)
                    if script_source.exists():
                        target_script: Path = target_scripts_base / script_name
                        with (
                            script_source.open("r") as src,
                            open(target_script, "w", newline="\n") as dst,
                        ):
                            dst.write(src.read())
                        if self.is_linux:
                            target_script.chmod(0o755)

                with open(self.install_path / "podman-compose.yml", "w") as f:
                    yaml.dump(compose_data, f, sort_keys=False)

            except Exception as e:
                console.print(f"[red]Failed to generate configuration: {e}[/red]")

    def create_directories(self) -> None:
        """Create necessary directories for configuration and media."""
        with console.status("[blue]Creating directory structure..."):
            # Media directories
            media_path: Path = self.config["MEDIA_DIRECTORY"]
            media_subdirs: list[str] = [
                "movies",
                "tv",
                "tvshows",
                "music",
                "books",
                "downloads",
            ]
            for subdir in media_subdirs:
                target_path: Path = media_path / subdir
                target_path.mkdir(parents=True, exist_ok=True)
                if self.is_linux:
                    try:
                        os.chmod(target_path, 0o777)
                    except PermissionError:
                        pass

            # Config directories
            config_path: Path = self.install_path / "config"
            config_path.mkdir(parents=True, exist_ok=True)

            with open(self.install_path / "podman-compose.yml", "r") as f:
                compose_data: dict[str, Any] = yaml.safe_load(f)

            for service_name in compose_data.get("services", {}).keys():
                service_config_path: Path = config_path / service_name
                service_config_path.mkdir(parents=True, exist_ok=True)
                if self.is_linux:
                    try:
                        os.chmod(service_config_path, 0o777)
                    except PermissionError:
                        pass

        console.print("[green]Directories created successfully![/green]")
