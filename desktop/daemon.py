"""Quip background daemon for global hotkey handling"""

import sys
import signal
import subprocess
import time
import threading
from pathlib import Path
from pynput import keyboard
from typing import Optional

from config import config
from config_watcher import ConfigWatcher
from updater import UpdateChecker


class QuipDaemon:
    """Background daemon that handles global hotkeys and spawns Quip windows"""

    def __init__(self):
        self.hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self.config_watcher: Optional[ConfigWatcher] = None
        self.running = False

    def spawn_quip(self):
        """Spawn the main Quip application"""
        try:
            # Check for updates in background (async, non-blocking)
            self.check_updates_async()

            # Get the path to the quip executable
            quip_cmd = sys.executable
            quip_module = str(Path(__file__).parent / "main.py")

            if config.debug_mode:
                print(f"Spawning Quip: {quip_cmd} {quip_module}")

            # Launch Quip as separate process
            subprocess.Popen(
                [quip_cmd, quip_module],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL if not config.debug_mode else None,
                start_new_session=True,
            )

        except Exception as e:
            print(f"Error spawning Quip: {e}")

    def check_updates_async(self):
        """Check for updates in background without blocking Quip spawn"""

        def update_check():
            try:
                # Check if auto-update checking is enabled
                if not config.auto_update_check:
                    if config.debug_mode:
                        print("Auto-update checking disabled in config")
                    return

                updater = UpdateChecker()
                # Use the configured check interval
                update_info = updater.check_for_updates(
                    check_interval_hours=config.check_interval_hours
                )
                if update_info:
                    if config.debug_mode:
                        print(f"🎉 Update available: v{update_info['version']}")
                        print("Run 'quip --update' to upgrade")
                    # Could write to a status file or send notification here
                elif config.debug_mode:
                    print("No updates available or rate limited")
            except Exception as e:
                if config.debug_mode:
                    print(f"Update check failed: {e}")
                # Silently fail - don't interrupt user experience
                pass

        # Run in background thread - don't block the hotkey response
        threading.Thread(target=update_check, daemon=True).start()

    def cleanup_llm(self):
        """Placeholder for LLM cleanup functionality"""
        if config.debug_mode:
            print("LLM cleanup requested (not implemented yet)")

    def setup_hotkeys(self):
        """Set up global hotkey listeners"""
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()

        hotkey_map = {
            config.spawn_hotkey: self.spawn_quip,
        }

        # Add cleanup hotkey if configured
        cleanup_hotkey = config.cleanup_hotkey
        if cleanup_hotkey and cleanup_hotkey != config.spawn_hotkey:
            hotkey_map[cleanup_hotkey] = self.cleanup_llm

        if config.debug_mode:
            print(f"Setting up hotkeys: {list(hotkey_map.keys())}")

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Error setting up hotkeys: {e}")
            print("Note: On Wayland, global hotkeys may require additional permissions")

    def on_config_change(self):
        """Handle configuration file changes"""
        if config.debug_mode:
            print("Configuration changed, reloading hotkeys...")

        self.setup_hotkeys()

    def start(self):
        """Start the daemon"""
        print("Starting Quip daemon...")

        if config.debug_mode:
            print(f"Config file: {config.config_file_path}")
            print(f"Debug mode: {config.debug_mode}")
            print(f"Spawn hotkey: {config.spawn_hotkey}")

        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start config watcher
        self.config_watcher = ConfigWatcher(self.on_config_change)
        self.config_watcher.start()

        # Set up initial hotkeys
        self.setup_hotkeys()

        print("Quip daemon running. Press Ctrl+C to stop.")

        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the daemon"""
        print("Stopping Quip daemon...")
        self.running = False

        if self.hotkey_listener:
            self.hotkey_listener.stop()

        if self.config_watcher:
            self.config_watcher.stop()

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.stop()


def main():
    """Main entry point for the daemon"""
    daemon = QuipDaemon()

    try:
        daemon.start()
    except Exception as e:
        print(f"Error running daemon: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
