# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Vision

Quip is a **frictionless thought capture tool** - Press hotkey → capture thought → back to work.

**Core Philosophy**: Minimize cognitive overhead. This should feel like an extension of your brain, not a separate app. 90% of the time: type → save → continue. 10% of the time: type → AI cleanup → save → continue.

## Current State & Architecture

- **Monorepo structure**: `desktop/`, `mobile/`, `web/`, `server/`, `shared/` components
- **Desktop app**: Single-file Python app in `desktop/main.py`
- **Note storage**: Saves to `~/notes/5. Inbox/Inbox.md` with `---` delimiter between entries
- **GUI**: Centered, dark-themed tkinter window with focus management for Linux/GNOME
- **Simple but functional**: Works, but needs to become truly unobtrusive overlay

## Development Direction

See [DEVELOPMENT.md](DEVELOPMENT.md) and [README.md](README.md) for complete roadmap. Priority improvements:

1. **Borderless overlay UI** - Remove window decorations, true HUD experience
2. **Global hotkey system** - Spawn from anywhere, not just when focused
3. **Optional LLM cleanup** - Integrate with local Ollama for note clarification
4. **Easy installation** - One-liner GitHub release installer
5. **Voice recording** - Speech-to-text integration

## Running the Application

Desktop app:
```bash
cd desktop
uv run quip
# or
uv run python main.py
```

## Setup

Install dependencies and set up the project:
```bash
cd desktop
uv sync --group dev
uv run pre-commit install
```

## Development Process

**Always run pre-commit hooks before committing:**
```bash
cd desktop
uv run ruff check desktop/ --fix
uv run ruff format desktop/
uv run pre-commit run --all-files
```

**Use Conventional Commits for clean history:**
- `feat:` - New features (e.g., "feat: add global hotkey support")
- `fix:` - Bug fixes (e.g., "fix: window focus on GNOME")
- `refactor:` - Code improvements (e.g., "refactor: extract UI components")
- `docs:` - Documentation (e.g., "docs: update installation guide")
- `style:` - Formatting only (e.g., "style: fix ruff warnings")
- `chore:` - Maintenance (e.g., "chore: update dependencies")

**Commit Guidelines:**
- Keep commits small and focused on single changes
- Always run pre-commit hooks before committing
- Use imperative mood ("add" not "added")
- Be descriptive but concise

## Key Controls

- `Ctrl+Enter` or `Ctrl+D`: Save note and exit
- `Escape`: Exit without saving
- Window close button: Exit without saving

## Development Notes

- The application uses standard library only (tkinter, pathlib, os)
- Dark theme colors: background `#2b2b2b`, foreground `#ffffff`
- Window size: 800x150px, centered on screen
- GNOME-specific window attributes for proper behavior on Ubuntu/Linux