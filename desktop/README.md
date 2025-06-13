# Quip Desktop

The desktop application for Quip - a frictionless thought capture tool.

## Overview

Python tkinter application that provides instant thought capture via global hotkey. Currently a simple dark-themed overlay that saves notes to `~/notes/5. Inbox/Inbox.md`.

## Installation

```bash
cd desktop
uv sync --group dev
uv run quip
```

## Development

```bash
# Lint and format
uv run ruff check
uv run ruff format

# Install pre-commit hooks
uv run pre-commit install
```

## Controls

- `Ctrl+Enter` or `Ctrl+D`: Save note and exit
- `Escape`: Exit without saving

## Planned Improvements

See [../DEVELOPMENT.md](../DEVELOPMENT.md) for the complete roadmap. Priority for desktop:

1. **Borderless overlay UI** - Remove window decorations for true HUD experience
2. **Global hotkey system** - Spawn from anywhere
3. **LLM integration** - Optional cleanup with local Ollama
4. **Voice recording** - Speech-to-text support

## Architecture

- Single-file application (`main.py`)
- Standard library only (tkinter, pathlib)
- Dark theme optimized for low distraction
- GNOME/Linux focus management
