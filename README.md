# PYAMS (Yet Another Python Media Server)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux / Windows](https://img.shields.io/badge/platform-linux%20%7C%20windows-lightgrey.svg)](#requirements)

PYAMS is an automated, Zero-Config, cross-platform Python CLI for managing a full media server stack using Podman.

## Features

- **Zero-Config Setup**: Automated initialization for Jellyfin (libraries, admin user) and other services.
- **Smart VPN Routing**: Route qBittorrent and Prowlarr through Gluetun with automatic interface binding (`tun0`).
- **Shell Autocompletion**: Tab-completion for service names across all commands.
- **Cross-Platform**: Full support for both Linux and Windows.
- **Modern CLI**: Beautiful terminal output using `Rich` and `Typer`.
- **Podman Native**: Designed specifically for rootless Podman environments.
- **Smart Configuration**: Centralized settings with automatic type casting and persistent memory.
- **Backup & Restore**: Easily archive your entire configuration and media library.

## Included Services

- **Jellyfin**: Media server and streaming.
- **qBittorrent**: Torrent downloader.
- **Sonarr/Radarr/Prowlarr**: Automation and indexing.
- **Gluetun**: VPN gateway.
- **FlareSolverr**: CAPTCHA bypass for indexers.
- **Watchtower**: Automatic container updates.

## What's Automated?

PYAMS aims for a "one-command" setup. When you run `pyams install`, it handles:

- **System Setup**:
  - Detects PUID/PGID and automatically calculates Podman socket paths.
  - Creates the entire media directory structure (`movies`, `tvshows`, `downloads`, etc.) with correct permissions.
  - Automatically installs Podman and Podman-Compose (Linux) or prompts for Podman Desktop (Windows).
- **Jellyfin**:
  - Sets up the initial server configuration (Language/Country).
  - Creates the default `admin` user (password: `changeme`).
  - Automatically creates and maps "Movies" and "Shows" libraries with real-time monitoring enabled.
  - Completes the initial startup wizard automatically.
- **qBittorrent**:
  - Sets default download paths and configures seeding ratios.
  - Applies an extensive blocklist of junk files (e.g., `.exe`, `.bat`, `.lnk`) to keep your library clean.
  - Configures Web UI security and sets default credentials.
  - Automatically binds to the `tun0` interface when VPN is enabled.
- **Prowlarr**:
  - Automatically configures FlareSolverr as an indexer proxy for CAPTCHA bypass.
  - Connects to qBittorrent and links to Sonarr and Radarr with "Full Sync" enabled.
  - Sets up admin authentication and secure API keys.
- **Sonarr & Radarr**:
  - Configures root media folders (`/data/tvshows` and `/data/movies`).
  - Automatically connects to qBittorrent as the primary download client.
  - Enables Forms Authentication and sets up default admin credentials.
- **Bazarr**:
  - Automatically links to Sonarr and Radarr for subtitle management.
  - Syncs API keys and connection settings across the stack.
- **VPN & Security**:
  - Routes qBittorrent and Prowlarr through the GluTun network stack.
  - Handles OpenVPN and WireGuard configuration, including Port Forwarding.
  - Generates unique, secure random API keys for all services during installation.

## Installation

### Quick Install (Recommended)

**Linux:**

```bash
curl -sSL https://raw.githubusercontent.com/a-hendo/pyams/main/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/a-hendo/pyams/main/install.ps1 | iex
```

### Standalone Binaries

If you prefer manual installation, download the latest pre-compiled binary from the [Releases](https://github.com/a-hendo/pyams/releases) page.

### Using uv

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv tool install git+https://github.com/a-hendo/pyams.git
```

### Shell Autocompletion

PYAMS supports tab-completion for service names (e.g., `pyams logs j[TAB]` -> `jellyfin`). To enable it for your shell:

**Zsh:**

```bash
pyams --install-completion zsh
```

**Bash:**

```bash
pyams --install-completion bash
```

_Note: You may need to restart your terminal or source your shell config for changes to take effect._

## Getting Started

Once installed, simply run the installation wizard:

```bash
pyams install
```

The wizard will guide you through:

1. Checking dependencies (Podman/Podman-Compose).
2. Setting up PUID/PGID and Timezone.
3. Choosing your media storage location.
4. Configuring VPN settings (Optional).

## CLI Usage

### Basic Management

- `pyams start`: Start all containers (or specific ones: `pyams start jellyfin`).
- `pyams stop`: Stop containers (or specific ones: `pyams stop jellyfin`).
- `pyams restart`: Restart containers (or specific ones: `pyams restart jellyfin`).
- `pyams status`: View status of all services (or specific ones: `pyams status jellyfin`).
- `pyams logs`: View live logs for a service (e.g., `pyams logs sonarr`).
- `pyams recycle`: Stop, remove, and recreate containers (or specific ones: `pyams recycle qbittorrent`).
- `pyams update`: Pull the latest images and restart containers (or specific ones: `pyams update sonarr`).

### Tools & Maintenance

- `pyams doctor`: Run a system health check to diagnose setup and permission issues.
- `pyams check-vpn`: Verifies if your IP is correctly masked by the VPN.
- `pyams backup`: Create a compressed backup of your config.
  - `pyams backup /path/to/backup --media`: Include your media library in the backup.
- `pyams restore`: Restore from a previous backup archive.
  - `pyams restore pyams_backup_20260402.tar.gz`
- `pyams remove`: Remove all containers and networks (your data remains safe).
- `pyams destroy`: **Full Cleanup**. Removes containers, volumes, and deletes local configuration and media folders. (Requires double confirmation).

## Requirements

- **Linux**: Podman and Podman-Compose.
- **Windows**: Podman Desktop.
- **Python**: 3.13 or higher.

## Contributing

Please see [Contributing Guide](CONTRIBUTING.md) to get started.

## Supporting the Project

PYAMS is a passion project and is completely free to use. If you find it helpful and would like to support its development, please consider sponsoring through GitHub.
