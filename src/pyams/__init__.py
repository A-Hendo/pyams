import importlib.metadata

try:
    __version__ = importlib.metadata.version("pyams")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development where the package isn't "installed"
    __version__ = "0.1.0-dev"
