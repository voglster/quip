"""Voice recording and transcription coordination."""

import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from config import config
from transcription import create_transcription_service


class VoiceHandler:
    """Coordinates voice recording and transcription with UI feedback."""

    def __init__(self):
        # Voice recording state
        self.tab_press_time: Optional[float] = None
        self.tab_hold_threshold = (
            config.voice_hold_threshold_ms / 1000.0
        )  # Convert to seconds
        self.recording_mode = False
        self.tab_physically_pressed = False  # Track physical key state
        self.tab_consumed_as_hold = False  # Track if this press was used for recording
        self.tab_release_time: Optional[float] = None  # Track when tab was released
        self.release_debounce_time = 0.1  # 100ms debounce for rapid press/release
        self.recording_tail_time = (
            config.voice_recording_tail_ms / 1000.0
        )  # Convert to seconds
        self.recording_tail_active = False  # Track if we're in the tail period

        # Defer component initialization for faster startup
        self.voice_recorder = None
        self.voice_recorder_loading = False
        self.voice_recorder_failed = False

        # Defer transcription service initialization for faster startup
        self.transcription_service = None
        self.transcription_loading = False
        self.transcription_failed = False

        # Start loading transcription service in background
        self._start_transcription_loading()

        # Initialize audio feedback
        self._init_audio_feedback()

        # Callbacks for UI updates
        self.on_recording_start: Optional[Callable[[], None]] = None
        self.on_recording_stop: Optional[Callable[[], None]] = None
        self.on_recording_tail_start: Optional[Callable[[], None]] = None
        self.on_transcription_start: Optional[Callable[[], None]] = None
        self.on_transcription_complete: Optional[Callable[[str], None]] = None
        self.on_transcription_error: Optional[Callable[[str], None]] = None

        # Voice recorder will be initialized lazily when needed

    def _init_audio_feedback(self) -> None:
        """Initialize audio feedback file paths."""
        try:
            sounds_dir = Path(__file__).parent.parent / "sounds"
            self.sound_record_start = sounds_dir / "record_start.wav"
            self.sound_record_stop = sounds_dir / "record_stop.wav"

            # Check if sound files exist
            if self.sound_record_start.exists() and self.sound_record_stop.exists():
                if config.debug_mode:
                    print("DEBUG: Audio feedback files found")
            else:
                self.sound_record_start = None
                self.sound_record_stop = None
                if config.debug_mode:
                    print("DEBUG: Audio feedback files not found")
        except Exception as e:
            self.sound_record_start = None
            self.sound_record_stop = None
            if config.debug_mode:
                print(f"DEBUG: Audio feedback initialization failed: {e}")

    def _ensure_voice_recorder_loaded(self) -> bool:
        """Ensure voice recorder is loaded. Returns True if successful."""
        if self.voice_recorder:
            return True

        if self.voice_recorder_loading:
            return False  # Still loading

        if self.voice_recorder_failed:
            return False  # Failed to load

        # Load voice recorder now
        try:
            from voice_recorder import VoiceRecorder

            self.voice_recorder = VoiceRecorder()

            # Set up callbacks
            self.voice_recorder.on_recording_start = self._on_voice_recording_start
            self.voice_recorder.on_recording_stop = self._on_voice_recording_stop

            if config.debug_mode:
                print("DEBUG: Voice recorder loaded successfully")
            return True
        except Exception as e:
            self.voice_recorder_failed = True
            if config.debug_mode:
                print(f"DEBUG: Failed to load voice recorder: {e}")
            return False

    def start_voice_recorder_background_loading(self) -> None:
        """Start loading voice recorder in background thread to avoid first-use delay."""
        if (
            self.voice_recorder
            or self.voice_recorder_loading
            or self.voice_recorder_failed
        ):
            return  # Already loaded, loading, or failed

        self.voice_recorder_loading = True

        def load_voice_recorder():
            """Background thread function to load voice recorder."""
            try:
                if config.debug_mode:
                    print("DEBUG: Loading voice recorder in background...")

                from voice_recorder import VoiceRecorder

                voice_recorder = VoiceRecorder()

                # Set up callbacks
                voice_recorder.on_recording_start = self._on_voice_recording_start
                voice_recorder.on_recording_stop = self._on_voice_recording_stop

                self.voice_recorder = voice_recorder
                self.voice_recorder_loading = False

                if config.debug_mode:
                    print("DEBUG: Voice recorder loaded successfully in background")

            except Exception as e:
                self.voice_recorder_loading = False
                self.voice_recorder_failed = True
                if config.debug_mode:
                    print(f"DEBUG: Failed to load voice recorder in background: {e}")

        # Start loading in background thread
        threading.Thread(target=load_voice_recorder, daemon=True).start()

    def _play_sound(self, sound_path: Optional[Path]) -> None:
        """Play a sound effect if available."""
        try:
            if sound_path and sound_path.exists():
                # Use threading to avoid blocking the UI
                def play_audio():
                    try:
                        # Try different audio players based on system
                        subprocess.run(
                            ["aplay", str(sound_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=1,
                        )
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        try:
                            # Fallback for systems without aplay
                            subprocess.run(
                                ["paplay", str(sound_path)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=1,
                            )
                        except (subprocess.TimeoutExpired, FileNotFoundError):
                            if config.debug_mode:
                                print("DEBUG: No audio player found (aplay/paplay)")

                threading.Thread(target=play_audio, daemon=True).start()
        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Failed to play sound: {e}")

    def on_tab_press(self) -> tuple[bool, str]:
        """Handle Tab key press - start timing for hold detection.

        Returns:
            Tuple of (should_break, action_taken)
        """
        current_time = time.time()

        # Check if this is a quick re-press after a recent release (debounce)
        if (
            self.tab_release_time
            and current_time - self.tab_release_time < self.release_debounce_time
        ):
            if config.debug_mode:
                print("DEBUG: Tab re-pressed within debounce window - continuing hold")
            # This is a quick re-press, treat as continued hold
            self.tab_physically_pressed = True

            # If we're in tail period, cancel it and go back to normal recording
            if self.recording_tail_active:
                self.recording_tail_active = False
                if self.on_recording_start:
                    self.on_recording_start()
                if config.debug_mode:
                    print("DEBUG: Cancelled recording tail - back to normal recording")

            return True, "continue_hold"

        # Handle first press of physical key or new press after debounce period
        if not self.tab_physically_pressed:
            if config.debug_mode:
                print("DEBUG: Tab PHYSICALLY pressed (first time)")

            self.tab_press_time = current_time
            self.tab_physically_pressed = True
            self.tab_consumed_as_hold = False
            self.tab_release_time = None  # Clear release time

            return True, "start_timing"
        else:
            # This is a keyboard repeat event - ignore it
            if config.debug_mode:
                print("DEBUG: Tab repeat event - ignoring")

            return True, "ignore_repeat"

    def check_tab_hold(self) -> None:
        """Check if tab is still being held after threshold."""
        if not self.tab_physically_pressed or self.recording_mode:
            return  # Tab was already released or already recording

        if config.debug_mode:
            print("DEBUG: Tab hold detected - starting recording mode")

        self.tab_consumed_as_hold = True  # Mark this press as consumed by hold
        self.start_voice_recording()

    def on_tab_release(self) -> tuple[bool, str]:
        """Handle Tab key release - determine if it was tap or hold.

        Returns:
            Tuple of (should_break, action_taken)
        """
        current_time = time.time()

        if config.debug_mode:
            print("DEBUG: Tab PHYSICALLY released")

        if not self.tab_physically_pressed:
            return True, "already_released"

        self.tab_physically_pressed = False
        self.tab_release_time = current_time  # Record release time for debouncing

        return True, "process_release"

    def process_tab_release_after_debounce(self) -> None:
        """Process tab release after debounce period for recording mode."""
        if not self.tab_physically_pressed and self.recording_mode:
            # Tab is still released after debounce - start recording tail period
            self.recording_tail_active = True

            if config.debug_mode:
                print(
                    f"DEBUG: Starting recording tail period ({self.recording_tail_time:.1f}s)"
                )

            # Notify UI about tail state
            if self.on_recording_tail_start:
                self.on_recording_tail_start()

    def stop_recording_tail(self) -> None:
        """Stop recording after tail period expires."""
        if self.recording_tail_active and not self.tab_physically_pressed:
            # Tab is still released after tail period - actually stop recording
            self.recording_tail_active = False
            self._process_final_tab_release()
        elif self.tab_physically_pressed:
            # Tab was re-pressed during tail period - cancel tail and continue recording
            self.recording_tail_active = False
            if config.debug_mode:
                print("DEBUG: Tab re-pressed during tail period - continuing recording")
            if self.on_recording_start:
                self.on_recording_start()  # Go back to normal recording state

    def process_immediate_tab_release(self) -> str:
        """Process immediate tab release for short taps.

        Returns:
            Action taken ("insert_tab", "stop_recording", or "already_handled")
        """
        if not self.tab_press_time:
            return "no_press_time"

        hold_duration = time.time() - self.tab_press_time

        if self.recording_mode:
            # We were recording, stop recording
            self.stop_voice_recording()
            if config.debug_mode:
                print(
                    f"DEBUG: Completed hold ({hold_duration:.3f}s) - stopped recording"
                )
            return "stop_recording"
        elif not self.tab_consumed_as_hold and hold_duration < self.tab_hold_threshold:
            # Quick tap - should insert tab character
            if config.debug_mode:
                print(f"DEBUG: Quick tap ({hold_duration:.3f}s) - should INSERT TAB")
            return "insert_tab"
        else:
            if config.debug_mode:
                print(
                    f"DEBUG: Hold duration {hold_duration:.3f}s - already handled or too long"
                )
            return "already_handled"

    def _process_final_tab_release(self) -> None:
        """Process the actual tab release."""
        if not self.tab_press_time:
            return

        hold_duration = time.time() - self.tab_press_time

        if self.recording_mode:
            # We were recording, stop recording
            self.stop_voice_recording()
            if config.debug_mode:
                print(
                    f"DEBUG: Completed hold ({hold_duration:.3f}s) - stopped recording"
                )

    def start_voice_recording(self) -> bool:
        """Start voice recording mode with visual and audio feedback.

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.recording_mode:
            return True

        self.recording_mode = True

        # Audio feedback: play start sound
        self._play_sound(self.sound_record_start)

        # Notify UI
        if self.on_recording_start:
            self.on_recording_start()

        # Ensure voice recorder is loaded
        if not self._ensure_voice_recorder_loaded():
            if config.debug_mode:
                print("DEBUG: Voice recorder not available - falling back to text mode")
            self.stop_voice_recording()
            return False

        # Start actual voice recording
        success = self.voice_recorder.start_recording()
        if not success:
            if config.debug_mode:
                print(
                    "DEBUG: Failed to start voice recording - falling back to text mode"
                )
            self.stop_voice_recording()
            return False

        if config.debug_mode:
            print("DEBUG: Voice recording started")

        return True

    def stop_voice_recording(self) -> None:
        """Stop voice recording and process audio."""
        if not self.recording_mode:
            return

        self.recording_mode = False

        # Audio feedback: play stop sound
        self._play_sound(self.sound_record_stop)

        # Stop recording and get audio data
        audio_data = None
        if self.voice_recorder:
            audio_data = self.voice_recorder.stop_recording()

        if audio_data is not None and len(audio_data) > 0:
            # Check if transcription service is ready
            if self.transcription_service:
                # Notify UI about transcription start
                if self.on_transcription_start:
                    self.on_transcription_start()

                # Start transcription
                self.transcription_service.transcribe_async(audio_data)

                if config.debug_mode:
                    print(
                        f"DEBUG: Voice recording stopped - {len(audio_data)} audio samples captured"
                    )
            elif self.transcription_loading:
                # Transcription service still loading
                if self.on_transcription_error:
                    self.on_transcription_error(
                        "Transcription service still loading, please try again in a moment"
                    )
                if config.debug_mode:
                    print(
                        "DEBUG: Voice recording captured but transcription service still loading"
                    )
            else:
                # Transcription service failed to load
                if self.on_transcription_error:
                    self.on_transcription_error("Transcription service unavailable")
                if config.debug_mode:
                    print(
                        "DEBUG: Voice recording captured but transcription service unavailable"
                    )
        else:
            # No audio captured, notify UI
            if self.on_recording_stop:
                self.on_recording_stop()

            if config.debug_mode:
                print("DEBUG: Voice recording stopped - no audio data captured")

    # Internal callbacks
    def _on_voice_recording_start(self) -> None:
        """Internal callback when voice recording starts."""
        if config.debug_mode:
            print("DEBUG: Voice recording started (callback)")

    def _on_voice_recording_stop(self) -> None:
        """Internal callback when voice recording stops."""
        if config.debug_mode:
            print("DEBUG: Voice recording stopped (callback)")

    def _on_transcription_start_internal(self) -> None:
        """Internal callback when transcription starts."""
        if config.debug_mode:
            print("DEBUG: Transcription started")

    def _on_transcription_complete_internal(self, transcribed_text: str) -> None:
        """Internal callback when transcription completes successfully."""
        if config.debug_mode:
            print(f"DEBUG: Transcription completed: '{transcribed_text}'")

        # Notify external callback
        if self.on_transcription_complete:
            self.on_transcription_complete(transcribed_text)

    def _on_transcription_error_internal(self, error_message: str) -> None:
        """Internal callback when transcription fails."""
        if config.debug_mode:
            print(f"DEBUG: Transcription error: {error_message}")

        # Notify external callback
        if self.on_transcription_error:
            self.on_transcription_error(error_message)

    def _start_transcription_loading(self) -> None:
        """Start loading transcription service in background thread."""
        if self.transcription_loading or self.transcription_service:
            return

        self.transcription_loading = True

        def load_transcription():
            """Background thread function to load Vosk model."""
            try:
                if config.debug_mode:
                    print("DEBUG: Loading transcription service in background...")

                transcription_service = create_transcription_service(
                    model_size=config.voice_model_size, language=config.voice_language
                )

                # Initialize the transcription service
                transcription_service.initialize_async()

                # Set up callbacks once loaded
                transcription_service.on_transcription_start = (
                    self._on_transcription_start_internal
                )
                transcription_service.on_transcription_complete = (
                    self._on_transcription_complete_internal
                )
                transcription_service.on_transcription_error = (
                    self._on_transcription_error_internal
                )

                self.transcription_service = transcription_service
                self.transcription_loading = False

                if config.debug_mode:
                    print("DEBUG: Transcription service loaded successfully")

            except Exception as e:
                self.transcription_loading = False
                self.transcription_failed = True
                if config.debug_mode:
                    print(f"DEBUG: Failed to load transcription service: {e}")

        # Start loading in background thread
        threading.Thread(target=load_transcription, daemon=True).start()

    def is_transcription_ready(self) -> bool:
        """Check if transcription service is ready to use."""
        return self.transcription_service is not None

    def get_transcription_status(self) -> str:
        """Get current transcription service status."""
        if self.transcription_service:
            return "ready"
        elif self.transcription_loading:
            return "loading"
        elif self.transcription_failed:
            return "failed"
        else:
            return "not_started"
