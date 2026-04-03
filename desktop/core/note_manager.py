"""Note saving and file management functionality."""

import threading
from datetime import datetime
from pathlib import Path

from config import config


class NoteManager:
    """Handles note saving and file management operations.

    Saves each note as a separate file in the configured inbox directory.
    Files are initially saved with a timestamp name, then renamed in the
    background using an LLM-generated descriptive title.
    """

    def __init__(self):
        self.save_dir = Path(config.save_path)
        self._last_saved_path: Path | None = None

    def save_note(self, content: str) -> bool:
        """Save note content as an individual file in the inbox directory.

        Saves immediately with a timestamp filename, then kicks off a
        background LLM call to rename the file with a descriptive title.

        Args:
            content: Note text content to save

        Returns:
            True if save was successful, False otherwise
        """
        content = content.strip()
        if not content:
            if config.debug_mode:
                print("DEBUG: No content to save")
            return False

        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)

            # Save with timestamp filename
            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")
            file_path = self.save_dir / f"{timestamp}.md"
            file_path.write_text(content, encoding="utf-8")
            self._last_saved_path = file_path

            if config.debug_mode:
                print(f"DEBUG: Note saved to {file_path}")

            # Background rename via LLM
            if config.llm_enabled:
                thread = threading.Thread(
                    target=self._rename_with_llm,
                    args=(file_path, content),
                    daemon=True,
                )
                thread.start()

            return True

        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Failed to save note: {e}")
            return False

    def _rename_with_llm(self, file_path: Path, content: str) -> None:
        """Rename a saved note file using an LLM-generated title."""
        try:
            from llm import llm_client

            title = llm_client.generate_filename(content)
            if not title:
                return

            new_path = self.save_dir / f"{title}.md"

            # Handle collisions
            if new_path.exists() and new_path != file_path:
                counter = 2
                while new_path.exists():
                    new_path = self.save_dir / f"{title} {counter}.md"
                    counter += 1

            file_path.rename(new_path)
            self._last_saved_path = new_path

            if config.debug_mode:
                print(f"DEBUG: Note renamed to {new_path}")

        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Failed to rename note: {e}")

    def get_save_path(self) -> Path:
        """Get the configured save directory."""
        return self.save_dir

    def get_last_saved_path(self) -> Path | None:
        """Get the path of the most recently saved note."""
        return self._last_saved_path

    def set_save_path(self, new_path: str | Path) -> None:
        """Update the save directory."""
        self.save_dir = Path(new_path)

    def validate_save_path(self) -> bool:
        """Validate that the save directory is writable.

        Returns:
            True if path is valid and writable, False otherwise
        """
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)

            # Test write access
            test_file = self.save_dir / ".quip_write_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()

            return True

        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Save path validation failed: {e}")
            return False
