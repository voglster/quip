# Quip Development Plan

**Vision**: A frictionless thought capture tool that interrupts your workflow as little as possible. Press hotkey → capture thought → back to work.

## Current State

✅ **Feature-Complete v0.3**
- Python/tkinter desktop app with borderless overlay
- Global hotkey system (Win+Space) with background daemon
- TOML-based configuration with file watching and auto-reload
- Multi-monitor support with xrandr detection
- Dark theme with clean UI (no flash, no borders)
- Configurable: window size, transparency, save path, debug mode
- Saves notes to configurable path (default: `~/notes/5. Inbox/Inbox.md`)
- Core hotkeys: `Ctrl+Enter`/`Ctrl+D` to save, `Escape` to exit
- Python package with `uv` dependency management

## Core Philosophy
- **Minimize cognitive overhead** - Should feel like an extension of your brain
- **Instant capture** - Idea pops up → hotkey → type/speak → save → continue
- **Unobtrusive design** - Overlay/HUD element, not a traditional window
- **Optional enhancement** - LLM cleanup available but not required

## Priority Improvements

## Completed Features ✅

- **Borderless Overlay UI** - Tkinter splash window, multi-monitor support
- **Global Hotkey System** - Win+Space spawns from anywhere, configurable
- **Background Daemon** - File watching, auto-reload config, debug mode
- **Easy Installation** - One-liner installer with auto-update system
- **GitHub Releases** - Automated releases, CLI update commands
- **SSPL License** - Prevents commercial hosting abuse
- **Autostart System** - Desktop autostart files for reliable GUI daemon startup
- **Settings Hotkey** - Ctrl+S while Quip open to edit config in default editor

## Active Priorities

### 1. Optional LLM Cleanup
- Integration with local Ollama (OpenAI-compatible API)
- Second hotkey for cleanup while in Quip (e.g., Ctrl+L)
- Fast, non-blocking operation with accept/reject

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
- Move the notes file path to a config in the system section
- Voice recording integration with whisper.cpp
- Optional LLM cleanup with local Ollama

Keep it focused on instant thought capture.