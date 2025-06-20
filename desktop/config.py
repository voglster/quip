"""Configuration management for Quip"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Handle tomli import for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class QuipConfig:
    """Handles loading and managing Quip configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "quip"
        self.config_file = self.config_dir / "config.toml"
        self._config_data = {}
        self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration values"""
        return {
            "hotkeys": {"spawn": "win+space", "cleanup": "ctrl+shift+l"},
            "ui": {
                "debug": False,
                "window_width": 800,
                "window_height": 150,
                "transparency": 0.98,
            },
            "notes": {"save_path": "~/notes/5. Inbox/Inbox.md"},
            "system": {"auto_install_hotkeys": True},
            "updates": {
                "auto_update_check": True,
                "check_interval_hours": 1,
            },
            "llm": {
                "enabled": False,
                "base_url": "http://localhost:11434/v1",
                "model": "llama3.2:3b",
                "api_key": "",
                "timeout_seconds": 30,
                "max_tokens": 1000,
                "temperature": 0.7,
                "improve_prompt": "This is a quick note that needs improvement. Fix spelling, grammar, and clarity while preserving the original meaning and intent. Return only the improved text without explanations or additions:",
            },
            "voice": {
                "enabled": True,
                "model_size": "base",
                "language": "auto",
                "hold_threshold_ms": 200,
                "audio_feedback": True,
                "recording_tail_ms": 400,
            },
        }

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _create_default_config(self):
        """Create default config file if it doesn't exist"""
        self._ensure_config_dir()

        if not self.config_file.exists():
            default_config = self._get_default_config()
            self._write_config(default_config)

    def _write_config(self, config_data: Dict[str, Any]):
        """Write config data to TOML file"""
        import tomli_w

        with open(self.config_file, "wb") as f:
            tomli_w.dump(config_data, f)

    def _load_config(self):
        """Load configuration from file"""
        self._create_default_config()

        try:
            with open(self.config_file, "rb") as f:
                self._config_data = tomllib.load(f)
        except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
            print(f"Warning: Could not load config file: {e}")
            self._config_data = self._get_default_config()

    def reload(self):
        """Reload configuration from file"""
        self._load_config()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self._config_data.get(section, {}).get(key, default)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section"""
        return self._config_data.get(section, {})

    def _normalize_hotkey(self, hotkey: str) -> str:
        """Convert user-friendly hotkey syntax to pynput format"""
        # Convert common key names to pynput format
        replacements = {
            "win": "<cmd>",
            "super": "<cmd>",
            "ctrl": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "space": "<space>",
            "enter": "<enter>",
            "tab": "<tab>",
            "esc": "<esc>",
            "escape": "<esc>",
        }

        normalized = hotkey.lower()

        # Split by + and process each part
        parts = [part.strip() for part in normalized.split("+")]
        normalized_parts = []

        for part in parts:
            if part in replacements:
                normalized_parts.append(replacements[part])
            elif len(part) == 1:
                # Single character keys stay as-is
                normalized_parts.append(part)
            else:
                # Unknown key, wrap in brackets as fallback
                normalized_parts.append(f"<{part}>")

        return "+".join(normalized_parts)

    @property
    def spawn_hotkey(self) -> str:
        """Get the spawn hotkey"""
        hotkey = self.get("hotkeys", "spawn", "<cmd>+space")
        return self._normalize_hotkey(hotkey)

    @property
    def cleanup_hotkey(self) -> str:
        """Get the cleanup hotkey"""
        hotkey = self.get("hotkeys", "cleanup", "<ctrl>+<shift>+l")
        return self._normalize_hotkey(hotkey)

    @property
    def debug_mode(self) -> bool:
        """Get debug mode setting"""
        return self.get("ui", "debug", False)

    @property
    def window_width(self) -> int:
        """Get window width"""
        return self.get("ui", "window_width", 800)

    @property
    def window_height(self) -> int:
        """Get window height"""
        return self.get("ui", "window_height", 150)

    @property
    def transparency(self) -> float:
        """Get window transparency"""
        return self.get("ui", "transparency", 0.98)

    @property
    def save_path(self) -> str:
        """Get notes save path"""
        return os.path.expanduser(
            self.get("notes", "save_path", "~/notes/5. Inbox/Inbox.md")
        )

    @property
    def config_file_path(self) -> Path:
        """Get path to config file"""
        return self.config_file

    @property
    def auto_update_check(self) -> bool:
        """Get auto update check setting"""
        return self.get("updates", "auto_update_check", True)

    @property
    def check_interval_hours(self) -> int:
        """Get update check interval in hours"""
        return self.get("updates", "check_interval_hours", 1)

    @property
    def llm_enabled(self) -> bool:
        """Get LLM enabled setting"""
        return self.get("llm", "enabled", False)

    @property
    def llm_base_url(self) -> str:
        """Get LLM base URL"""
        return self.get("llm", "base_url", "http://10.0.6.16:11434")

    @property
    def llm_model(self) -> str:
        """Get LLM model name"""
        return self.get("llm", "model", "LoTUs5494/mistral-small-3.1:latest")

    @property
    def llm_api_key(self) -> str:
        """Get LLM API key"""
        return self.get("llm", "api_key", "")

    @property
    def llm_timeout_seconds(self) -> int:
        """Get LLM timeout in seconds"""
        return self.get("llm", "timeout_seconds", 30)

    @property
    def llm_max_tokens(self) -> int:
        """Get LLM max tokens"""
        return self.get("llm", "max_tokens", 1000)

    @property
    def llm_temperature(self) -> float:
        """Get LLM temperature"""
        return self.get("llm", "temperature", 0.7)

    @property
    def llm_improve_prompt(self) -> str:
        """Get LLM improve prompt"""
        return self.get(
            "llm",
            "improve_prompt",
            "This is a quick note that needs improvement. Fix spelling, grammar, and clarity while preserving the original meaning and intent. Return only the improved text without explanations or additions:",
        )

    @property
    def voice_enabled(self) -> bool:
        """Get voice recording enabled setting"""
        return self.get("voice", "enabled", True)

    @property
    def voice_model_size(self) -> str:
        """Get voice model size"""
        return self.get("voice", "model_size", "base")

    @property
    def voice_language(self) -> str:
        """Get voice language setting"""
        return self.get("voice", "language", "auto")

    @property
    def voice_hold_threshold_ms(self) -> int:
        """Get voice hold threshold in milliseconds"""
        return self.get("voice", "hold_threshold_ms", 200)

    @property
    def voice_audio_feedback(self) -> bool:
        """Get voice audio feedback setting"""
        return self.get("voice", "audio_feedback", True)

    @property
    def voice_recording_tail_ms(self) -> int:
        """Get voice recording tail duration in milliseconds"""
        return self.get("voice", "recording_tail_ms", 300)


# Global config instance
config = QuipConfig()
