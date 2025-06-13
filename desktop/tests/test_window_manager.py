"""Tests for window_manager module."""

import subprocess
from unittest.mock import patch

import pytest

from ui.window_manager import MonitorInfo, WindowManager


class TestMonitorInfo:
    """Test MonitorInfo functionality."""

    def test_monitor_info_creation(self):
        """Test creating a MonitorInfo instance."""
        monitor = MonitorInfo("DP-1", 100, 200, 1920, 1080)

        assert monitor.name == "DP-1"
        assert monitor.x == 100
        assert monitor.y == 200
        assert monitor.width == 1920
        assert monitor.height == 1080

    def test_contains_point_inside(self):
        """Test contains_point with point inside monitor."""
        monitor = MonitorInfo("DP-1", 100, 200, 1920, 1080)

        assert monitor.contains_point(500, 500)  # Inside
        assert monitor.contains_point(100, 200)  # Top-left corner
        assert monitor.contains_point(2019, 1279)  # Bottom-right corner (exclusive)

    def test_contains_point_outside(self):
        """Test contains_point with point outside monitor."""
        monitor = MonitorInfo("DP-1", 100, 200, 1920, 1080)

        assert not monitor.contains_point(50, 500)  # Left of monitor
        assert not monitor.contains_point(500, 150)  # Above monitor
        assert not monitor.contains_point(2020, 500)  # Right of monitor
        assert not monitor.contains_point(500, 1280)  # Below monitor


class TestWindowManager:
    """Test WindowManager functionality."""

    @pytest.fixture
    def window_manager(self, mock_tkinter, mock_config):
        """Create a WindowManager instance for testing."""
        with patch("ui.window_manager.config", mock_config):
            return WindowManager(mock_tkinter["root"])

    def test_setup_window_properties(self, window_manager):
        """Test window property setup."""
        window_manager.setup_window_properties()

        # Should call withdraw to hide initially
        window_manager.root.withdraw.assert_called_once()

        # Should set topmost
        window_manager.root.attributes.assert_called_with("-topmost", True)

    def test_setup_window_properties_handles_errors(self, window_manager):
        """Test window property setup handles TclError gracefully."""
        import tkinter as tk

        # Mock wm_attributes to raise TclError
        window_manager.root.wm_attributes.side_effect = tk.TclError("Not supported")

        # Should not raise exception
        window_manager.setup_window_properties()

    def test_parse_xrandr_output(self, window_manager):
        """Test parsing xrandr output."""
        xrandr_output = """Screen 0: minimum 8 x 8, current 5120 x 1440, maximum 16384 x 16384
DP-2 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
DP-4 connected 2560x1440+2560+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
HDMI-A-1 disconnected (normal left inverted right x axis y axis)"""

        monitors = window_manager._parse_xrandr_output(xrandr_output)

        assert len(monitors) == 2

        # Check first monitor
        assert monitors[0].name == "DP-2"
        assert monitors[0].x == 0
        assert monitors[0].y == 0
        assert monitors[0].width == 2560
        assert monitors[0].height == 1440

        # Check second monitor
        assert monitors[1].name == "DP-4"
        assert monitors[1].x == 2560
        assert monitors[1].y == 0
        assert monitors[1].width == 2560
        assert monitors[1].height == 1440

    def test_parse_xrandr_output_no_monitors(self, window_manager):
        """Test parsing xrandr output with no connected monitors."""
        xrandr_output = "No displays found"

        monitors = window_manager._parse_xrandr_output(xrandr_output)

        assert len(monitors) == 1
        assert monitors[0].name == "default"

    @patch("subprocess.run")
    def test_detect_monitors_success(self, mock_run, window_manager):
        """Test successful monitor detection."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "DP-1 connected 1920x1080+0+0"

        monitors = window_manager.detect_monitors()

        assert len(monitors) == 1
        assert monitors[0].name == "DP-1"

    @patch("subprocess.run")
    def test_detect_monitors_failure(self, mock_run, window_manager):
        """Test monitor detection fallback on failure."""
        mock_run.side_effect = subprocess.TimeoutExpired("xrandr", 2)

        monitors = window_manager.detect_monitors()

        assert len(monitors) == 1
        assert monitors[0].name == "default"

    def test_find_current_monitor_found(self, window_manager):
        """Test finding current monitor when cursor is on a monitor."""
        monitors = [
            MonitorInfo("DP-1", 0, 0, 1920, 1080),
            MonitorInfo("DP-2", 1920, 0, 1920, 1080),
        ]

        # Mock pointer position to be on second monitor
        window_manager.root.winfo_pointerx.return_value = 2000
        window_manager.root.winfo_pointery.return_value = 500

        current = window_manager.find_current_monitor(monitors)

        assert current is not None
        assert current.name == "DP-2"

    def test_find_current_monitor_not_found(self, window_manager):
        """Test finding current monitor when cursor is not on any monitor."""
        monitors = [
            MonitorInfo("DP-1", 0, 0, 1920, 1080),
        ]

        # Mock pointer position to be outside monitor
        window_manager.root.winfo_pointerx.return_value = 2000
        window_manager.root.winfo_pointery.return_value = 500

        current = window_manager.find_current_monitor(monitors)

        assert current is None

    def test_position_window_centered(self, window_manager, mock_config):
        """Test centering window on monitor."""
        # Mock monitor detection to return a single monitor
        monitor = MonitorInfo("DP-1", 100, 200, 1920, 1080)

        with (
            patch.object(window_manager, "detect_monitors") as mock_detect,
            patch.object(window_manager, "find_current_monitor") as mock_find,
        ):
            mock_detect.return_value = [monitor]
            mock_find.return_value = monitor

            window_manager.position_window_centered()

            # Should call geometry with centered position
            expected_x = 100 + (1920 // 2) - (800 // 2)  # 100 + 960 - 400 = 660
            expected_y = 200 + (1080 // 2) - (150 // 2)  # 200 + 540 - 75 = 665

            window_manager.root.geometry.assert_called_with(
                f"800x150+{expected_x}+{expected_y}"
            )

    def test_expand_window(self, window_manager):
        """Test expanding window height."""
        window_manager.original_height = 150
        window_manager.root.geometry.return_value = "800x150+100+200"

        window_manager.expand_window(200)

        window_manager.root.geometry.assert_called_with("800x350+100+200")

    def test_restore_original_height(self, window_manager):
        """Test restoring window to original height."""
        window_manager.original_height = 150
        window_manager.root.geometry.return_value = "800x350+100+200"

        window_manager.restore_original_height()

        window_manager.root.geometry.assert_called_with("800x150+100+200")

    def test_ensure_focus(self, window_manager):
        """Test ensuring window focus."""
        window_manager.ensure_focus()

        window_manager.root.lift.assert_called_once()
        window_manager.root.focus_force.assert_called_once()

    def test_show_window(self, window_manager):
        """Test showing window."""
        window_manager.show_window()

        window_manager.root.deiconify.assert_called_once()
        window_manager.root.after.assert_called_once_with(
            100, window_manager.ensure_focus
        )
