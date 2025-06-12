# Autostart System Fix - Context Document

## Current Problem

The systemd service approach for autostarting the Quip daemon doesn't work reliably:

- **Issue**: Systemd user services run in different context than desktop session
- **Symptom**: `ImportError: this platform is not supported: ('failed to acquire X connection: Can\'t connect to display ":0"')`
- **Root Cause**: pynput (global hotkey library) can't access X11/Wayland from systemd context
- **Impact**: Daemon fails to start, hotkeys don't work

## Current State

✅ **Daemon works perfectly when run manually**:
```bash
# This works fine:
uv run quip-daemon start
# Hotkey Win+Space spawns Quip correctly
```

❌ **Systemd service fails**:
```bash
systemctl --user status quip-daemon
# Shows: "failed to acquire X connection"
```

## Solution: Desktop Autostart

Replace systemd with standard desktop autostart entry (`.desktop` file).

### Why Desktop Autostart is Better

- ✅ **Inherits desktop environment** - Automatically gets DISPLAY, XAUTHORITY, etc.
- ✅ **Standard approach** - What all GUI apps use (Discord, Slack, etc.)
- ✅ **User-friendly** - Shows up in "Startup Applications" settings
- ✅ **Cross-platform** - Works on GNOME, KDE, XFCE, etc.
- ✅ **No permissions issues** - Runs in user's session context

### Implementation Plan

1. **Update installer** (`install.sh`):
   - Replace systemd service creation with desktop file creation
   - Create `~/.config/autostart/quip-daemon.desktop`
   - Remove systemd-specific code

2. **Desktop file format**:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Quip Daemon
   Comment=Global hotkey handler for thought capture
   Exec=/home/user/.local/bin/quip-daemon start
   Hidden=false
   NoDisplay=false
   X-GNOME-Autostart-enabled=true
   ```

3. **Cleanup existing installations**:
   - Provide migration script for users with systemd service
   - Update documentation with new approach

## Files to Modify

1. **`install.sh`**:
   - Remove systemd service creation in `--autostart` section
   - Add desktop file creation
   - Update for macOS LaunchAgent (keep existing)
   - Update fallback autostart entry

2. **Documentation**:
   - Update README installation instructions
   - Add migration guide for existing users

## Testing Requirements

- Test on multiple desktop environments (GNOME, KDE, XFCE)
- Verify hotkeys work after login
- Test uninstall/cleanup process
- Verify no conflicts with existing systemd installations

## Current Workaround

For immediate use:
```bash
# Run daemon manually
uv run quip-daemon start &

# Test hotkey: Win+Space
# Kill when done:
pkill -f quip-daemon
```

## Migration for Existing Users

Users who installed with `--autostart` need to clean up:

```bash
# Stop and disable systemd service
systemctl --user stop quip-daemon
systemctl --user disable quip-daemon
rm ~/.config/systemd/user/quip-daemon.service
systemctl --user daemon-reload

# Then reinstall with fixed version
curl -sSL https://raw.githubusercontent.com/voglster/quip/main/install.sh | bash -s -- --autostart
```

## Expected Outcome

After fix:
- ✅ Daemon starts automatically on login
- ✅ Hotkeys work immediately
- ✅ No GUI permission issues
- ✅ Works across all desktop environments
- ✅ User can manage via standard "Startup Applications"