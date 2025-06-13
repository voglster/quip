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
