"""Main application controller that coordinates all components."""

import subprocess
import tkinter as tk

from config import config
from core.note_manager import NoteManager
from curator.curator import CuratorManager
from ui.overlays import TooltipManager
from ui.text_widget import QuipTextWidget
from ui.window_manager import WindowManager
from voice.voice_handler import VoiceHandler


class QuipApplication:
    """Main application controller that coordinates all components."""

    def __init__(self):
        # Initialize Tkinter root
        self.root = tk.Tk()
        self.root.title("Quip")

        # Initialize core components
        self.window_manager = WindowManager(self.root)
        self.note_manager = NoteManager()
        self.voice_handler = VoiceHandler()

        # Initialize UI
        self._setup_ui()

        # Initialize managers that depend on UI
        self.curator_manager = CuratorManager(self.main_frame, self.window_manager)
        self.tooltip_manager = TooltipManager(self.main_frame, self.root)

        # Connect components
        self._connect_components()

        # Setup window and show
        self._finalize_setup()

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Configure window
        self.window_manager.setup_window_properties()

        # Dark mode colors
        bg_color = "#2b2b2b"

        # Configure the root window background
        self.root.configure(bg=bg_color)

        # Create a main frame for padding
        self.main_frame = tk.Frame(self.root, bg=bg_color)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create enhanced text widget
        self.text_widget = QuipTextWidget(self.main_frame)

        # Position window
        self.window_manager.position_window_centered()

    def _connect_components(self) -> None:
        """Connect all components with appropriate callbacks."""
        # Connect voice handler callbacks
        self.voice_handler.on_recording_start = self.text_widget.show_recording_overlay
        self.voice_handler.on_recording_tail_start = (
            self.text_widget.show_recording_tail_overlay
        )
        self.voice_handler.on_transcription_start = (
            self.text_widget.show_processing_overlay
        )
        self.voice_handler.on_transcription_complete = self._on_transcription_complete
        self.voice_handler.on_transcription_error = self._on_transcription_error

        # Connect text widget key bindings
        self._setup_key_bindings()

    def _setup_key_bindings(self) -> None:
        """Set up all keyboard shortcuts."""
        # Core functionality
        self.text_widget.bind_key("<Control-Return>", self._save_and_exit)
        self.text_widget.bind_key("<Control-d>", self._save_and_exit)
        self.text_widget.bind_key("<Control-s>", self._open_settings)
        self.text_widget.bind_key("<Escape>", lambda e: self.root.destroy())

        # LLM functionality
        self.text_widget.bind_key("<Control-i>", self._improve_note)
        self.text_widget.bind_key("<Control-z>", self._undo_improvement)
        self.text_widget.bind_key("<Control-l>", self._toggle_curator_mode)

        # Voice recording
        self.text_widget.bind_key("<KeyPress-Tab>", self._on_tab_press)
        self.text_widget.bind_key("<KeyRelease-Tab>", self._on_tab_release)

        # Window manager protocol
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _finalize_setup(self) -> None:
        """Finalize setup and show window."""
        # Show window after everything is configured
        self.window_manager.show_window()

        # Set initial focus
        self.text_widget.focus_set()

    # Event handlers
    def _save_and_exit(self, event) -> None:
        """Save note and exit application."""
        note_text = self.text_widget.get_text()

        # Save if there's actual text content
        if note_text.strip():
            success = self.note_manager.save_note(note_text)
            if config.debug_mode:
                if success:
                    print(f"DEBUG: Note saved to {self.note_manager.get_save_path()}")
                else:
                    print("DEBUG: Failed to save note")

        self.root.destroy()

    def _open_settings(self, event=None) -> None:
        """Open settings file in default editor and close Quip."""
        try:
            # Open config file with default editor
            subprocess.Popen(
                ["xdg-open", str(config.config_file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if config.debug_mode:
                print(f"DEBUG: Opening settings: {config.config_file_path}")
        except Exception as e:
            if config.debug_mode:
                print(f"DEBUG: Failed to open settings: {e}")

        # Close current Quip window so fresh config loads on next spawn
        self.root.destroy()

    def _improve_note(self, event=None) -> None:
        """Improve the current note using LLM."""
        current_text = self.text_widget.get_text().strip()
        if not current_text:
            return

        # Set processing state
        self.text_widget.set_processing_state(True)
        self.root.update_idletasks()

        # Attempt improvement
        success, result = self.curator_manager.improve_note(current_text)

        # Restore normal state
        self.text_widget.set_processing_state(False)

        if success:
            # Replace with improved text
            self.text_widget.set_text(result)
        else:
            # Restore original text on error
            self.text_widget.set_text(current_text)

    def _undo_improvement(self, event=None) -> None:
        """Undo the last LLM improvement."""
        success, result = self.curator_manager.undo_improvement()

        if success:
            self.text_widget.set_text(result)

    def _toggle_curator_mode(self, event=None) -> None:
        """Toggle curator feedback mode."""
        current_text = self.text_widget.get_text().strip()
        if not current_text:
            return

        self.curator_manager.toggle_curator_mode(current_text)

    def _on_tab_press(self, event) -> str:
        """Handle Tab key press for voice recording."""
        should_break, action = self.voice_handler.on_tab_press()

        if action == "start_timing":
            # Schedule hold check after threshold
            self.root.after(
                int(self.voice_handler.tab_hold_threshold * 1000),
                self.voice_handler.check_tab_hold,
            )

        return "break" if should_break else None

    def _on_tab_release(self, event) -> str:
        """Handle Tab key release for voice recording."""
        should_break, action = self.voice_handler.on_tab_release()

        if action == "process_release":
            # Don't process release immediately if we're in recording mode
            if self.voice_handler.recording_mode:
                # Schedule a delayed check to see if we should stop recording
                self.root.after(
                    int(self.voice_handler.release_debounce_time * 1000),
                    self._check_tab_release_final,
                )
            else:
                # Process immediate release for short taps
                action_result = self.voice_handler.process_immediate_tab_release()
                if action_result == "insert_tab":
                    # Insert tab character
                    self.text_widget.insert_text("\t")

        return "break" if should_break else None

    def _check_tab_release_final(self) -> None:
        """Check if tab is still released after debounce period."""
        self.voice_handler.process_tab_release_after_debounce()

        # Schedule actual stop after tail period if needed
        if self.voice_handler.recording_tail_active:
            self.root.after(
                int(self.voice_handler.recording_tail_time * 1000),
                self.voice_handler.stop_recording_tail,
            )

    def _on_transcription_complete(self, transcribed_text: str) -> None:
        """Handle successful transcription."""

        def update_text():
            if transcribed_text.strip():
                self.text_widget.insert_text_smart_spacing(transcribed_text)
            else:
                # Just update to normal state if no text
                self.text_widget.hide_all_overlays()

        # Update UI in main thread
        self.root.after(0, update_text)

    def _on_transcription_error(self, error_message: str) -> None:
        """Handle transcription error."""

        def update_text():
            # Don't insert error text, just reset to normal empty state
            self.text_widget.hide_all_overlays()

        # Update UI in main thread
        self.root.after(0, update_text)

    def run(self) -> None:
        """Start the application main loop."""
        self.root.mainloop()
