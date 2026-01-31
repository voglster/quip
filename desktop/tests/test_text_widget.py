"""Tests for enhanced text widget with overlay management."""

from unittest.mock import Mock, patch

import pytest

from ui.fonts import MAIN_TEXT_FONT
from ui.text_widget import QuipTextWidget


class TestQuipTextWidget:
    """Test QuipTextWidget functionality."""

    @pytest.fixture
    def mock_tkinter(self):
        """Mock tkinter components."""
        with (
            patch("tkinter.Text") as mock_text,
            patch("ui.text_widget.OverlayManager") as mock_overlay_manager,
        ):
            mock_text_instance = Mock()
            mock_text.return_value = mock_text_instance

            mock_overlay_manager_instance = Mock()
            mock_overlay_manager.return_value = mock_overlay_manager_instance

            yield {
                "text": mock_text,
                "text_instance": mock_text_instance,
                "overlay_manager": mock_overlay_manager,
                "overlay_manager_instance": mock_overlay_manager_instance,
            }

    @pytest.fixture
    def text_widget(self, mock_tkinter):
        """Create a QuipTextWidget instance for testing."""
        mock_parent = Mock()
        widget = QuipTextWidget(mock_parent)
        return widget, mock_tkinter

    def test_text_widget_initialization(self, text_widget):
        """Test proper initialization of text widget."""
        widget, mocks = text_widget

        # Should create text widget with correct configuration
        mocks["text"].assert_called_once()
        call_args = mocks["text"].call_args

        # Check key configuration parameters
        assert call_args[1]["font"] == MAIN_TEXT_FONT
        assert call_args[1]["wrap"] == "word"
        assert call_args[1]["height"] == 4
        assert call_args[1]["bg"] == "#2b2b2b"
        assert call_args[1]["fg"] == "#ffffff"

        # Should configure text widget
        mocks["text_instance"].configure.assert_called()
        mocks["text_instance"].pack.assert_called_once()
        mocks["text_instance"].focus_set.assert_called_once()

    def test_get_text(self, text_widget):
        """Test getting text content."""
        widget, mocks = text_widget

        mocks["text_instance"].get.return_value = "test content"

        result = widget.get_text()

        assert result == "test content"
        mocks["text_instance"].get.assert_called_once_with("1.0", "end-1c")

    def test_set_text(self, text_widget):
        """Test setting text content."""
        widget, mocks = text_widget

        widget.set_text("new content")

        # Should clear existing text and insert new content
        mocks["text_instance"].delete.assert_called_once_with("1.0", "end")
        mocks["text_instance"].insert.assert_called_once_with("1.0", "new content")

    def test_clear_text(self, text_widget):
        """Test clearing text content."""
        widget, mocks = text_widget

        widget.clear_text()

        # Should delete all text
        mocks["text_instance"].delete.assert_called_once_with("1.0", "end")

    def test_insert_text(self, text_widget):
        """Test inserting text at position."""
        widget, mocks = text_widget

        widget.insert_text("inserted text", "1.5")

        # Should insert at specified position
        mocks["text_instance"].insert.assert_called_with("1.5", "inserted text")

    def test_insert_text_default_position(self, text_widget):
        """Test inserting text at default position."""
        widget, mocks = text_widget

        widget.insert_text("inserted text")

        # Should insert at "insert" position by default
        mocks["text_instance"].insert.assert_called_with("insert", "inserted text")

    def test_insert_text_smart_spacing_beginning(self, text_widget):
        """Test smart spacing when inserting at text beginning."""
        widget, mocks = text_widget

        mocks["text_instance"].index.return_value = "1.0"

        widget.insert_text_smart_spacing("  new text  ")

        # Should not add space at beginning, but should strip whitespace
        mocks["text_instance"].insert.assert_called_with("insert", "new text")

    def test_insert_text_smart_spacing_after_space(self, text_widget):
        """Test smart spacing when inserting after existing space."""
        widget, mocks = text_widget

        mocks["text_instance"].index.return_value = "1.5"
        mocks["text_instance"].get.return_value = " "

        widget.insert_text_smart_spacing("new text")

        # Should not add extra space after existing space
        mocks["text_instance"].insert.assert_called_with("insert", "new text")

    def test_insert_text_smart_spacing_after_letter(self, text_widget):
        """Test smart spacing when inserting after letter."""
        widget, mocks = text_widget

        mocks["text_instance"].index.return_value = "1.5"
        mocks["text_instance"].get.return_value = "a"

        widget.insert_text_smart_spacing("new text")

        # Should add space before text when previous character is a letter
        mocks["text_instance"].insert.assert_called_with("insert", " new text")

    def test_bind_key(self, text_widget):
        """Test key binding functionality."""
        widget, mocks = text_widget

        callback = Mock()
        widget.bind_key("<Control-s>", callback)

        # Should bind key to text widget
        mocks["text_instance"].bind.assert_any_call("<Control-s>", callback)

    def test_set_processing_state_enabled(self, text_widget):
        """Test enabling processing state."""
        widget, mocks = text_widget

        mocks["text_instance"].cget.side_effect = (
            lambda x: "#2b2b2b" if x == "bg" else "#ffffff"
        )

        widget.set_processing_state(True, "Processing...")

        # Should disable widget and show processing message
        mocks["text_instance"].delete.assert_called_with("1.0", "end")
        mocks["text_instance"].insert.assert_called_with("1.0", "Processing...")
        mocks["text_instance"].configure.assert_called()
        mocks["text_instance"].config.assert_called_with(state="disabled")

    def test_set_processing_state_disabled(self, text_widget):
        """Test disabling processing state."""
        widget, mocks = text_widget

        # First enable processing state to set original values
        mocks["text_instance"].cget.side_effect = (
            lambda x: "#2b2b2b" if x == "bg" else "#ffffff"
        )
        widget.set_processing_state(True)

        # Then disable it
        widget.set_processing_state(False)

        # Should re-enable widget and restore original styling
        mocks["text_instance"].config.assert_any_call(state="normal")

    def test_focus_set(self, text_widget):
        """Test setting focus to text widget."""
        widget, mocks = text_widget

        widget.focus_set()

        # Should call focus_set on text widget (called during init and explicit call)
        assert mocks["text_instance"].focus_set.call_count >= 2

    def test_index(self, text_widget):
        """Test getting index for position."""
        widget, mocks = text_widget

        mocks["text_instance"].index.return_value = "1.5"

        result = widget.index("insert")

        assert result == "1.5"
        mocks["text_instance"].index.assert_called_with("insert")

    def test_get_char_at(self, text_widget):
        """Test getting character at specific position."""
        widget, mocks = text_widget

        mocks["text_instance"].get.return_value = "a"

        result = widget.get_char_at("1.5")

        assert result == "a"
        mocks["text_instance"].get.assert_called_with("1.5", "1.5+1c")

    def test_text_change_event_triggers_overlay_update(self, text_widget):
        """Test that text changes update overlay state."""
        widget, mocks = text_widget

        # Mock get_text to return content with text
        mocks["text_instance"].get.return_value = "some content"

        # Trigger text change event
        widget._on_text_change()

        # Should update overlay manager with has_text=True
        mocks["overlay_manager_instance"].update_for_text_content.assert_called_with(
            True
        )

    def test_text_change_event_empty_content(self, text_widget):
        """Test that empty text changes update overlay state correctly."""
        widget, mocks = text_widget

        # Mock get_text to return empty content
        mocks["text_instance"].get.return_value = "   \n  "

        # Trigger text change event
        widget._on_text_change()

        # Should update overlay manager with has_text=False for whitespace-only content
        mocks["overlay_manager_instance"].update_for_text_content.assert_called_with(
            False
        )

    def test_text_change_callback(self, text_widget):
        """Test that text change callback is called when set."""
        widget, mocks = text_widget

        callback = Mock()
        widget.on_text_change = callback

        mocks["text_instance"].get.return_value = "test content"

        # Trigger text change event
        widget._on_text_change()

        # Should call the callback with the text content
        callback.assert_called_once_with("test content")

    def test_overlay_management_methods(self, text_widget):
        """Test overlay management method delegation."""
        widget, mocks = text_widget
        overlay_manager = mocks["overlay_manager_instance"]

        # Test each overlay management method
        widget.show_empty_state()
        overlay_manager.show_empty_state.assert_called_once()

        widget.show_recording_overlay()
        overlay_manager.show_recording.assert_called_once()

        widget.show_recording_tail_overlay()
        overlay_manager.show_recording_tail.assert_called_once()

        widget.show_processing_overlay()
        overlay_manager.show_processing.assert_called_once()

        widget.hide_all_overlays()
        overlay_manager.hide_all_overlays.assert_called_once()

    def test_event_binding_during_init(self, text_widget):
        """Test that events are properly bound during initialization."""
        widget, mocks = text_widget

        # Should bind text change events
        mocks["text_instance"].bind.assert_any_call(
            "<KeyRelease>", widget._on_text_change
        )
        mocks["text_instance"].bind.assert_any_call(
            "<Button-1>", widget._on_text_change
        )
