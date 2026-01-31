"""Centralized font configuration for the Quip UI."""

from config import config

# Base font family - loaded from config, defaults to "DejaVu Sans"
# Use "Helvetica" on HiDPI Linux displays for better anti-aliasing
FONT_FAMILY = config.font_family

# Font configurations for different UI elements
MAIN_TEXT_FONT = (FONT_FAMILY, 14)
PLACEHOLDER_FONT = (FONT_FAMILY, 16, "italic")
RECORDING_FONT = (FONT_FAMILY, 18, "bold")
PROCESSING_FONT = (FONT_FAMILY, 18, "bold")
RECORDING_TAIL_FONT = (FONT_FAMILY, 18, "bold")
HELP_TEXT_FONT = (FONT_FAMILY, 12)
KEYBIND_FONT = (FONT_FAMILY, 10)
