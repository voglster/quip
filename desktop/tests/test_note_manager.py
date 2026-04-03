"""Tests for note_manager module."""

from unittest.mock import patch, MagicMock

import pytest

from core.note_manager import NoteManager


class TestNoteManager:
    """Test NoteManager functionality."""

    @pytest.fixture
    def note_manager(self, temp_dir, mock_config):
        """Create a NoteManager instance for testing."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = False
        with patch("core.note_manager.config", mock_config):
            return NoteManager()

    def test_save_note_creates_file(self, note_manager, temp_dir):
        """Test that saving a note creates a file in the inbox directory."""
        result = note_manager.save_note("This is a test note")

        assert result is True
        inbox = temp_dir / "Inbox"
        assert inbox.exists()
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        assert files[0].read_text(encoding="utf-8") == "This is a test note"

    def test_save_note_creates_individual_files(self, note_manager, temp_dir):
        """Test that each save creates a separate file."""
        note_manager.save_note("First note")
        note_manager.save_note("Second note")

        inbox = temp_dir / "Inbox"
        files = sorted(inbox.glob("*.md"))
        assert len(files) == 2

        contents = {f.read_text(encoding="utf-8") for f in files}
        assert contents == {"First note", "Second note"}

    def test_save_note_uses_timestamp_filename(self, note_manager, temp_dir):
        """Test that saved files use timestamp naming."""
        note_manager.save_note("Test note")

        inbox = temp_dir / "Inbox"
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        # Filename should match YYYY-MM-DD-HHMMSS pattern
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2}-\d{6}-\d+\.md", files[0].name)

    def test_save_empty_note_returns_false(self, note_manager):
        """Test that saving empty content returns False."""
        result = note_manager.save_note("")
        assert result is False

        result = note_manager.save_note("   ")
        assert result is False

    def test_save_note_creates_directory(self, temp_dir, mock_config):
        """Test that saving a note creates the inbox directory."""
        nested_path = temp_dir / "nested" / "path" / "Inbox"
        mock_config.save_path = str(nested_path)
        mock_config.llm_enabled = False

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        result = note_manager.save_note("Test note")

        assert result is True
        assert nested_path.exists()

    def test_validate_save_path_valid(self, note_manager, temp_dir):
        """Test validating a writable path."""
        result = note_manager.validate_save_path()
        assert result is True

    def test_validate_save_path_invalid(self, mock_config):
        """Test validating an invalid path."""
        mock_config.save_path = "/root/cannot_write_here"

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
        new_path = temp_dir / "new_inbox"
        note_manager.set_save_path(new_path)

        assert note_manager.get_save_path() == new_path

    def test_save_note_handles_encoding(self, note_manager, temp_dir):
        """Test that save_note handles Unicode content properly."""
        unicode_content = "Test with emoji 📝 and special chars: ñáéíóú"

        result = note_manager.save_note(unicode_content)

        assert result is True
        inbox = temp_dir / "Inbox"
        files = list(inbox.glob("*.md"))
        content = files[0].read_text(encoding="utf-8")
        assert content == unicode_content

    def test_get_last_saved_path(self, note_manager, temp_dir):
        """Test that last saved path is tracked."""
        assert note_manager.get_last_saved_path() is None

        note_manager.save_note("Test note")

        last_path = note_manager.get_last_saved_path()
        assert last_path is not None
        assert last_path.exists()

    def test_background_rename_not_triggered_without_llm(self, temp_dir, mock_config):
        """Test that background rename doesn't run when LLM is disabled."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = False

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

            with patch("threading.Thread") as mock_thread:
                note_manager.save_note("Test note")
                mock_thread.assert_not_called()

    def test_background_rename_triggered_with_llm(self, temp_dir, mock_config):
        """Test that background rename is triggered when LLM is enabled."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = True

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

            with patch("threading.Thread") as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance

                note_manager.save_note("Test note")

                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()

    def test_rename_with_llm(self, temp_dir, mock_config):
        """Test the LLM rename logic."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = True
        mock_config.debug_mode = False

        inbox = temp_dir / "Inbox"
        inbox.mkdir(parents=True)
        file_path = inbox / "2026-03-31-143022.md"
        file_path.write_text("My test note content", encoding="utf-8")

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        mock_llm = MagicMock()
        mock_llm.generate_filename.return_value = "My Test Note"

        with patch.dict("sys.modules", {"llm": MagicMock(llm_client=mock_llm)}):
            note_manager._rename_with_llm(file_path, "My test note content")

        expected_path = inbox / "My Test Note.md"
        assert expected_path.exists()
        assert not file_path.exists()

    def test_rename_with_llm_handles_collision(self, temp_dir, mock_config):
        """Test that rename handles filename collisions."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = True
        mock_config.debug_mode = False

        inbox = temp_dir / "Inbox"
        inbox.mkdir(parents=True)

        # Create existing file with the name LLM will generate
        (inbox / "My Note.md").write_text("existing", encoding="utf-8")

        file_path = inbox / "2026-03-31-143022.md"
        file_path.write_text("New content", encoding="utf-8")

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        mock_llm = MagicMock()
        mock_llm.generate_filename.return_value = "My Note"

        with patch.dict("sys.modules", {"llm": MagicMock(llm_client=mock_llm)}):
            note_manager._rename_with_llm(file_path, "New content")

        assert (inbox / "My Note 2.md").exists()
        assert not file_path.exists()

    def test_rename_with_llm_empty_title_keeps_original(self, temp_dir, mock_config):
        """Test that empty LLM response keeps the timestamp filename."""
        mock_config.save_path = str(temp_dir / "Inbox")
        mock_config.llm_enabled = True
        mock_config.debug_mode = False

        inbox = temp_dir / "Inbox"
        inbox.mkdir(parents=True)
        file_path = inbox / "2026-03-31-143022.md"
        file_path.write_text("content", encoding="utf-8")

        with patch("core.note_manager.config", mock_config):
            note_manager = NoteManager()

        mock_llm = MagicMock()
        mock_llm.generate_filename.return_value = ""

        with patch.dict("sys.modules", {"llm": MagicMock(llm_client=mock_llm)}):
            note_manager._rename_with_llm(file_path, "content")

        # Original file should still be there
        assert file_path.exists()
