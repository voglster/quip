"""Voice recording functionality for Quip."""

import threading
import time
from typing import Optional, Callable

import numpy as np
import sounddevice as sd


class VoiceRecorder:
    """Handles audio recording with real-time feedback."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
        self.recording_thread: Optional[threading.Thread] = None

        # Callbacks for UI feedback
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_audio_level: Optional[Callable[[float], None]] = None

    def start_recording(self) -> bool:
        """Start recording audio. Returns True if successful."""
        if self.is_recording:
            return False

        try:
            self.audio_data = []
            self.is_recording = True

            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()

            if self.on_recording_start:
                self.on_recording_start()

            return True
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return audio data."""
        if not self.is_recording:
            return None

        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)

        if self.on_recording_stop:
            self.on_recording_stop()

        # Convert to numpy array if we have data
        if self.audio_data:
            audio_array = np.concatenate(self.audio_data, axis=0)
            return audio_array.flatten()

        return None

    def _record_audio(self):
        """Internal method to record audio in chunks."""

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")

            if self.is_recording:
                # Store audio data
                self.audio_data.append(indata.copy())

                # Calculate audio level for visual feedback
                if self.on_audio_level:
                    level = float(np.sqrt(np.mean(indata**2)))
                    self.on_audio_level(level)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=audio_callback,
                blocksize=1024,
            ):
                # Keep recording until stopped
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False

    def get_audio_devices(self) -> dict:
        """Get available audio input devices."""
        try:
            devices = sd.query_devices()
            input_devices = {}

            for i, device in enumerate(devices):
                if device["max_input_channels"] > 0:
                    input_devices[i] = {
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": device["default_samplerate"],
                    }

            return input_devices
        except Exception as e:
            print(f"Failed to get audio devices: {e}")
            return {}

    def test_audio_input(self, duration: float = 1.0) -> bool:
        """Test if audio input is working."""
        try:
            # Record for a short duration
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            )
            sd.wait()  # Wait for recording to finish

            # Check if we got any audio data
            max_level = float(np.max(np.abs(recording)))
            return max_level > 0.001  # Some minimal threshold
        except Exception as e:
            print(f"Audio test failed: {e}")
            return False
