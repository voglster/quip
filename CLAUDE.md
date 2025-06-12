# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quip is a minimal quick-note GUI application built with Python's tkinter. It creates a centered, dark-themed text input window that saves notes to `~/notes/5. Inbox/Inbox.md`.

## Key Architecture

- **Single-file application**: All functionality is contained in `main.py`
- **Note storage**: Saves to `~/notes/5. Inbox/Inbox.md` with `---` delimiter between entries
- **GUI behavior**: Creates topmost, dialog-type window with focus management for Linux/GNOME environments

## Running the Application

With uv:
```bash
uv run quip
```

Or directly:
```bash
uv run python main.py
```

## Setup

Install dependencies and set up the project:
```bash
uv sync
```

## Key Controls

- `Ctrl+Enter` or `Ctrl+D`: Save note and exit
- `Escape`: Exit without saving
- Window close button: Exit without saving

## Development Notes

- The application uses standard library only (tkinter, pathlib, os)
- Dark theme colors: background `#2b2b2b`, foreground `#ffffff`
- Window size: 800x150px, centered on screen
- GNOME-specific window attributes for proper behavior on Ubuntu/Linux