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

### 1. Borderless Overlay UI ✅ **COMPLETED**
- [x] Remove window decorations (title bar, close/minimize buttons)
- [x] Overlay/HUD-style interface that floats above other windows
- [x] Minimal visual chrome - just text input with subtle border/shadow
- [x] Center on screen, multi-monitor support
- [x] Using tkinter splash window type for borderless effect
- [x] Keep stdlib-only approach (no CustomTkinter dependency)

### 2. Global Hotkey Integration ✅ **COMPLETED**
- [x] System-level hotkey to spawn Quip from anywhere
- [x] Works regardless of current application focus
- [x] Configurable hotkey with user-friendly syntax (win+space)
- [x] Background daemon with auto-reload on config changes
- [x] File watching for instant configuration updates

### 3. Easy Installation + Auto-Updates
**Priority: High**
- [ ] GitHub release-based installer script
- [ ] One-liner: `curl -sSL raw.githubusercontent.com/user/quip/main/install.sh | bash`
- [ ] Handles uv installation if needed
- [ ] Cross-platform support (Linux primary, macOS secondary)
- [ ] Easy to share with friends
- [ ] **Auto-update system**:
  - [ ] Check GitHub releases API for newer versions
  - [ ] Background update checking (configurable frequency)
  - [ ] Seamless reinstall/upgrade process
  - [ ] Option to disable auto-updates
  - [ ] Update notifications in UI (subtle, non-intrusive)

### 4. Optional LLM Cleanup
**Priority: High**
- [ ] Integration with local Ollama (OpenAI-compatible API)
- [ ] Second hotkey while in Quip to request cleanup (e.g., Ctrl+L)
- [ ] Subtle organization and clarification nudges
- [ ] Fast, non-blocking operation
- [ ] User can accept/reject suggestions
- [ ] 90% of time: just save and go; 10%: cleanup first

### 5. Voice Recording Integration
**Priority: Medium**
- [ ] Hotkey to start recording (opens Quip + starts recording)
- [ ] Speech-to-text transcription into text field
- [ ] Integration with existing nerd dictation setup
- [ ] Local processing preferred (whisper.cpp or similar)
- [ ] Can edit transcription before saving

## Technical Approach

### UI Framework Decision ✅ **RESOLVED**
- **Tkinter (splash window)** - Stdlib-only, borderless overlay achieved
- Simple, fast, universally compatible

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
3. **Installation + auto-update system** - Make it portable, shareable, and self-updating
4. **LLM integration** - Add optional cleanup capability
5. **Voice recording** - Add speech input option

## Next Priority Tasks
- [ ] Create GitHub release-based installer with auto-update checking
- [ ] Add auto-start daemon on system boot (systemd service)
- [ ] Implement LLM integration with Ollama for note cleanup
- [ ] Add voice recording with speech-to-text

## Non-Goals
- Complex note organization (separate project handles this)
- Multiple themes/customization
- Sync/cloud features
- Rich text editing
- Plugin architecture

Keep it focused on the core capture experience.