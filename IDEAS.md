# Ideas & Future Improvements

This file captures ideas for improving Quip's user experience and functionality.

## UI/UX Enhancements

### Information Overlay
- **Low contrast info icon** in bottom corner
  - Shows on hover: "About Quip" + keyboard shortcuts
  - Shortcuts: `Esc` to quit, `Ctrl+Enter`/`Ctrl+D` to save & exit
  - Minimal, unobtrusive design that doesn't interfere with typing

### Visual Improvements
- **True rounded corners** (investigate OS-level window properties)
- **Better multi-monitor centering** (detect primary monitor accurately)
- **Subtle animations** for window appearance/disappearance
- **Theme customization** (light mode, custom colors)

## Functionality Ideas

### Input Methods
- **Voice recording support** with speech-to-text
- **Markdown shortcuts** (auto-formatting as you type)
- **Quick templates** (meeting notes, todos, etc.)

### AI Integration
- **Optional LLM cleanup** with local Ollama
- **Smart categorization** of notes
- **Auto-tagging** based on content

### System Integration
- **Global hotkey** to spawn from anywhere
- **System tray integration**
- **Auto-updates** via GitHub releases
- **Cross-platform launcher** scripts

## Technical Improvements

### Configuration & Debugging
- **Config file support** - Store preferences in `~/.config/quip/config.toml`
  - Window size, position preferences
  - Theme customization (colors, fonts)
  - Default save location
  - Hotkey bindings
- **Debug mode** - CLI flag (`--debug`) and/or config option
  - Monitor detection logging
  - Window positioning details
  - Focus management diagnostics
- **Settings UI** - Simple overlay for config management
  - Toggle debug mode
  - Adjust window size/transparency
  - Change themes and colors

### Performance
- **Faster startup time**
- **Memory optimization**
- **Background service** option

### Storage
- **Note organization** beyond simple inbox
- **Search functionality** across all notes
- **Export options** (PDF, various formats)

---

## Contributing Ideas

To add new ideas:
1. Add to appropriate section above
2. Include brief description and rationale
3. Mark priority level if relevant (High/Medium/Low)
4. Reference any related GitHub issues

## Process

Ideas should be:
- **Specific enough** to be actionable
- **Aligned with** the core philosophy of frictionless capture
- **Considerate of** the minimal, unobtrusive design goal