import platform
from pathlib import Path
from typing import Any
from dotenv import dotenv_values

# --- 1. SYSTEM DETECTION ---
OS: str = platform.system().lower()
IS_LINUX: bool = OS == "linux"
IS_WINDOWS: bool = OS == "windows"

# --- 2. BASE PATHS ---
INSTALL_PATH: Path = (
    Path.home() / ".config" / "pyams"
    if IS_LINUX
    else Path.home() / "AppData" / "Roaming" / "pyams"
)

# --- 3. DEFAULTS ---
DEFAULTS: dict[str, Any] = {
    "PUID": 1000,
    "PGID": 1000,
    "TZ": "UTC",
    "MEDIA_DIRECTORY": (
        Path.home() / "media" / "pyams"
        if IS_LINUX
        else INSTALL_PATH / "media"
    ),
    "INSTALL_DIRECTORY": INSTALL_PATH,
    "VPN_SERVICE": "",
    "VPN_TYPE": "openvpn",
    "VPN_USER": "",
    "VPN_PASSWORD": "",
    "WIREGUARD_PRIVATE_KEY": "",
    "VPN_PORT_FORWARDING": False,
    "PORT_FORWARDING": False,
    "VPN_PORT_FORWARDING_PROVIDER": "",
    "USE_VPN": False,
    "USE_PROWLARR_VPN": False,
    "PODMAN_SOCK": "",
    "SONARR_API_KEY": "",
    "RADARR_API_KEY": "",
    "PROWLARR_API_KEY": "",
    "BAZARR_API_KEY": "",
}


def load_config() -> dict[str, Any]:
    """Load configuration from .env file and apply type casting."""
    config: dict[str, Any] = DEFAULTS.copy()
    env_file: Path = INSTALL_PATH / ".env"

    if not env_file.exists():
        return config

    try:
        loaded: dict[str, Any | None] = dotenv_values(env_file)
        for key, value in loaded.items():
            if value is None:
                continue

            if key in config:
                # Type Casting
                if key in ["PUID", "PGID"]:
                    try:
                        config[key] = int(value)
                    except ValueError:
                        pass
                elif key in [
                    "USE_VPN",
                    "USE_PROWLARR_VPN",
                    "VPN_PORT_FORWARDING",
                    "PORT_FORWARDING",
                ]:
                    config[key] = value.lower() in ["true", "on"]
                elif key in ["MEDIA_DIRECTORY", "INSTALL_DIRECTORY"]:
                    config[key] = Path(value)
                else:
                    config[key] = value
    except Exception:
        # If loading fails, we fallback to defaults silently
        pass

    return config


# --- 4. SINGLETON INSTANCE ---
# This object will be imported by all other modules
settings: dict[str, Any] = load_config()
