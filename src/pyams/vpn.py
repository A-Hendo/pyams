import subprocess
import requests
from rich.console import Console
import re

console: Console = Console()

IP_ENDPOINTS: list[str] = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://ident.me",
    "https://checkip.amazonaws.com",
]


def get_ip_with_retries(context: str = "local") -> str | None:
    """Get IP address with retries, either locally or from within a container."""
    endpoint: str
    for endpoint in IP_ENDPOINTS:
        try:
            if context == "local":
                response: requests.Response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    ip: str = response.text.strip()
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                        return ip
            else:
                # Try qbittorrent container via podman exec
                # Using both curl and wget as fallbacks
                cmd: str
                for cmd in ["curl -s --connect-timeout 5", "wget -qO- --timeout=5"]:
                    try:
                        result: subprocess.CompletedProcess[str] = subprocess.run(
                            ["podman", "exec", "qbittorrent", *cmd.split(), endpoint],
                            capture_output=True,
                            text=True,
                            timeout=7,
                        )
                        if result.returncode == 0:
                            ip_val: str = result.stdout.strip()
                            if re.match(
                                r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_val
                            ):
                                return ip_val
                    except Exception:
                        continue
        except Exception:
            continue
    return None


def get_country(ip: str, context: str = "local") -> str:
    """Get country for an IP address."""
    url: str = f"https://ipinfo.io/{ip}/country"
    try:
        if context == "local":
            response: requests.Response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        else:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                [
                    "podman",
                    "exec",
                    "qbittorrent",
                    "curl",
                    "-s",
                    "--connect-timeout",
                    "5",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=7,
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return "Unknown"


def check_vpn() -> None:
    """Check if the VPN is working correctly by comparing local and qbittorrent IPs."""
    console.print("[bold blue]Getting your local IP...[/bold blue]")
    local_ip: str | None = get_ip_with_retries("local")
    if not local_ip:
        console.print(
            "[bold red]Failed to get your local IP address from any endpoint.[/bold red]"
        )
        return

    local_country: str = get_country(local_ip, "local")
    console.print(f"Your Local IP: [cyan]{local_ip}[/cyan] ({local_country})")

    console.print("\n[bold blue]Getting your qBittorrent IP...[/bold blue]")
    # First check if container is running
    try:
        check_container: subprocess.CompletedProcess[str] = subprocess.run(
            ["podman", "ps", "--filter", "name=qbittorrent", "--format", "{{.State}}"],
            capture_output=True,
            text=True,
        )
        if "running" not in check_container.stdout.lower():
            console.print(
                "[bold yellow]qBittorrent container is not running. Please start it first.[/bold yellow]"
            )
            return
    except Exception:
        pass

    qbit_ip: str | None = get_ip_with_retries("qbittorrent")
    if not qbit_ip:
        console.print(
            "[bold red]Failed to get qBittorrent IP from any endpoint.[/bold red]"
        )
        return

    qbit_country: str = get_country(qbit_ip, "qbittorrent")
    console.print(f"qBittorrent IP: [cyan]{qbit_ip}[/cyan] ({qbit_country})")

    console.print("\n" + "=" * 40)
    if local_ip == qbit_ip:
        console.print(
            "[bold red]⚠️  WARNING: Your IPs are the same! qBittorrent is exposing your IP![/bold red]"
        )
    else:
        console.print(
            "[bold green]✅ Success: Your IPs are different. qBittorrent is masking your IP![/bold green]"
        )
    console.print("=" * 40 + "\n")
