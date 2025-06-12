"""Speech transcription functionality for Quip."""

import json
import threading
import wave
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Callable
from pathlib import Path

import numpy as np


class TranscriptionEngine(ABC):
    """Abstract base class for transcription engines."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the transcription engine. Returns True if successful."""
        pass

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data to text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and working."""
        pass


class MockEngine(TranscriptionEngine):
    """Mock transcription engine for testing."""

    def __init__(self):
        self._initialized = False

    def initialize(self) -> bool:
        """Mock initialization."""
        self._initialized = True
        print("Mock transcription engine initialized")
        return True

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Mock transcription."""
        duration = len(audio_data) / sample_rate
        return f"[Mock transcription: {duration:.1f}s of audio captured]"

    def is_available(self) -> bool:
        """Mock is always available."""
        return True


class VoskEngine(TranscriptionEngine):
    """Vosk speech recognition engine (local, lightweight)."""

    def __init__(self, model_path: Optional[str] = None, language: str = "en"):
        self.language = language
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self._initialized = False

    def initialize(self) -> bool:
        """Load the Vosk model."""
        if self._initialized:
            return True

        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel

            # Suppress Vosk logging
            SetLogLevel(-1)

            # Try to find a suitable model
            model_path = self._find_model()
            if not model_path:
                print(
                    "No Vosk model found. Please download a model from https://alphacephei.com/vosk/models"
                )
                return False

            print(f"Loading Vosk model from {model_path}...")
            self.model = Model(str(model_path))
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self._initialized = True
            print("Vosk model loaded successfully")
            return True
        except ImportError:
            print("Vosk not available - voice transcription disabled")
            return False
        except Exception as e:
            print(f"Failed to initialize Vosk: {e}")
            return False

    def _find_model(self) -> Optional[Path]:
        """Find a suitable Vosk model."""
        if self.model_path and Path(self.model_path).exists():
            return Path(self.model_path)

        # Common model locations
        possible_paths = [
            Path.home() / ".cache" / "vosk",
            Path.home() / "vosk-models",
            Path("/usr/share/vosk"),
            Path("/opt/vosk"),
            Path.cwd() / "vosk-models",
            Path(__file__).parent / "vosk-models",  # Look next to this script
            Path.home()
            / ".local"
            / "share"
            / "quip"
            / "desktop"
            / "vosk-models",  # Installed location
        ]

        # Look for English models first, then any model
        model_patterns = [
            "*en*",  # English models
            "*small*",  # Small models
            "*",  # Any model
        ]

        for base_path in possible_paths:
            if not base_path.exists():
                continue

            for pattern in model_patterns:
                for model_dir in base_path.glob(pattern):
                    if model_dir.is_dir() and (model_dir / "am" / "final.mdl").exists():
                        return model_dir

        return None

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using Vosk."""
        if not self._initialized or self.recognizer is None:
            raise RuntimeError("Vosk engine not initialized")

        try:
            # Convert numpy array to WAV format that Vosk expects
            # Vosk expects 16-bit PCM data
            if audio_data.dtype != np.int16:
                # Convert float32 to int16
                if audio_data.dtype == np.float32:
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)

            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with wave.open(temp_file.name, "wb") as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data.tobytes())

                # Read back and transcribe
                with wave.open(temp_file.name, "rb") as wav_file:
                    text_parts = []

                    while True:
                        data = wav_file.readframes(4000)
                        if len(data) == 0:
                            break

                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            if result.get("text"):
                                text_parts.append(result["text"])

                    # Get final result
                    final_result = json.loads(self.recognizer.FinalResult())
                    if final_result.get("text"):
                        text_parts.append(final_result["text"])

                # Clean up temp file
                Path(temp_file.name).unlink(missing_ok=True)

            return " ".join(text_parts).strip()
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    def is_available(self) -> bool:
        """Check if Vosk is available."""
        import importlib.util

        return importlib.util.find_spec("vosk") is not None


class TranscriptionService:
    """Service for managing speech transcription with pluggable engines."""

    def __init__(self, engine: Optional[TranscriptionEngine] = None):
        self.engine = engine or VoskEngine()
        self.is_initialized = False
        self.initialization_thread: Optional[threading.Thread] = None

        # Callbacks for UI feedback
        self.on_transcription_start: Optional[Callable] = None
        self.on_transcription_complete: Optional[Callable[[str], None]] = None
        self.on_transcription_error: Optional[Callable[[str], None]] = None

    def initialize_async(self) -> None:
        """Initialize transcription engine asynchronously."""
        if self.initialization_thread and self.initialization_thread.is_alive():
            return

        self.initialization_thread = threading.Thread(target=self._initialize_engine)
        self.initialization_thread.start()

    def _initialize_engine(self) -> None:
        """Internal method to initialize the engine."""
        try:
            self.is_initialized = self.engine.initialize()
            if not self.is_initialized:
                print("Failed to initialize transcription engine")
        except Exception as e:
            print(f"Error initializing transcription engine: {e}")
            self.is_initialized = False

    def wait_for_initialization(self, timeout: float = 30.0) -> bool:
        """Wait for engine initialization to complete."""
        if self.is_initialized:
            return True

        if self.initialization_thread and self.initialization_thread.is_alive():
            self.initialization_thread.join(timeout=timeout)

        return self.is_initialized

    def transcribe_async(
        self, audio_data: np.ndarray, sample_rate: int = 16000
    ) -> None:
        """Transcribe audio asynchronously."""
        if not self.is_initialized:
            if self.on_transcription_error:
                self.on_transcription_error("Transcription engine not initialized")
            return

        thread = threading.Thread(
            target=self._transcribe_audio, args=(audio_data, sample_rate)
        )
        thread.start()

    def _transcribe_audio(self, audio_data: np.ndarray, sample_rate: int) -> None:
        """Internal method to transcribe audio."""
        try:
            if self.on_transcription_start:
                self.on_transcription_start()

            text = self.engine.transcribe(audio_data, sample_rate)

            if self.on_transcription_complete:
                self.on_transcription_complete(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Transcription error: {error_msg}")
            if self.on_transcription_error:
                self.on_transcription_error(error_msg)

    def set_engine(self, engine: TranscriptionEngine) -> None:
        """Switch to a different transcription engine."""
        self.engine = engine
        self.is_initialized = False
        self.initialize_async()

    def get_supported_engines(self) -> dict:
        """Get list of available transcription engines."""
        engines = {}

        # Check Vosk
        vosk_engine = VoskEngine()
        if vosk_engine.is_available():
            engines["vosk"] = {
                "name": "Vosk (Local, Lightweight)",
                "description": "Fast offline transcription with small models",
                "languages": ["en", "de", "fr", "es", "ru", "cn", "etc"],
            }

        # Check Mock (always available)
        engines["mock"] = {
            "name": "Mock Engine (Testing)",
            "description": "For testing voice recording functionality",
            "languages": ["any"],
        }

        return engines


# Factory function for easy instantiation
def create_transcription_service(
    engine_type: str = "vosk",
    model_size: str = "small",  # Not used for Vosk but kept for compatibility
    language: str = "en",
) -> TranscriptionService:
    """Create a transcription service with the specified engine."""
    if engine_type == "vosk":
        engine = VoskEngine(language=language)
    elif engine_type == "mock":
        engine = MockEngine()
    else:
        # Fall back to mock if unknown engine type
        print(f"Unknown engine type '{engine_type}', falling back to mock engine")
        engine = MockEngine()

    return TranscriptionService(engine)
