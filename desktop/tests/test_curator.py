"""Tests for curator module."""

from unittest.mock import Mock, patch

import pytest

from curator.curator import CuratorManager


class TestCuratorManager:
    """Test CuratorManager functionality."""

    @pytest.fixture
    def curator_manager(self, mock_tkinter, mock_config):
        """Create a CuratorManager instance for testing."""
        mock_frame = Mock()
        mock_window_manager = Mock()

        with (
            patch("tkinter.Frame") as mock_frame_class,
            patch("tkinter.Text"),
            patch("curator.curator.config", mock_config),
        ):
            mock_frame_class.return_value = Mock()
            return CuratorManager(mock_frame, mock_window_manager)

    def test_curator_manager_creation(self, curator_manager):
        """Test CuratorManager initialization."""
        assert curator_manager.curator_mode is False
        assert curator_manager.current_curator_feedback is None
        assert curator_manager.text_before_improvement is None
        assert curator_manager.curator_frame is not None
        assert curator_manager.curator_text is not None

    def test_is_curator_mode_active(self, curator_manager):
        """Test checking if curator mode is active."""
        assert curator_manager.is_curator_mode_active() is False

        curator_manager.curator_mode = True
        assert curator_manager.is_curator_mode_active() is True

    def test_toggle_curator_mode_llm_disabled(self, curator_manager, mock_config):
        """Test toggling curator mode when LLM is disabled."""
        mock_config.llm_enabled = False

        with patch("curator.curator.config", mock_config):
            result = curator_manager.toggle_curator_mode("Test note")

        assert result is False
        assert curator_manager.curator_mode is False

    def test_toggle_curator_mode_empty_text(self, curator_manager, mock_config):
        """Test toggling curator mode with empty text."""
        mock_config.llm_enabled = True

        result = curator_manager.toggle_curator_mode("")

        assert result is False
        assert curator_manager.curator_mode is False

    def test_toggle_curator_mode_success(self, curator_manager, mock_config):
        """Test successfully toggling curator mode."""
        mock_config.llm_enabled = True

        with (
            patch("curator.curator.config", mock_config),
            patch.object(curator_manager, "show_curator_feedback") as mock_show,
        ):
            result = curator_manager.toggle_curator_mode("Test note")

            assert result is True
            mock_show.assert_called_once_with("Test note")

    @patch("llm.llm_client")
    def test_show_curator_feedback_success(
        self, mock_llm_client, curator_manager, mock_config
    ):
        """Test showing curator feedback successfully."""
        mock_config.llm_enabled = True
        mock_llm_client._make_request.return_value = {
            "choices": [{"message": {"content": "Test feedback"}}]
        }

        curator_manager.show_curator_feedback("Test note")

        assert curator_manager.curator_mode is True
        assert curator_manager.current_curator_feedback == "Test feedback"
        curator_manager.window_manager.expand_window.assert_called_once()

    @patch("llm.llm_client")
    def test_show_curator_feedback_error(
        self, mock_llm_client, curator_manager, mock_config
    ):
        """Test showing curator feedback with LLM error."""
        from llm import LLMError

        mock_config.llm_enabled = True
        mock_llm_client._make_request.side_effect = LLMError("API Error")

        # Should not raise exception
        curator_manager.show_curator_feedback("Test note")

        # Error should be displayed in curator text
        curator_manager.curator_text.insert.assert_called()

    def test_clear_curator_mode(self, curator_manager):
        """Test clearing curator mode."""
        curator_manager.curator_mode = True
        curator_manager.current_curator_feedback = "Some feedback"

        curator_manager.clear_curator_mode()

        assert curator_manager.curator_mode is False
        assert curator_manager.current_curator_feedback is None
        curator_manager.curator_frame.pack_forget.assert_called_once()
        curator_manager.window_manager.restore_original_height.assert_called_once()

    def test_improve_note_llm_disabled(self, curator_manager, mock_config):
        """Test improving note when LLM is disabled."""
        mock_config.llm_enabled = False

        with patch("curator.curator.config", mock_config):
            success, result = curator_manager.improve_note("Test note")

        assert success is False
        assert result == "LLM not enabled"

    def test_improve_note_empty_text(self, curator_manager, mock_config):
        """Test improving note with empty text."""
        mock_config.llm_enabled = True

        with patch("curator.curator.config", mock_config):
            success, result = curator_manager.improve_note("")

        assert success is False
        assert result == "No text to improve"

    @patch("llm.llm_client")
    def test_improve_note_success(self, mock_llm_client, curator_manager, mock_config):
        """Test successfully improving a note."""
        mock_config.llm_enabled = True
        mock_llm_client.improve_note.return_value = "Improved note text"

        with patch("curator.curator.config", mock_config):
            success, result = curator_manager.improve_note("Original note")

        assert success is True
        assert result == "Improved note text"
        assert curator_manager.text_before_improvement == "Original note"

    @patch("llm.llm_client")
    def test_improve_note_error(self, mock_llm_client, curator_manager, mock_config):
        """Test improving note with error."""
        mock_config.llm_enabled = True
        mock_llm_client.improve_note.side_effect = Exception("API Error")

        with patch("curator.curator.config", mock_config):
            success, result = curator_manager.improve_note("Test note")

        assert success is False
        assert "API Error" in result
        assert curator_manager.text_before_improvement is None

    def test_undo_improvement_no_previous_text(self, curator_manager):
        """Test undoing improvement when no previous text exists."""
        curator_manager.text_before_improvement = None

        success, result = curator_manager.undo_improvement()

        assert success is False
        assert result == "No previous text to restore"

    def test_undo_improvement_success(self, curator_manager):
        """Test successfully undoing improvement."""
        original_text = "Original text"
        curator_manager.text_before_improvement = original_text

        success, result = curator_manager.undo_improvement()

        assert success is True
        assert result == original_text
        assert curator_manager.text_before_improvement is None

    @patch("llm.llm_client")
    def test_get_curator_feedback(self, mock_llm_client, curator_manager, mock_config):
        """Test getting curator feedback from LLM."""
        mock_config.llm_enabled = True
        mock_llm_client._make_request.return_value = {
            "choices": [{"message": {"content": "What is the next action?"}}]
        }

        feedback = curator_manager._get_curator_feedback("Test note")

        assert feedback == "What is the next action?"
        mock_llm_client._make_request.assert_called_once()

    @patch("llm.llm_client")
    def test_get_curator_feedback_no_choices(
        self, mock_llm_client, curator_manager, mock_config
    ):
        """Test getting curator feedback with no response choices."""
        from llm import LLMError

        mock_config.llm_enabled = True
        mock_llm_client._make_request.return_value = {"choices": []}

        with pytest.raises(LLMError):
            curator_manager._get_curator_feedback("Test note")

    def test_improve_note_with_curator_context(self, curator_manager, mock_config):
        """Test improving note with curator context."""
        mock_config.llm_enabled = True
        curator_manager.curator_mode = True
        curator_manager.current_curator_feedback = "What is the deadline?"

        with (
            patch("curator.curator.config", mock_config),
            patch("llm.llm_client") as mock_llm_client,
        ):
            mock_llm_client.improve_note.return_value = "Improved text"

            success, result = curator_manager.improve_note("Test note")

            # Should pass curator context to LLM
            mock_llm_client.improve_note.assert_called_once_with(
                "Test note", "What is the deadline?"
            )
            assert success is True
