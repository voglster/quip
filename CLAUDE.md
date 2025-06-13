# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Vision

Quip is a **frictionless thought capture tool** - Press hotkey → capture thought → back to work.

**Core Philosophy**: Minimize cognitive overhead. This should feel like an extension of your brain, not a separate app. 90% of the time: type → save → continue. 10% of the time: type → AI cleanup → save → continue.

## Current State & Architecture

- **Monorepo structure**: `desktop/`, `mobile/`, `web/`, `server/`, `shared/` components
- **Desktop app**: Modular Python application with clean, testable architecture
- **Note storage**: Saves to `~/notes/5. Inbox/Inbox.md` with `---` delimiter between entries
- **GUI**: Centered, dark-themed tkinter window with focus management for Linux/GNOME
- **Refactored Architecture**: Well-organized, maintainable codebase:
  - `ui/` - UI components (window management, overlays, text widgets)
  - `core/` - Core application logic (app controller, note management)
  - `voice/` - Voice recording and transcription handling
  - `curator/` - LLM functionality and note improvement
  - `tests/` - Comprehensive test suite with 75+ tests and coverage reporting

## Development Direction

See [DEVELOPMENT.md](DEVELOPMENT.md) and [README.md](README.md) for complete roadmap and tasks.

**Always check DEVELOPMENT.md for current tasks and todos before starting work.**

Priority improvements:
1. **Borderless overlay UI** - Remove window decorations, true HUD experience
2. **Global hotkey system** - Spawn from anywhere, not just when focused
3. **Easy installation + auto-updates** - One-liner GitHub installer with seamless update checking
4. **Optional LLM cleanup** - Integrate with local Ollama for note clarification
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
uv run ruff check . --fix
uv run ruff format .
uv run pytest tests/ --cov=. --cov-fail-under=80
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
- **DO NOT** include Claude Code attribution in commit messages

## Key Controls

- `Ctrl+Enter` or `Ctrl+D`: Save note and exit
- `Escape`: Exit without saving
- Window close button: Exit without saving

## Development Notes

- **Architecture**: Clean separation of concerns with modular design
- **Testing**: Comprehensive test suite with pytest, coverage reporting, and pre-commit integration
- **Dependencies**: Core app uses standard library (tkinter, pathlib, os) + minimal external deps
- **Dark theme colors**: background `#2b2b2b`, foreground `#ffffff`
- **Window size**: 800x150px, centered on screen
- **GNOME-specific**: Window attributes for proper behavior on Ubuntu/Linux

## Testing

Run the full test suite:
```bash
cd desktop
uv run pytest tests/ -v --cov=. --cov-report=html
```

Run specific test modules:
```bash
uv run pytest tests/test_note_manager.py -v
uv run pytest tests/test_window_manager.py -v
```