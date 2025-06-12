# Quip Development Plan

**Vision**: A frictionless thought capture tool that interrupts your workflow as little as possible. Press hotkey → capture thought → back to work.

## Current State
- Simple tkinter GUI with dark theme
- Saves notes to `~/notes/5. Inbox/Inbox.md`
- Basic keyboard shortcuts (Ctrl+Enter/Ctrl+D to save, Escape to exit)
- Python package with `uv` dependency management

## Core Philosophy
- **Minimize cognitive overhead** - Should feel like an extension of your brain
- **Instant capture** - Idea pops up → hotkey → type/speak → save → continue
- **Unobtrusive design** - Overlay/HUD element, not a traditional window
- **Optional enhancement** - LLM cleanup available but not required

## Priority Improvements

### 1. Borderless Overlay UI
**Priority: Critical**
- [ ] Remove window decorations (title bar, close/minimize buttons)
- [ ] Overlay/HUD-style interface that floats above other windows
- [ ] Minimal visual chrome - just text input with subtle border/shadow
- [ ] Center on screen, fixed size initially
- [ ] Evaluate frameworks: CustomTkinter, or stay with tkinter frameless
- [ ] Test different levels of transparency/visual weight

### 2. Global Hotkey Integration  
**Priority: Critical**
- [ ] System-level hotkey to spawn Quip from anywhere
- [ ] Works regardless of current application focus
- [ ] Configurable hotkey (default suggestion: Ctrl+Shift+Space)
- [ ] Cross-platform hotkey handling

### 3. Optional LLM Cleanup
**Priority: High**
- [ ] Integration with local Ollama (OpenAI-compatible API)
- [ ] Second hotkey while in Quip to request cleanup (e.g., Ctrl+L)
- [ ] Subtle organization and clarification nudges
- [ ] Fast, non-blocking operation
- [ ] User can accept/reject suggestions
- [ ] 90% of time: just save and go; 10%: cleanup first

### 4. Voice Recording Integration
**Priority: Medium**
- [ ] Hotkey to start recording (opens Quip + starts recording)
- [ ] Speech-to-text transcription into text field
- [ ] Integration with existing nerd dictation setup
- [ ] Local processing preferred (whisper.cpp or similar)
- [ ] Can edit transcription before saving

### 5. Easy Installation
**Priority: High**
- [ ] GitHub release-based installer script
- [ ] One-liner: `curl -sSL raw.githubusercontent.com/user/quip/main/install.sh | bash`
- [ ] Handles uv installation if needed
- [ ] Cross-platform support (Linux primary, macOS secondary)
- [ ] Easy to share with friends

## Technical Approach

### UI Framework Options
- **Tkinter (frameless)** - Keep it simple, remove decorations
- **CustomTkinter** - Better styling while staying lightweight  
- **PyQt6** - More control over window behavior
- **Web-based overlay** - Ultimate flexibility but more complex

### LLM Integration
- Use existing local Ollama instance
- OpenAI-compatible API calls
- Simple prompt: "Clean up and clarify this quick note: [text]"
- Non-blocking async requests

### Installation Strategy
- GitHub releases with bundled executables
- Install script handles dependencies
- Portable where possible

## Success Metrics
- **Speed**: Hotkey to save in < 2 seconds
- **Invisibility**: Doesn't break flow of current work
- **Reliability**: Always captures the thought, never loses data
- **Adoption**: Easy enough to install that you actually use it on new machines

## Implementation Order
1. **Borderless UI experiment** - Test different approaches for minimal window
2. **Global hotkey** - Make it accessible from anywhere
3. **LLM integration** - Add optional cleanup capability
4. **Installation script** - Make it portable and shareable
5. **Voice recording** - Add speech input option

## Non-Goals
- Complex note organization (separate project handles this)
- Multiple themes/customization
- Sync/cloud features
- Rich text editing
- Plugin architecture

Keep it focused on the core capture experience.