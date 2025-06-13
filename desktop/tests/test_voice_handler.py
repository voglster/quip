"""Tests for voice_handler module."""

import time
from unittest.mock import Mock, patch

import pytest

from voice.voice_handler import VoiceHandler


class TestVoiceHandler:
    """Test VoiceHandler functionality."""

    @pytest.fixture
    def voice_handler(self, mock_config, mock_voice_components):
        """Create a VoiceHandler instance for testing."""
        with (
            patch("voice.voice_handler.config", mock_config),
            patch("voice.voice_handler.VoiceRecorder") as mock_recorder,
            patch(
                "voice.voice_handler.create_transcription_service"
            ) as mock_transcription,
        ):
            mock_recorder.return_value = mock_voice_components["recorder"]
            mock_transcription.return_value = mock_voice_components["transcription"]

            return VoiceHandler()

    def test_voice_handler_creation(self, voice_handler):
        """Test VoiceHandler initialization."""
        assert voice_handler.voice_recorder is not None
        assert voice_handler.transcription_service is not None
        assert voice_handler.recording_mode is False
        assert voice_handler.tab_physically_pressed is False

    def test_on_tab_press_first_time(self, voice_handler):
        """Test tab press for the first time."""
        should_break, action = voice_handler.on_tab_press()

        assert should_break is True
        assert action == "start_timing"
        assert voice_handler.tab_physically_pressed is True
        assert voice_handler.tab_press_time is not None

    def test_on_tab_press_repeat_event(self, voice_handler):
        """Test tab press repeat event (keyboard repeat)."""
        # First press
        voice_handler.on_tab_press()

        # Repeat event
        should_break, action = voice_handler.on_tab_press()

        assert should_break is True
        assert action == "ignore_repeat"

    def test_on_tab_press_debounce_repress(self, voice_handler):
        """Test tab press within debounce window."""
        voice_handler.tab_release_time = time.time()
        voice_handler.tab_physically_pressed = False

        should_break, action = voice_handler.on_tab_press()

        assert should_break is True
        assert action == "continue_hold"
        assert voice_handler.tab_physically_pressed is True

    def test_on_tab_release(self, voice_handler):
        """Test tab release."""
        voice_handler.tab_physically_pressed = True

        should_break, action = voice_handler.on_tab_release()

        assert should_break is True
        assert action == "process_release"
        assert voice_handler.tab_physically_pressed is False
        assert voice_handler.tab_release_time is not None

    def test_on_tab_release_not_pressed(self, voice_handler):
        """Test tab release when not pressed."""
        voice_handler.tab_physically_pressed = False

        should_break, action = voice_handler.on_tab_release()

        assert should_break is True
        assert action == "already_released"

    def test_check_tab_hold_triggers_recording(self, voice_handler):
        """Test that tab hold triggers voice recording."""
        voice_handler.tab_physically_pressed = True
        voice_handler.recording_mode = False

        voice_handler.check_tab_hold()

        assert voice_handler.tab_consumed_as_hold is True
        assert voice_handler.recording_mode is True

    def test_check_tab_hold_already_released(self, voice_handler):
        """Test tab hold check when tab already released."""
        voice_handler.tab_physically_pressed = False

        voice_handler.check_tab_hold()

        assert voice_handler.tab_consumed_as_hold is False
        assert voice_handler.recording_mode is False

    def test_start_voice_recording(self, voice_handler, mock_voice_components):
        """Test starting voice recording."""
        mock_voice_components["recorder"].start_recording.return_value = True

        result = voice_handler.start_voice_recording()

        assert result is True
        assert voice_handler.recording_mode is True
        mock_voice_components["recorder"].start_recording.assert_called_once()

    def test_start_voice_recording_failure(self, voice_handler, mock_voice_components):
        """Test starting voice recording when it fails."""
        mock_voice_components["recorder"].start_recording.return_value = False

        result = voice_handler.start_voice_recording()

        assert result is False
        assert voice_handler.recording_mode is False

    def test_start_voice_recording_already_recording(self, voice_handler):
        """Test starting voice recording when already recording."""
        voice_handler.recording_mode = True

        result = voice_handler.start_voice_recording()

        assert result is True

    def test_stop_voice_recording(self, voice_handler, mock_voice_components):
        """Test stopping voice recording."""
        voice_handler.recording_mode = True
        mock_voice_components["recorder"].stop_recording.return_value = b"audio_data"

        voice_handler.stop_voice_recording()

        assert voice_handler.recording_mode is False
        mock_voice_components["recorder"].stop_recording.assert_called_once()
        mock_voice_components["transcription"].transcribe_async.assert_called_once_with(
            b"audio_data"
        )

    def test_stop_voice_recording_no_audio(self, voice_handler, mock_voice_components):
        """Test stopping voice recording with no audio data."""
        voice_handler.recording_mode = True
        mock_voice_components["recorder"].stop_recording.return_value = None

        voice_handler.stop_voice_recording()

        assert voice_handler.recording_mode is False
        mock_voice_components["transcription"].transcribe_async.assert_not_called()

    def test_stop_voice_recording_not_recording(
        self, voice_handler, mock_voice_components
    ):
        """Test stopping voice recording when not recording."""
        voice_handler.recording_mode = False

        voice_handler.stop_voice_recording()

        mock_voice_components["recorder"].stop_recording.assert_not_called()

    def test_process_immediate_tab_release_short_tap(self, voice_handler):
        """Test processing immediate tab release for short tap."""
        voice_handler.tab_press_time = time.time() - 0.1  # 100ms ago
        voice_handler.tab_hold_threshold = 0.5  # 500ms
        voice_handler.recording_mode = False
        voice_handler.tab_consumed_as_hold = False

        action = voice_handler.process_immediate_tab_release()

        assert action == "insert_tab"

    def test_process_immediate_tab_release_recording_mode(self, voice_handler):
        """Test processing immediate tab release in recording mode."""
        voice_handler.tab_press_time = time.time() - 0.6  # 600ms ago
        voice_handler.recording_mode = True

        action = voice_handler.process_immediate_tab_release()

        assert action == "stop_recording"
        assert voice_handler.recording_mode is False

    def test_process_immediate_tab_release_already_consumed(self, voice_handler):
        """Test processing immediate tab release when already consumed as hold."""
        voice_handler.tab_press_time = time.time() - 0.6  # 600ms ago
        voice_handler.tab_consumed_as_hold = True
        voice_handler.recording_mode = False

        action = voice_handler.process_immediate_tab_release()

        assert action == "already_handled"

    def test_process_tab_release_after_debounce_recording_mode(self, voice_handler):
        """Test processing tab release after debounce in recording mode."""
        voice_handler.tab_physically_pressed = False
        voice_handler.recording_mode = True

        voice_handler.process_tab_release_after_debounce()

        assert voice_handler.recording_tail_active is True

    def test_stop_recording_tail_still_released(self, voice_handler):
        """Test stopping recording tail when tab still released."""
        voice_handler.recording_tail_active = True
        voice_handler.tab_physically_pressed = False
        voice_handler.recording_mode = True
        voice_handler.tab_press_time = time.time() - 1.0  # Set up timing

        voice_handler.stop_recording_tail()

        assert voice_handler.recording_tail_active is False
        assert voice_handler.recording_mode is False

    def test_stop_recording_tail_repressed(self, voice_handler):
        """Test stopping recording tail when tab was re-pressed."""
        voice_handler.recording_tail_active = True
        voice_handler.tab_physically_pressed = True

        voice_handler.stop_recording_tail()

        assert voice_handler.recording_tail_active is False

    def test_callbacks_setup(self, voice_handler):
        """Test that callbacks are properly set up."""
        # Test external callback assignment
        mock_callback = Mock()
        voice_handler.on_recording_start = mock_callback

        assert voice_handler.on_recording_start == mock_callback

    def test_audio_feedback_initialization(self, voice_handler):
        """Test audio feedback initialization."""
        # Should initialize without error
        assert hasattr(voice_handler, "sound_record_start")
        assert hasattr(voice_handler, "sound_record_stop")

    @patch("voice.voice_handler.subprocess.run")
    @patch("voice.voice_handler.threading.Thread")
    def test_play_sound(self, mock_thread, mock_run, voice_handler, temp_dir):
        """Test playing sound effect."""
        # Create a mock sound file
        sound_file = temp_dir / "test.wav"
        sound_file.touch()

        voice_handler._play_sound(sound_file)

        # Should start a thread to play audio
        mock_thread.assert_called_once()

    def test_play_sound_nonexistent_file(self, voice_handler):
        """Test playing non-existent sound file."""
        # Should not raise exception
        voice_handler._play_sound(None)

    def test_async_transcription_loading(self, mock_config):
        """Test that transcription service loads asynchronously."""
        import time

        with (
            patch("voice.voice_handler.VoiceRecorder"),
            patch("voice.voice_handler.create_transcription_service") as mock_create,
        ):
            mock_transcription = Mock()
            mock_create.return_value = mock_transcription

            voice_handler = VoiceHandler()

            # Initially should be loading
            assert voice_handler.get_transcription_status() == "loading"
            assert not voice_handler.is_transcription_ready()

            # Wait a short time for async loading to complete
            for _ in range(50):  # Max 0.5 seconds
                if voice_handler.is_transcription_ready():
                    break
                time.sleep(0.01)

            # Should be ready after async loading
            assert voice_handler.get_transcription_status() == "ready"
            assert voice_handler.is_transcription_ready()
            assert voice_handler.transcription_service == mock_transcription

    def test_transcription_not_ready_during_recording(self, voice_handler):
        """Test handling when transcription service isn't ready during recording."""
        import time

        # Set up recording state
        voice_handler.recording_mode = True
        voice_handler.tab_press_time = time.time()

        # Set transcription service to None (not ready)
        voice_handler.transcription_service = None
        voice_handler.transcription_loading = True

        # Mock voice recorder to return audio data with length
        mock_audio_data = [1, 2, 3, 4, 5]  # Mock audio array with length > 0
        voice_handler.voice_recorder.stop_recording.return_value = mock_audio_data

        # Mock transcription error callback
        voice_handler.on_transcription_error = Mock()

        # Call stop_voice_recording directly (which is what _process_final_tab_release calls)
        voice_handler.stop_voice_recording()

        # Should call error callback with loading message
        voice_handler.on_transcription_error.assert_called_once_with(
            "Transcription service still loading, please try again in a moment"
        )
