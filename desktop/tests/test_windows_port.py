"""Tests for Windows-specific port changes."""

import os
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest.mock import Mock, patch, MagicMock

import pytest

from config import QuipConfig
from ui.window_manager import WindowManager
from transcription import VoskEngine

class TestWindowsPort:
    """Test changes made for Windows support."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=MagicMock)
    @patch("tomllib.load", return_value={})
    def test_config_paths_windows(self, mock_toml, mock_open, mock_exists, mock_mkdir):
        """Test that config paths are correct on Windows."""
        with patch("os.name", "nt"), patch("pathlib.Path.home", return_value=Path("C:/Users/TestUser")):
            config = QuipConfig()
            assert config.config_dir == Path("C:/Users/TestUser/.quip")

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=MagicMock)
    @patch("tomllib.load", return_value={})
    def test_config_paths_linux(self, mock_toml, mock_open, mock_exists, mock_mkdir):
        """Test that config paths remain correct on Linux."""
        # Mock Path to avoid instantiation error
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = mock_path
        
        with patch("os.name", "posix"), patch("pathlib.Path.home", return_value=mock_path):
            config = QuipConfig()
            # On Linux, it should be home / .config / quip
            assert mock_path.__truediv__.call_count >= 2

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=MagicMock)
    @patch("tomllib.load", return_value={})
    def test_default_font_windows(self, mock_toml, mock_open, mock_exists, mock_mkdir):
        """Test default font family on Windows."""
        with patch("os.name", "nt"), patch("pathlib.Path.home", return_value=Path("C:/Users/TestUser")):
            config = QuipConfig()
            assert config.font_family == "Segoe UI"

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=MagicMock)
    @patch("tomllib.load", return_value={})
    def test_default_font_linux(self, mock_toml, mock_open, mock_exists, mock_mkdir):
        """Test default font family on Linux."""
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = mock_path
        
        with patch("os.name", "posix"), patch("pathlib.Path.home", return_value=mock_path):
            config = QuipConfig()
            assert config.font_family == "DejaVu Sans"

    def test_window_properties_windows(self, mock_tkinter):
        """Test window properties on Windows."""
        with patch("os.name", "nt"), patch("ui.window_manager.config") as mock_conf:
            mock_conf.transparency = 0.95
            wm = WindowManager(mock_tkinter["root"])
            wm.setup_window_properties()
            
            mock_tkinter["root"].overrideredirect.assert_called_with(True)
            mock_tkinter["root"].wm_attributes.assert_any_call("-toolwindow", True)

    def test_window_properties_linux(self, mock_tkinter):
        """Test window properties on Linux."""
        with patch("os.name", "posix"), patch("ui.window_manager.config") as mock_conf:
            mock_conf.transparency = 0.95
            wm = WindowManager(mock_tkinter["root"])
            wm.setup_window_properties()
            
            assert not mock_tkinter["root"].overrideredirect.called
            mock_tkinter["root"].wm_attributes.assert_any_call("-type", "splash")

    def test_vosk_model_paths_windows(self):
        """Test Vosk model search paths on Windows."""
        with patch("os.name", "nt"), \
             patch("os.environ.get", return_value="C:/AppData"), \
             patch("pathlib.Path.exists", return_value=False), \
             patch("pathlib.Path.glob", return_value=[]):
            engine = VoskEngine()
            engine._find_model()
            os.environ.get.assert_any_call("APPDATA")

    @patch("os.startfile")
    @patch("subprocess.Popen")
    def test_open_settings_windows(self, mock_popen, mock_startfile, mock_tkinter):
        """Test opening settings on Windows."""
        from core.app import QuipApplication
        with patch("os.name", "nt"), patch("core.app.config") as mock_conf:
            mock_conf.config_file_path = Path("C:/test/config.toml")
            app = QuipApplication()
            app._open_settings()
            
            mock_startfile.assert_called_once()
            assert not mock_popen.called

    @patch("os.startfile")
    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_open_settings_linux(self, mock_popen, mock_run, mock_startfile, mock_tkinter):
        """Test opening settings on Linux."""
        from core.app import QuipApplication
        mock_run.return_value = Mock(returncode=0, stdout="DP-1 connected 1920x1080+0+0")
        
        with patch("os.name", "posix"), patch("core.app.config") as mock_conf:
            mock_conf.config_file_path = PurePosixPath("/home/test/config.toml")
            app = QuipApplication()
            app._open_settings()
            
            assert not mock_startfile.called
            mock_popen.assert_called_once()
