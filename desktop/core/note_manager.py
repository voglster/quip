"""Note saving and file management functionality."""

from pathlib import Path

from config import config


class NoteManager:
    """Handles note saving and file management operations."""

    NOTE_DELIMITER = "---"

    def __init__(self):
        self.save_path = Path(config.save_path)

    def save_note(self, content: str) -> bool:
        """Save note content to configured file path.

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
            # Ensure directory exists
            self.save_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to file with proper delimiter
            with open(self.save_path, "a", encoding="utf-8") as f:
                if self._file_has_content():
                    f.write(f"\n\n{self.NOTE_DELIMITER}\n\n")
                f.write(content)

            if config.debug_mode:
                print(f"DEBUG: Note saved to {self.save_path}")

            return True

        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Failed to save note: {e}")
            return False

    def _file_has_content(self) -> bool:
        """Check if the notes file exists and has content."""
        try:
            return self.save_path.exists() and self.save_path.stat().st_size > 0
        except Exception:
            return False

    def get_save_path(self) -> Path:
        """Get the configured save path."""
        return self.save_path

    def set_save_path(self, new_path: str | Path) -> None:
        """Update the save path."""
        self.save_path = Path(new_path)

    def validate_save_path(self) -> bool:
        """Validate that the save path is writable.

        Returns:
            True if path is valid and writable, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.save_path.parent.mkdir(parents=True, exist_ok=True)

            # Test write access
            test_file = self.save_path.parent / ".quip_write_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()

            return True

        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Save path validation failed: {e}")
            return False
