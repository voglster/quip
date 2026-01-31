"""Shared test fixtures and configuration."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config():
    """Mock config object with default values."""
    config = Mock()
    config.window_width = 800
    config.window_height = 150
    config.transparency = 0.95
    config.font_family = "DejaVu Sans"
    config.save_path = "~/notes/5. Inbox/Inbox.md"
    config.debug_mode = False
    config.llm_enabled = False
    config.llm_model = "gpt-3.5-turbo"
    config.llm_max_tokens = 150
    config.llm_temperature = 0.7
    config.llm_base_url = "https://api.openai.com/v1"
    config.llm_api_key = ""
    config.llm_timeout_seconds = 30
    config.voice_hold_threshold_ms = 500
    config.voice_recording_tail_ms = 800
    config.voice_model_size = "small"
    config.voice_language = "en"
    config.config_file_path = Path("~/.config/quip/config.toml")
    return config


@pytest.fixture
def mock_tkinter():
    """Mock tkinter for testing without GUI."""
    with patch("tkinter.Tk") as mock_tk:
        mock_root = Mock()
        mock_tk.return_value = mock_root

        # Mock common tkinter methods
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_root.winfo_pointerx.return_value = 960
        mock_root.winfo_pointery.return_value = 540
        mock_root.geometry.return_value = "800x150+560+465"

        with (
            patch("tkinter.Frame") as mock_frame,
            patch("tkinter.Text") as mock_text,
            patch("tkinter.Label") as mock_label,
        ):
            yield {
                "root": mock_root,
                "frame": mock_frame,
                "text": mock_text,
                "label": mock_label,
            }


@pytest.fixture
def mock_voice_components():
    """Mock voice recording and transcription components."""
    with (
        patch("voice_recorder.VoiceRecorder") as mock_recorder,
        patch("transcription.create_transcription_service") as mock_transcription,
    ):
        mock_recorder_instance = Mock()
        mock_recorder_instance.start_recording.return_value = True
        mock_recorder_instance.stop_recording.return_value = b"audio_data"
        mock_recorder.return_value = mock_recorder_instance

        mock_transcription_instance = Mock()
        mock_transcription.return_value = mock_transcription_instance

        yield {
            "recorder": mock_recorder_instance,
            "transcription": mock_transcription_instance,
        }
