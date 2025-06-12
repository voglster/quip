"""File watcher for Quip configuration changes"""

import time
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import config


class ConfigFileHandler(FileSystemEventHandler):
    """Handles configuration file change events"""

    def __init__(self, on_config_change: Callable[[], None]):
        super().__init__()
        self.on_config_change = on_config_change
        self.config_file = config.config_file_path
        self.last_modified = 0

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return

        # Check if it's our config file
        if Path(event.src_path) == self.config_file:
            # Debounce rapid file changes (some editors write multiple times)
            current_time = time.time()
            if current_time - self.last_modified > 0.5:  # 500ms debounce
                self.last_modified = current_time

                if config.debug_mode:
                    print(f"Config file changed: {event.src_path}")

                # Reload config and notify
                config.reload()
                self.on_config_change()


class ConfigWatcher:
    """Watches configuration file for changes and triggers callbacks"""

    def __init__(self, on_config_change: Callable[[], None]):
        self.observer: Optional[Observer] = None
        self.handler = ConfigFileHandler(on_config_change)
        self.watch_dir = config.config_file_path.parent

    def start(self):
        """Start watching the config file"""
        if self.observer is not None:
            return  # Already running

        # Ensure config directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)

        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.watch_dir), recursive=False)
        self.observer.start()

        if config.debug_mode:
            print(f"Started watching config directory: {self.watch_dir}")

    def stop(self):
        """Stop watching the config file"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None

            if config.debug_mode:
                print("Stopped config watcher")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
