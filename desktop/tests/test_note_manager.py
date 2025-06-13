"""Tests for note_manager module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.note_manager import NoteManager


class TestNoteManager:
    """Test NoteManager functionality."""

    @pytest.fixture
    def note_manager(self, temp_dir, mock_config):
        """Create a NoteManager instance for testing."""
        mock_config.save_path = str(temp_dir / "test_notes.md")
        with patch("core.note_manager.config", mock_config):
            return NoteManager()

    def test_save_note_creates_file(self, note_manager, temp_dir):
        """Test that saving a note creates the file."""
        note_content = "This is a test note"

        result = note_manager.save_note(note_content)

        assert result is True
        save_path = Path(note_manager.save_path)
        assert save_path.exists()
        assert save_path.read_text(encoding="utf-8") == note_content

    def test_save_note_appends_with_delimiter(self, note_manager, temp_dir):
        """Test that saving multiple notes appends with delimiter."""
        first_note = "First note"
        second_note = "Second note"

        # Save first note
        note_manager.save_note(first_note)

        # Save second note
        note_manager.save_note(second_note)

        save_path = Path(note_manager.save_path)
        content = save_path.read_text(encoding="utf-8")

        expected = f"{first_note}\n\n{NoteManager.NOTE_DELIMITER}\n\n{second_note}"
        assert content == expected

    def test_save_empty_note_returns_false(self, note_manager):
        """Test that saving empty content returns False."""
        result = note_manager.save_note("")
        assert result is False

        result = note_manager.save_note("   ")
        assert result is False

    def test_save_note_creates_directory(self, temp_dir, mock_config):
        """Test that saving a note creates parent directories."""
        nested_path = temp_dir / "nested" / "path" / "notes.md"
        mock_config.save_path = str(nested_path)

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        result = note_manager.save_note("Test note")

        assert result is True
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_validate_save_path_valid(self, note_manager, temp_dir):
        """Test validating a writable path."""
        result = note_manager.validate_save_path()
        assert result is True

    def test_validate_save_path_invalid(self, mock_config):
        """Test validating an invalid path."""
        mock_config.save_path = "/root/cannot_write_here.md"

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        result = note_manager.validate_save_path()
        assert result is False

    def test_get_save_path(self, note_manager, mock_config):
        """Test getting the configured save path."""
        result = note_manager.get_save_path()
        assert str(result) == mock_config.save_path

    def test_set_save_path(self, note_manager, temp_dir):
        """Test updating the save path."""
        new_path = temp_dir / "new_notes.md"
        note_manager.set_save_path(new_path)

        assert note_manager.get_save_path() == new_path

    def test_file_has_content_empty_file(self, note_manager, temp_dir):
        """Test _file_has_content with empty file."""
        # Create empty file
        Path(note_manager.save_path).touch()

        assert not note_manager._file_has_content()

    def test_file_has_content_with_content(self, note_manager, temp_dir):
        """Test _file_has_content with file that has content."""
        # Save a note to create file with content
        note_manager.save_note("Some content")

        assert note_manager._file_has_content()

    def test_file_has_content_nonexistent_file(self, note_manager):
        """Test _file_has_content with nonexistent file."""
        assert not note_manager._file_has_content()

    def test_save_note_handles_encoding(self, note_manager):
        """Test that save_note handles Unicode content properly."""
        unicode_content = "Test with emoji 📝 and special chars: ñáéíóú"

        result = note_manager.save_note(unicode_content)

        assert result is True
        save_path = Path(note_manager.save_path)
        content = save_path.read_text(encoding="utf-8")
        assert content == unicode_content
