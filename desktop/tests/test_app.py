"""Tests for core application module."""

from unittest.mock import Mock, patch

import pytest

from core.app import QuipApplication


class TestQuipApplication:
    """Test QuipApplication functionality."""

    @pytest.fixture
    def mock_tkinter(self):
        """Mock tkinter components."""
        with (
            patch("tkinter.Tk") as mock_tk,
            patch("tkinter.Frame") as mock_frame,
        ):
            mock_root = Mock()
            mock_tk.return_value = mock_root
            mock_frame.return_value = Mock()

            yield {"root": mock_root, "frame": mock_frame}

    @pytest.fixture
    def mock_components(self):
        """Mock all component classes."""
        with (
            patch("core.app.WindowManager") as mock_window_manager,
            patch("core.app.NoteManager") as mock_note_manager,
            patch("core.app.VoiceHandler") as mock_voice_handler,
            patch("core.app.QuipTextWidget") as mock_text_widget,
            patch("core.app.CuratorManager") as mock_curator_manager,
            patch("core.app.TooltipManager") as mock_tooltip_manager,
        ):
            yield {
                "window_manager": mock_window_manager,
                "note_manager": mock_note_manager,
                "voice_handler": mock_voice_handler,
                "text_widget": mock_text_widget,
                "curator_manager": mock_curator_manager,
                "tooltip_manager": mock_tooltip_manager,
            }

    def test_text_widget_focus_wiring(self, mock_tkinter, mock_components):
        """Test that text widget is properly wired to window manager for focus."""
        # Create app instance
        with patch("core.app.config"):
            QuipApplication()

            # Check that window manager has text widget reference for focus
            mock_window_manager_instance = mock_components[
                "window_manager"
            ].return_value
            mock_text_widget_instance = mock_components["text_widget"].return_value

            # The text widget should be assigned to window manager
            assert (
                mock_window_manager_instance.text_widget
                == mock_text_widget_instance.text
            )

    def test_run_calls_ensure_focus(self, mock_tkinter, mock_components):
        """Test that run method calls ensure_focus on window manager."""
        with patch("core.app.config"):
            app = QuipApplication()

            mock_window_manager_instance = mock_components[
                "window_manager"
            ].return_value

            # Call run method
            app.run()

            # Should call ensure_focus before starting mainloop
            mock_window_manager_instance.ensure_focus.assert_called_once()
            mock_tkinter["root"].mainloop.assert_called_once()

    def test_initial_empty_state_shown(self, mock_tkinter, mock_components):
        """Test that empty state overlay is shown on app startup."""
        with patch("core.app.config"):
            QuipApplication()

            mock_text_widget_instance = mock_components["text_widget"].return_value

            # Should call show_empty_state to initialize the overlay
            mock_text_widget_instance.show_empty_state.assert_called_once()

    def test_save_and_exit_with_text(self, mock_tkinter, mock_components):
        """Test saving note with actual text content."""
        with patch("core.app.config") as mock_config:
            mock_config.debug_mode = False
            app = QuipApplication()

            # Mock text widget to return some text
            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_text_widget_instance.get_text.return_value = "  some note text  "

            # Mock note manager save
            mock_note_manager_instance = mock_components["note_manager"].return_value
            mock_note_manager_instance.save_note.return_value = True

            # Call save and exit
            app._save_and_exit(None)

            # Should save the original text (stripping is only for checking if there's content)
            mock_note_manager_instance.save_note.assert_called_once_with(
                "  some note text  "
            )
            mock_tkinter["root"].destroy.assert_called_once()

    def test_save_and_exit_with_empty_text(self, mock_tkinter, mock_components):
        """Test that empty text doesn't get saved."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Mock text widget to return empty text
            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_text_widget_instance.get_text.return_value = "   \n  \t  "

            # Mock note manager
            mock_note_manager_instance = mock_components["note_manager"].return_value

            # Call save and exit
            app._save_and_exit(None)

            # Should not save empty text
            mock_note_manager_instance.save_note.assert_not_called()
            mock_tkinter["root"].destroy.assert_called_once()

    def test_improve_note_success(self, mock_tkinter, mock_components):
        """Test successful note improvement."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Mock text widget and curator manager
            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_text_widget_instance.get_text.return_value = "bad grammer text"

            mock_curator_instance = mock_components["curator_manager"].return_value
            mock_curator_instance.improve_note.return_value = (
                True,
                "improved grammar text",
            )

            # Call improve note
            app._improve_note(None)

            # Should set processing state, improve, and update text
            mock_text_widget_instance.set_processing_state.assert_any_call(True)
            mock_text_widget_instance.set_processing_state.assert_any_call(False)
            mock_curator_instance.improve_note.assert_called_once_with(
                "bad grammer text"
            )
            mock_text_widget_instance.set_text.assert_called_with(
                "improved grammar text"
            )

    def test_improve_note_failure(self, mock_tkinter, mock_components):
        """Test note improvement failure handling."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Mock text widget and curator manager
            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_text_widget_instance.get_text.return_value = "original text"

            mock_curator_instance = mock_components["curator_manager"].return_value
            mock_curator_instance.improve_note.return_value = (False, "error message")

            # Call improve note
            app._improve_note(None)

            # Should restore original text on failure
            mock_text_widget_instance.set_text.assert_called_with("original text")

    def test_improve_note_empty_text(self, mock_tkinter, mock_components):
        """Test that empty text doesn't trigger improvement."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Mock text widget to return empty text
            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_text_widget_instance.get_text.return_value = ""

            mock_curator_instance = mock_components["curator_manager"].return_value

            # Call improve note
            app._improve_note(None)

            # Should not attempt improvement
            mock_curator_instance.improve_note.assert_not_called()

    def test_undo_improvement_success(self, mock_tkinter, mock_components):
        """Test successful undo improvement."""
        with patch("core.app.config"):
            app = QuipApplication()

            mock_text_widget_instance = mock_components["text_widget"].return_value
            mock_curator_instance = mock_components["curator_manager"].return_value
            mock_curator_instance.undo_improvement.return_value = (
                True,
                "original text",
            )

            # Call undo improvement
            app._undo_improvement(None)

            # Should set text to undone version
            mock_text_widget_instance.set_text.assert_called_with("original text")

    def test_transcription_complete_with_text(self, mock_tkinter, mock_components):
        """Test handling transcription completion with actual text."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Call transcription complete
            app._on_transcription_complete("transcribed text")

            # Should schedule text insertion
            mock_tkinter["root"].after.assert_called()

    def test_transcription_complete_empty(self, mock_tkinter, mock_components):
        """Test handling transcription completion with empty text."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Call transcription complete with empty text
            app._on_transcription_complete("  ")

            # Should schedule overlay hiding
            mock_tkinter["root"].after.assert_called()

    def test_transcription_error(self, mock_tkinter, mock_components):
        """Test handling transcription error."""
        with patch("core.app.config"):
            app = QuipApplication()

            # Call transcription error
            app._on_transcription_error("error message")

            # Should schedule overlay hiding
            mock_tkinter["root"].after.assert_called()

    def test_open_settings(self, mock_tkinter, mock_components):
        """Test opening settings file."""
        with (
            patch("core.app.config") as mock_config,
            patch("core.app.subprocess.Popen") as mock_popen,
        ):
            mock_config.config_file_path = "/path/to/config.toml"
            mock_config.debug_mode = False

            app = QuipApplication()

            # Call open settings
            app._open_settings(None)

            # Should open file and destroy window
            mock_popen.assert_called_once()
            mock_tkinter["root"].destroy.assert_called_once()
