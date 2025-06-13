"""UI overlay components for different application states."""

import random
import tkinter as tk
from typing import Optional


class OverlayManager:
    """Manages different overlay states for the text widget."""

    # Random placeholder messages with personality
    PLACEHOLDER_MESSAGES = [
        "What's on your mind?",
        "Spill the tea...",
        "Your thoughts are safe with me",
        "What are you scheming?",
        "Drop your wisdom here",
        "Tell me your secrets",
        "What's brewing in there?",
        "Share your brain dump",
        "I'm all ears... well, pixels",
        "Whisper your ideas to me",
        "What's the latest gossip?",
        "Pour your heart out",
        "Hit me with your best thought",
        "What's rattling around up there?",
        "Feed me your thoughts",
        "I promise I won't judge",
        "What's the word?",
        "Penny for your thoughts?",
        "What's keeping you up?",
        "Let's hear it, genius",
    ]

    def __init__(self, parent_frame: tk.Frame):
        self.parent_frame = parent_frame
        self.bg_color = "#2b2b2b"

        # Initialize all overlays
        self._create_empty_state_overlay()
        self._create_recording_overlay()
        self._create_processing_overlay()

        # Track current state
        self.current_overlay: Optional[tk.Widget] = None

    def _create_empty_state_overlay(self) -> None:
        """Create empty state placeholder overlay."""
        self.empty_state_overlay = tk.Label(
            self.parent_frame,
            text=random.choice(self.PLACEHOLDER_MESSAGES),
            font=("Helvetica", 16, "italic"),
            fg="#666666",
            bg=self.bg_color,
            justify="center",
        )

    def _create_recording_overlay(self) -> None:
        """Create recording state overlay."""
        self.recording_overlay = tk.Frame(
            self.parent_frame,
            bg="#4d2626",  # Dark red background
            relief="solid",
            bd=2,
            highlightbackground="#ff6666",
            highlightcolor="#ff6666",
            highlightthickness=2,
        )

        self.recording_label = tk.Label(
            self.recording_overlay,
            text="🎤 Recording... (release Tab to stop)",
            font=("Helvetica", 18, "bold"),
            fg="#ff9999",
            bg="#4d2626",
            justify="center",
        )
        self.recording_label.pack(expand=True)

    def _create_processing_overlay(self) -> None:
        """Create processing state overlay."""
        self.processing_overlay = tk.Frame(
            self.parent_frame,
            bg="#264d4d",  # Dark blue background
            relief="solid",
            bd=2,
            highlightbackground="#6699ff",
            highlightcolor="#6699ff",
            highlightthickness=2,
        )

        self.processing_label = tk.Label(
            self.processing_overlay,
            text="🧠 Processing audio...",
            font=("Helvetica", 18, "bold"),
            fg="#99ccff",
            bg="#264d4d",
            justify="center",
        )
        self.processing_label.pack(expand=True)

    def hide_all_overlays(self) -> None:
        """Hide all overlay widgets."""
        self.empty_state_overlay.place_forget()
        self.recording_overlay.place_forget()
        self.processing_overlay.place_forget()
        self.current_overlay = None

    def show_empty_state(self) -> None:
        """Show empty state overlay with a fresh random message."""
        self.hide_all_overlays()

        # Update with fresh random message
        self.empty_state_overlay.config(
            text=random.choice(self.PLACEHOLDER_MESSAGES),
            fg="#666666",
            bg=self.bg_color,
        )
        self.empty_state_overlay.place(relx=0.5, rely=0.4, anchor="center")
        self.current_overlay = self.empty_state_overlay

    def show_recording(self) -> None:
        """Show recording state overlay."""
        self.hide_all_overlays()

        # Reset to normal recording state
        self.recording_label.config(
            text="🎤 Recording... (release Tab to stop)",
            fg="#ff9999",
        )

        self.recording_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)
        self.current_overlay = self.recording_overlay

    def show_recording_tail(self) -> None:
        """Show recording tail state (finishing up recording)."""
        # Update the recording label to show tail state
        self.recording_label.config(
            text="🎤 Finishing recording...",
            fg="#ffaa99",  # Slightly dimmer red to indicate tail period
        )

        # Keep the recording overlay visible
        self.recording_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)
        self.current_overlay = self.recording_overlay

    def show_processing(self) -> None:
        """Show processing state overlay."""
        self.hide_all_overlays()

        self.processing_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)
        self.current_overlay = self.processing_overlay

    def update_for_text_content(self, has_text: bool) -> None:
        """Update overlay visibility based on whether text widget has content."""
        if has_text:
            # Hide all overlays when there's text
            self.hide_all_overlays()
        else:
            # Show empty state overlay when text is empty (unless we're in recording/processing)
            if self.current_overlay not in [
                self.recording_overlay,
                self.processing_overlay,
            ]:
                self.show_empty_state()


class TooltipManager:
    """Manages info icon and contextual tooltips."""

    def __init__(self, parent_frame: tk.Frame, root: tk.Tk):
        self.parent_frame = parent_frame
        self.root = root
        self.bg_color = "#2b2b2b"

        self.tooltip_window: Optional[tk.Toplevel] = None
        self.tooltip_label: Optional[tk.Label] = None

        self._create_info_icon()

    def _create_info_icon(self) -> None:
        """Create info icon in bottom right corner."""
        self.info_frame = tk.Frame(self.parent_frame, bg=self.bg_color)
        self.info_frame.pack(side="bottom", anchor="se", pady=(0, 2))

        self.info_icon = tk.Label(
            self.info_frame,
            text="ⓘ",
            font=("Helvetica", 12),
            fg="#666666",  # Subtle gray
            bg=self.bg_color,
            cursor="hand2",
        )
        self.info_icon.pack()

        # Bind tooltip events
        self.info_icon.bind("<Enter>", self.show_tooltip)
        self.info_icon.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None) -> None:
        """Show tooltip with hotkey information."""
        if self.tooltip_window:
            return

        # Position tooltip relative to info icon
        x = self.info_icon.winfo_rootx() + 20
        y = self.info_icon.winfo_rooty() - 150

        self.tooltip_window = tk.Toplevel(self.root)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Create tooltip content
        tooltip_text = self._generate_tooltip_text()

        self.tooltip_label = tk.Label(
            self.tooltip_window,
            text=tooltip_text,
            font=("Helvetica", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            justify="left",
        )
        self.tooltip_label.pack()

    def _generate_tooltip_text(self) -> str:
        """Generate contextual tooltip text based on configuration."""
        from config import config

        tooltip_text = "Hotkeys:\n"
        tooltip_text += "• Ctrl+Enter / Ctrl+D — Save and exit\n"
        tooltip_text += "• Ctrl+S — Open settings\n"

        if config.llm_enabled:
            tooltip_text += "• Ctrl+I — Improve with AI\n"
            tooltip_text += "• Ctrl+L — Curator feedback\n"
            tooltip_text += "• Ctrl+Z — Undo improvement\n"

        tooltip_text += "• Escape — Exit without saving"

        # Add LLM status
        llm_status = "✅ AI enabled" if config.llm_enabled else "⚠️ AI disabled"
        tooltip_text += f"\n\n{llm_status}"

        return tooltip_text

    def hide_tooltip(self, event=None) -> None:
        """Hide tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            self.tooltip_label = None
