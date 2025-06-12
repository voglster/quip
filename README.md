# Quip

A frictionless thought capture tool designed to interrupt your workflow as little as possible.

## Vision

Press hotkey → capture thought → back to work.

Quip is built for those moments when an idea pops into your head and you need to capture it *instantly* without breaking your flow. No windows to manage, no apps to switch to - just pure, instant thought capture.

## Current Features

- **Instant capture**: Global hotkey spawns a minimal overlay
- **Dark theme**: Easy on the eyes during late-night inspiration
- **Automatic save**: Notes go to `~/notes/5. Inbox/Inbox.md`
- **Zero friction**: Escape to dismiss, Ctrl+Enter to save

## Quick Start

```bash
# Quick install (coming soon)
curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash

# Manual install
git clone https://github.com/voglster/quip.git
cd quip/desktop
uv sync
uv run quip
```

## Components

- **[desktop/](desktop/)** - Python tkinter app for instant thought capture
- **[mobile/](mobile/)** - Expo/React Native mobile companion (planned)
- **[web/](web/)** - Web interface for note review and management (planned)  
- **[server/](server/)** - Backend API for sync and processing (planned)
- **[shared/](shared/)** - Common utilities and types (planned)

## Usage

1. Press your configured hotkey (default: `Ctrl+Shift+Space`)
2. Type your thought
3. Press `Ctrl+Enter` to save, or `Escape` to dismiss
4. Continue with what you were doing

## Planned Improvements

### Core Enhancements
- **Borderless overlay UI** - Remove window decorations for true overlay experience
- **Global hotkey system** - Spawn from anywhere, regardless of current app
- **LLM cleanup** - Optional AI-powered note clarification (integrates with local Ollama)
- **Voice recording** - Speak your thoughts, get them transcribed

### Philosophy
This tool is intentionally minimal. It does one thing well: captures errant thoughts without breaking your concentration. 

- 90% of the time: type → save → continue
- 10% of the time: type → cleanup with AI → save → continue

No complex organization, no sync, no themes. Just instant, reliable thought capture.

## Technical Details

- **Built with**: Python + tkinter (for now)
- **Storage**: Plain text markdown files
- **Requirements**: Python 3.8+, managed with `uv`
- **Target platforms**: Linux (primary), macOS (secondary)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the complete roadmap and implementation plan.

### Setup
```bash
# Desktop development
cd desktop
uv sync --group dev
uv run pre-commit install
```

### Development Workflow
```bash
# Run the app
uv run quip

# Code quality (run before committing)
uv run ruff check desktop/ --fix
uv run ruff format desktop/
uv run pre-commit run --all-files

# Commit changes
git add .
git commit -m "feat: add new feature"
```

### Commit Style
Use [Conventional Commits](https://www.conventionalcommits.org/) for clean history:

- `feat:` - New features
- `fix:` - Bug fixes  
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `style:` - Code style/formatting
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Keep commits small, focused, and incremental. Run pre-commit hooks before every commit.

## Why Quip?

Because good ideas don't wait for you to open the right app, find the right document, or switch contexts. They appear in the shower, during meetings, while debugging, at 2 AM.

Quip is there for those moments.

---

*Currently in active development - expect rapid iteration as we perfect the capture experience.*