"""Tests for overlays module."""

from unittest.mock import Mock, patch

import pytest

from ui.overlays import OverlayManager, TooltipManager


class TestOverlayManager:
    """Test OverlayManager functionality."""

    @pytest.fixture
    def overlay_manager(self, mock_tkinter):
        """Create an OverlayManager instance for testing."""
        mock_frame = Mock()
        with (
            patch("tkinter.Label"),
            patch("tkinter.Frame") as mock_frame_class,
        ):
            mock_frame_class.return_value = Mock()
            return OverlayManager(mock_frame)

    def test_overlay_manager_creation(self, overlay_manager):
        """Test that OverlayManager creates all overlays."""
        assert overlay_manager.empty_state_overlay is not None
        assert overlay_manager.recording_overlay is not None
        assert overlay_manager.processing_overlay is not None
        assert overlay_manager.current_overlay is None

    def test_show_empty_state(self, overlay_manager):
        """Test showing empty state overlay."""
        overlay_manager.show_empty_state()

        assert overlay_manager.current_overlay == overlay_manager.empty_state_overlay
        overlay_manager.empty_state_overlay.place.assert_called_with(
            relx=0.5, rely=0.4, anchor="center"
        )

    def test_show_recording(self, overlay_manager):
        """Test showing recording overlay."""
        overlay_manager.show_recording()

        assert overlay_manager.current_overlay == overlay_manager.recording_overlay
        overlay_manager.recording_overlay.place.assert_called_with(
            x=10, y=10, relwidth=0.97, relheight=0.85
        )

    def test_show_recording_tail(self, overlay_manager):
        """Test showing recording tail overlay."""
        overlay_manager.show_recording_tail()

        assert overlay_manager.current_overlay == overlay_manager.recording_overlay
        overlay_manager.recording_label.config.assert_called_with(
            text="🎤 Finishing recording...", fg="#ffaa99"
        )

    def test_show_processing(self, overlay_manager):
        """Test showing processing overlay."""
        overlay_manager.show_processing()

        assert overlay_manager.current_overlay == overlay_manager.processing_overlay
        overlay_manager.processing_overlay.place.assert_called_with(
            x=10, y=10, relwidth=0.97, relheight=0.85
        )

    def test_hide_all_overlays(self, overlay_manager):
        """Test hiding all overlays."""
        overlay_manager.current_overlay = overlay_manager.empty_state_overlay

        overlay_manager.hide_all_overlays()

        assert overlay_manager.current_overlay is None
        overlay_manager.empty_state_overlay.place_forget.assert_called()
        overlay_manager.recording_overlay.place_forget.assert_called()
        overlay_manager.processing_overlay.place_forget.assert_called()

    def test_update_for_text_content_with_text(self, overlay_manager):
        """Test updating overlays when text is present."""
        overlay_manager.update_for_text_content(has_text=True)

        # Should hide all overlays when text is present
        overlay_manager.empty_state_overlay.place_forget.assert_called()
        overlay_manager.recording_overlay.place_forget.assert_called()
        overlay_manager.processing_overlay.place_forget.assert_called()

    def test_update_for_text_content_without_text(self, overlay_manager):
        """Test updating overlays when no text is present."""
        overlay_manager.current_overlay = None

        overlay_manager.update_for_text_content(has_text=False)

        # Should show empty state when no text and not recording/processing
        assert overlay_manager.current_overlay == overlay_manager.empty_state_overlay


class TestTooltipManager:
    """Test TooltipManager functionality."""

    @pytest.fixture
    def tooltip_manager(self, mock_tkinter, mock_config):
        """Create a TooltipManager instance for testing."""
        mock_frame = Mock()
        mock_root = mock_tkinter["root"]

        with (
            patch("tkinter.Frame") as mock_frame_class,
            patch("tkinter.Label"),
        ):
            mock_frame_class.return_value = Mock()
            tooltip_manager = TooltipManager(mock_frame, mock_root)
            return tooltip_manager

    def test_tooltip_manager_creation(self, tooltip_manager):
        """Test that TooltipManager creates info icon."""
        assert tooltip_manager.info_icon is not None
        assert tooltip_manager.tooltip_window is None
        assert tooltip_manager.tooltip_label is None

    def test_show_tooltip(self, tooltip_manager, mock_config):
        """Test showing tooltip."""
        # Mock info icon position
        tooltip_manager.info_icon.winfo_rootx.return_value = 100
        tooltip_manager.info_icon.winfo_rooty.return_value = 200

        with (
            patch("tkinter.Toplevel") as mock_toplevel,
            patch("tkinter.Label"),
        ):
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            tooltip_manager.show_tooltip()

            # Should create tooltip window
            mock_toplevel.assert_called_once_with(tooltip_manager.root)
            mock_window.wm_overrideredirect.assert_called_with(True)
            mock_window.wm_geometry.assert_called_with("+120+50")  # x+20, y-150

    def test_show_tooltip_already_shown(self, tooltip_manager):
        """Test showing tooltip when already shown."""
        tooltip_manager.tooltip_window = Mock()

        with patch("tkinter.Toplevel") as mock_toplevel:
            tooltip_manager.show_tooltip()

            # Should not create new tooltip
            mock_toplevel.assert_not_called()

    def test_hide_tooltip(self, tooltip_manager):
        """Test hiding tooltip."""
        mock_window = Mock()
        tooltip_manager.tooltip_window = mock_window
        tooltip_manager.tooltip_label = Mock()

        tooltip_manager.hide_tooltip()

        mock_window.destroy.assert_called_once()
        assert tooltip_manager.tooltip_window is None
        assert tooltip_manager.tooltip_label is None

    def test_hide_tooltip_not_shown(self, tooltip_manager):
        """Test hiding tooltip when not shown."""
        tooltip_manager.tooltip_window = None

        # Should not raise exception
        tooltip_manager.hide_tooltip()

    def test_generate_tooltip_text_llm_enabled(self, tooltip_manager, mock_config):
        """Test generating tooltip text with LLM enabled."""
        mock_config.llm_enabled = True

        with patch("config.config", mock_config):
            text = tooltip_manager._generate_tooltip_text()

        assert "Hotkeys:" in text
        assert "Ctrl+I — Improve with AI" in text
        assert "Ctrl+L — Curator feedback" in text
        assert "✅ AI enabled" in text

    def test_generate_tooltip_text_llm_disabled(self, tooltip_manager, mock_config):
        """Test generating tooltip text with LLM disabled."""
        mock_config.llm_enabled = False

        with patch("config.config", mock_config):
            text = tooltip_manager._generate_tooltip_text()

        assert "Hotkeys:" in text
        assert "Ctrl+I — Improve with AI" not in text
        assert "Ctrl+L — Curator feedback" not in text
        assert "⚠️ AI disabled" in text
