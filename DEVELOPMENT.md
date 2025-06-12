# Quip Development Plan

**Vision**: A frictionless thought capture tool that interrupts your workflow as little as possible. Press hotkey → capture thought → back to work.

## Current State

✅ **Feature-Complete v0.5.2**
- Python/tkinter desktop app with borderless overlay
- Global hotkey system (Win+Space) with background daemon
- TOML-based configuration with file watching and auto-reload
- Multi-monitor support with xrandr detection
- Dark theme with clean UI (no flash, no borders)
- Configurable: window size, transparency, save path, debug mode
- Saves notes to configurable path (default: `~/notes/5. Inbox/Inbox.md`)
- Core hotkeys: `Ctrl+Enter`/`Ctrl+D` to save, `Escape` to exit, `Ctrl+S` for settings
- **Curator mode**: `Ctrl+L` for interactive note improvement with LLM feedback
- **Context-aware improvements**: `Ctrl+I` uses curator feedback for better results
- Python package with `uv` dependency management
- One-liner installer with autostart support

## Core Philosophy
- **Minimize cognitive overhead** - Should feel like an extension of your brain
- **Instant capture** - Idea pops up → hotkey → type/speak → save → continue
- **Unobtrusive design** - Overlay/HUD element, not a traditional window
- **Optional enhancement** - LLM cleanup available but not required

## Active Priorities

### 1. UI Polish & Discoverability
- Add subtle info icon (circle with "i") in bottom right corner
- Hover tooltip showing available hotkeys and features
- Make curator mode and LLM features discoverable to new users
- Clean, minimal design that doesn't clutter the interface

### 2. Voice Recording Integration
- Speech-to-text integration (whisper.cpp preferred)
- Hotkey to start recording mode
- Edit transcription before saving

## Technical Notes

- **UI**: Tkinter splash window (stdlib-only, borderless overlay)
- **Hotkeys**: pynput library with config normalization
- **Config**: TOML files with file watching for live reload
- **Install**: GitHub releases + shell script with uv dependency management
- **License**: SSPL (prevents commercial hosting abuse)

## Success Metrics
- **Speed**: Hotkey to save in < 2 seconds
- **Invisibility**: Doesn't break flow of current work  
- **Reliability**: Always captures thoughts, never loses data

## Non-Goals
- Complex note organization (use separate tools)
- Multiple themes/customization  
- Sync/cloud features
- Rich text editing
- Plugin architecture

## Ideas for Future

See [IDEAS.md](IDEAS.md) for additional feature ideas and improvements.

Keep it focused on instant thought capture.