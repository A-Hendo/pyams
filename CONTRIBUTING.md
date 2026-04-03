# Contributing to PYAMS

Thank you for your interest in contributing to PYAMS! This project is a modern, Python-based replacement for YAMS, and we welcome improvements, bug fixes, and new features.

## Development Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and packaging.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/a-hendo/pyams.git
    cd pyams
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv sync
    ```

3.  **Run the CLI in development mode**:
    ```bash
    uv run pyams --help
    ```

## Project Structure

- `src/pyams/`: The main package directory.
  - `main.py`: Entry point and Typer command definitions.
  - `install.py`: The installation wizard and configuration logic.
  - `containers.py`: Core logic for interacting with Podman/Podman-Compose.
  - `vpn.py`: VPN checking and IP verification logic.
  - `utils.py`: Backup, restore, and other utility functions.
  - `templates/`: YAML templates for the Podman Compose configurations.

## Coding Standards

- **Type Hinting**: All new functions and classes must include Python 3.10+ type hints (e.g., use `list[str] | None` instead of `Optional[List[str]]`).
- **Formatting**: We use `ruff` for formatting and linting. Please ensure your code passes linting before submitting a PR.
- **Rich UI**: Use the `rich` library for terminal output to maintain a consistent and professional look and feel.
- **Cross-Platform**: Always ensure that paths and subprocess calls work on both Linux and Windows. Use `pathlib.Path` for all path manipulations.

## How to Contribute

1.  **Check for Issues**: Look at the existing issues or open a new one to discuss your proposed changes.
2.  **Fork and Branch**: Create a feature branch for your work.
3.  **Submit a PR**: Once your changes are tested and linted, submit a Pull Request with a clear description of what you've done.

## License

By contributing to PYAMS, you agree that your contributions will be licensed under the project's MIT License.
