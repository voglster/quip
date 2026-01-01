"""Enhanced text widget with overlay management and event handling."""

import tkinter as tk
from typing import Callable, Optional

from .fonts import MAIN_TEXT_FONT
from .overlays import OverlayManager


class QuipTextWidget:
    """Enhanced text widget with overlay management and smart content handling."""

    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"

        self._create_text_widget()
        self.overlay_manager = OverlayManager(parent_frame)

        # Event callbacks
        self.on_text_change: Optional[Callable[[str], None]] = None

        self._bind_events()

    def _create_text_widget(self) -> None:
        """Create and configure the main text widget."""
        self.text = tk.Text(
            self.parent_frame,
            font=MAIN_TEXT_FONT,
            wrap="word",
            height=4,
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,  # Cursor color
            relief="flat",
            padx=8,  # Minimal padding
            pady=8,
            bd=0,  # Remove border
        )
        self.text.pack(fill="both", expand=True)

        # Remove the default highlight colors and borders
        self.text.configure(
            highlightthickness=0,  # Remove highlight border
            selectbackground="#404040",
            selectforeground=self.fg_color,
        )

        # Ensure focus
        self.text.focus_set()

    def _bind_events(self) -> None:
        """Bind text change events."""
        self.text.bind("<KeyRelease>", self._on_text_change)
        self.text.bind("<Button-1>", self._on_text_change)

    def _on_text_change(self, event=None) -> None:
        """Handle text change events."""
        content = self.get_text()
        has_text = bool(content.strip())

        # Update overlay state
        self.overlay_manager.update_for_text_content(has_text)

        # Call external callback if set
        if self.on_text_change:
            self.on_text_change(content)

    def get_text(self) -> str:
        """Get current text content."""
        return self.text.get("1.0", "end-1c")

    def set_text(self, text: str) -> None:
        """Set text content."""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self._on_text_change()  # Update overlays

    def clear_text(self) -> None:
        """Clear all text."""
        self.text.delete("1.0", "end")
        self._on_text_change()  # Update overlays

    def insert_text(self, text: str, position: str = "insert") -> None:
        """Insert text at specified position."""
        self.text.insert(position, text)
        self._on_text_change()  # Update overlays

    def insert_text_smart_spacing(self, text: str) -> None:
        """Insert text with smart spacing logic."""
        cursor_pos = self.text.index("insert")
        text_to_insert = text.strip()

        # Check if we need to add a space before the text
        if cursor_pos != "1.0":  # Not at the beginning of the text
            char_before = self.text.get(f"{cursor_pos}-1c", cursor_pos)
            if char_before and char_before not in [" ", "\n", "\t"]:
                text_to_insert = " " + text_to_insert

        self.insert_text(text_to_insert)

    def bind_key(self, key_combination: str, callback: Callable) -> None:
        """Bind a key combination to a callback."""
        self.text.bind(key_combination, callback)

    def set_processing_state(
        self, is_processing: bool, message: str = "✨ Improving with AI..."
    ) -> None:
        """Set widget to processing state (disabled with message)."""
        if is_processing:
            # Save original styling
            self._original_bg = self.text.cget("bg")
            self._original_cursor = self.text.cget("insertbackground")

            # Clear text and show waiting message
            self.set_text(message)
            self.text.configure(
                bg="#3a3a3a",  # Slightly lighter background
                insertbackground="#888888",  # Dimmed cursor
            )
            self.text.config(state="disabled")  # Disable editing while processing
        else:
            # Restore editing and original styling
            self.text.config(state="normal")
            if hasattr(self, "_original_bg"):
                self.text.configure(
                    bg=self._original_bg, insertbackground=self._original_cursor
                )

    def focus_set(self) -> None:
        """Set focus to the text widget."""
        self.text.focus_set()

    def index(self, position: str) -> str:
        """Get index for a position."""
        return self.text.index(position)

    def get_char_at(self, position: str) -> str:
        """Get character at specific position."""
        return self.text.get(position, f"{position}+1c")

    # Overlay management methods
    def show_empty_state(self) -> None:
        """Show empty state overlay."""
        self.overlay_manager.show_empty_state()

    def show_recording_overlay(self) -> None:
        """Show recording state overlay."""
        self.overlay_manager.show_recording()

    def show_recording_tail_overlay(self) -> None:
        """Show recording tail state overlay."""
        self.overlay_manager.show_recording_tail()

    def show_processing_overlay(self) -> None:
        """Show processing state overlay."""
        self.overlay_manager.show_processing()

    def hide_all_overlays(self) -> None:
        """Hide all overlays."""
        self.overlay_manager.hide_all_overlays()
