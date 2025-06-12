import tkinter as tk
from pathlib import Path
import subprocess
import re
import sys
import time
import threading

from config import config
from voice_recorder import VoiceRecorder
from transcription import create_transcription_service

# Handle tomli import for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

note_delimiter = "---"


class QuickNote:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quip")
        self.text_before_improvement = None  # Store text before LLM improvement
        self.curator_mode = False  # Track if curator feedback is shown
        self.original_height = None  # Store original window height
        self.current_curator_feedback = (
            None  # Store current curator feedback for context
        )

        # Voice recording state
        self.tab_press_time = None
        self.tab_hold_threshold = (
            config.voice_hold_threshold_ms / 1000.0
        )  # Convert to seconds
        self.recording_mode = False
        self.tab_physically_pressed = False  # Track physical key state
        self.tab_consumed_as_hold = False  # Track if this press was used for recording
        self.tab_release_time = None  # Track when tab was released
        self.release_debounce_time = 0.1  # 100ms debounce for rapid press/release
        self.recording_tail_time = (
            config.voice_recording_tail_ms / 1000.0
        )  # Convert to seconds
        self.recording_tail_active = False  # Track if we're in the tail period

        # Initialize audio feedback paths
        self.init_audio()

        # Initialize voice recording and transcription
        self.voice_recorder = VoiceRecorder()
        self.transcription_service = create_transcription_service(
            model_size=config.voice_model_size, language=config.voice_language
        )

        # Set up voice recording callbacks
        self.voice_recorder.on_recording_start = self.on_voice_recording_start
        self.voice_recorder.on_recording_stop = self.on_voice_recording_stop

        # Set up transcription callbacks
        self.transcription_service.on_transcription_start = self.on_transcription_start
        self.transcription_service.on_transcription_complete = (
            self.on_transcription_complete
        )
        self.transcription_service.on_transcription_error = self.on_transcription_error

        # Initialize transcription service asynchronously
        self.transcription_service.initialize_async()

        # Hide window initially to prevent flash
        self.root.withdraw()

        # Try different approach for borderless window
        try:
            # Linux/X11 specific attributes for borderless window
            self.root.wm_attributes(
                "-type", "splash"
            )  # Splash windows have no decorations
        except tk.TclError:
            try:
                # Alternative approach
                self.root.wm_attributes(
                    "-toolwindow", True
                )  # Tool windows (Windows-specific)
            except tk.TclError:
                pass

        # Keep topmost behavior
        self.root.attributes("-topmost", True)

        # Try to add rounded corners (Linux-specific)
        try:
            # Some window managers support rounded corners via window properties
            self.root.wm_attributes(
                "-alpha", config.transparency
            )  # Slight transparency can help with antialiasing
        except tk.TclError:
            pass

        # Dark mode colors
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"

        # Set window size and position (centered on primary monitor)
        window_width = config.window_width
        window_height = config.window_height
        self.original_height = window_height  # Store for expansion/collapse

        # Get monitor dimensions and find current monitor
        self.root.update_idletasks()  # Ensure window is ready
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        pointer_x = self.root.winfo_pointerx()
        pointer_y = self.root.winfo_pointery()

        # Try to detect actual monitor configuration using xrandr
        monitors = self.detect_monitors()

        if config.debug_mode:
            print(f"DEBUG: screen_width={screen_width}, screen_height={screen_height}")
            print(f"DEBUG: pointer x={pointer_x}, pointer y={pointer_y}")
            print(f"DEBUG: Detected monitors: {monitors}")

        # Find which monitor the cursor is on
        current_monitor = None
        for monitor in monitors:
            x, y, w, h = monitor["x"], monitor["y"], monitor["width"], monitor["height"]
            if config.debug_mode:
                print(
                    f"DEBUG: Checking if cursor ({pointer_x}, {pointer_y}) is in monitor {monitor['name']}: x={x}-{x + w}, y={y}-{y + h}"
                )
            if x <= pointer_x < x + w and y <= pointer_y < y + h:
                current_monitor = monitor
                break

        if current_monitor:
            monitor_start_x = current_monitor["x"]
            monitor_start_y = current_monitor["y"]
            monitor_width = current_monitor["width"]
            monitor_height = current_monitor["height"]
        else:
            # Cursor is in a gap between monitors or monitor not detected
            # Try to infer monitor size and position based on cursor location
            if len(monitors) >= 2 and screen_width > 4000:
                # Multi-monitor setup with gaps - estimate monitor size
                typical_width = 2560  # Common monitor width
                estimated_monitor = pointer_x // typical_width
                monitor_start_x = estimated_monitor * typical_width
                monitor_start_y = 0
                monitor_width = typical_width
                monitor_height = screen_height
            else:
                # Fallback to simple centering across all screens
                monitor_width = screen_width
                monitor_height = screen_height
                monitor_start_x = 0
                monitor_start_y = 0

        # Center on the current monitor
        center_x = monitor_start_x + int(monitor_width / 2 - window_width / 2)
        center_y = monitor_start_y + int(monitor_height / 2 - window_height / 2)

        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # Configure the root window background
        self.root.configure(bg=bg_color)

        # Create a main frame for padding
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create and configure the text widget with minimal padding
        self.text = tk.Text(
            main_frame,
            font=("Helvetica", 14),
            wrap="word",
            height=4,
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,  # Cursor color
            relief="flat",
            padx=8,  # Minimal padding
            pady=8,
            bd=0,  # Remove border
        )
        self.text.pack(fill="both", expand=True)

        # Random placeholder messages with personality
        self.placeholder_messages = [
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

        # Create overlay for empty state message
        import random

        self.empty_state_overlay = tk.Label(
            main_frame,
            text=random.choice(self.placeholder_messages),
            font=("Helvetica", 16, "italic"),
            fg="#666666",
            bg=bg_color,
            justify="center",
        )
        # Position overlay in center of text area
        self.empty_state_overlay.place(relx=0.5, rely=0.4, anchor="center")

        # Create recording overlay frame (covers most of the text area)
        self.recording_overlay = tk.Frame(
            main_frame,
            bg="#4d2626",  # Dark red background
            relief="solid",
            bd=2,
            highlightbackground="#ff6666",
            highlightcolor="#ff6666",
            highlightthickness=2,
        )

        # Create recording label inside the overlay
        self.recording_label = tk.Label(
            self.recording_overlay,
            text="🎤 Recording... (release Tab to stop)",
            font=("Helvetica", 18, "bold"),
            fg="#ff9999",
            bg="#4d2626",
            justify="center",
        )
        self.recording_label.pack(expand=True)

        # Create processing overlay frame (covers most of the text area)
        self.processing_overlay = tk.Frame(
            main_frame,
            bg="#264d4d",  # Dark blue background
            relief="solid",
            bd=2,
            highlightbackground="#6699ff",
            highlightcolor="#6699ff",
            highlightthickness=2,
        )

        # Create processing label inside the overlay
        self.processing_label = tk.Label(
            self.processing_overlay,
            text="🧠 Processing audio...",
            font=("Helvetica", 18, "bold"),
            fg="#99ccff",
            bg="#264d4d",
            justify="center",
        )
        self.processing_label.pack(expand=True)

        # Create info icon frame (positioned in bottom right)
        self.info_frame = tk.Frame(main_frame, bg=bg_color)
        self.info_frame.pack(side="bottom", anchor="se", pady=(0, 2))

        # Create info icon
        self.info_icon = tk.Label(
            self.info_frame,
            text="ⓘ",
            font=("Helvetica", 12),
            fg="#666666",  # Subtle gray
            bg=bg_color,
            cursor="hand2",
        )
        self.info_icon.pack()

        # Create tooltip (initially hidden)
        self.tooltip = None
        self.tooltip_window = None

        # Create curator feedback area (initially hidden)
        self.curator_frame = tk.Frame(main_frame, bg=bg_color)

        # Add a subtle divider
        divider = tk.Frame(self.curator_frame, bg="#404040", height=1)
        divider.pack(fill="x", pady=(5, 5))

        # Curator feedback text area (read-only)
        self.curator_text = tk.Text(
            self.curator_frame,
            font=("Helvetica", 12),
            wrap="word",
            height=6,
            bg="#1e1e1e",  # Slightly darker than main
            fg="#cccccc",  # Slightly dimmer text
            relief="flat",
            padx=8,
            pady=8,
            bd=0,
            state="disabled",  # Read-only
        )
        self.curator_text.pack(fill="both", expand=True, pady=(0, 5))

        # Configure curator text colors
        self.curator_text.configure(
            highlightthickness=0,
            selectbackground="#303030",
            selectforeground="#cccccc",
        )

        # Remove the default highlight colors and borders
        self.text.configure(
            highlightthickness=0,  # Remove highlight border
            selectbackground="#404040",
            selectforeground=fg_color,
        )

        # Bind events
        self.text.bind("<Control-Return>", self.save_and_exit)
        self.text.bind("<Control-d>", self.save_and_exit)
        self.text.bind("<Control-s>", self.open_settings)
        self.text.bind("<Control-i>", self.improve_note)
        self.text.bind("<Control-z>", self.undo_improvement)
        self.text.bind("<Control-l>", self.toggle_curator_mode)
        self.text.bind("<Escape>", lambda e: self.root.destroy())

        # Bind tab events for voice recording
        self.text.bind("<KeyPress-Tab>", self.on_tab_press)
        self.text.bind("<KeyRelease-Tab>", self.on_tab_release)
        self.text.focus_set()  # Ensure focus for key events

        # Bind text change events to update empty state overlay
        self.text.bind("<KeyRelease>", self.update_empty_state)
        self.text.bind("<Button-1>", self.update_empty_state)

        # Bind tooltip events
        self.info_icon.bind("<Enter>", self.show_tooltip)
        self.info_icon.bind("<Leave>", self.hide_tooltip)

        # Show window after everything is configured
        self.root.deiconify()

        # Ensure proper focus
        self.root.after(100, self.ensure_focus)

        # Bind window manager delete window protocol
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def detect_monitors(self):
        """Detect monitor configuration using xrandr on Linux"""
        try:
            # Try xrandr first (most common on Linux)
            result = subprocess.run(
                ["xrandr"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return self.parse_xrandr_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: return single monitor based on tkinter values
        return [
            {
                "name": "default",
                "x": 0,
                "y": 0,
                "width": self.root.winfo_screenwidth(),
                "height": self.root.winfo_screenheight(),
            }
        ]

    def parse_xrandr_output(self, output):
        """Parse xrandr output to get monitor positions and sizes"""
        monitors = []
        lines = output.split("\n")

        for line in lines:
            # Look for lines like: "DP-2 connected 2560x1440+2560+0" or "DP-4 connected primary 2560x1440+1920+0"
            match = re.search(
                r"^(\S+)\s+connected\s+(?:primary\s+)?(\d+)x(\d+)\+(\d+)\+(\d+)", line
            )
            if match:
                name, width, height, x, y = match.groups()
                monitors.append(
                    {
                        "name": name,
                        "x": int(x),
                        "y": int(y),
                        "width": int(width),
                        "height": int(height),
                    }
                )

        return (
            monitors
            if monitors
            else [
                {
                    "name": "default",
                    "x": 0,
                    "y": 0,
                    "width": self.root.winfo_screenwidth(),
                    "height": self.root.winfo_screenheight(),
                }
            ]
        )

    def ensure_focus(self):
        """Ensure window has proper focus"""
        self.root.lift()  # Lift the window to the top
        self.root.focus_force()  # Force focus to the window
        self.text.focus_set()  # Set focus to the text widget

    def update_empty_state(self, event=None):
        """Update empty state overlay visibility based on text content"""
        current_text = self.text.get("1.0", "end-1c").strip()
        if current_text:
            # Hide all overlays when there's text
            self.empty_state_overlay.place_forget()
            self.recording_overlay.place_forget()
            self.processing_overlay.place_forget()
        else:
            # Hide recording/processing overlays
            self.recording_overlay.place_forget()
            self.processing_overlay.place_forget()

            # Show empty state overlay when text is empty with a fresh random message
            import random

            self.empty_state_overlay.config(
                text=random.choice(self.placeholder_messages),
                fg="#666666",  # Reset to default gray
                bg="#2b2b2b",  # Reset to default background
            )
            self.empty_state_overlay.place(relx=0.5, rely=0.4, anchor="center")

    def show_recording_overlay(self):
        """Show recording state with red box overlay"""
        # Hide other overlays
        self.empty_state_overlay.place_forget()
        self.processing_overlay.place_forget()

        # Reset recording label to normal recording state
        self.recording_label.config(
            text="🎤 Recording... (release Tab to stop)",
            fg="#ff9999",  # Normal red color
        )

        # Show recording overlay covering most of the text area
        self.recording_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)

    def show_recording_tail_overlay(self):
        """Show recording tail state (finishing up recording)"""
        # Update the recording label to show tail state
        self.recording_label.config(
            text="🎤 Finishing recording...",
            fg="#ffaa99",  # Slightly dimmer red to indicate tail period
        )

        # Keep the recording overlay visible
        self.recording_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)

    def show_processing_overlay(self):
        """Show processing state with blue box overlay"""
        # Hide other overlays
        self.empty_state_overlay.place_forget()
        self.recording_overlay.place_forget()

        # Show processing overlay covering most of the text area
        self.processing_overlay.place(x=10, y=10, relwidth=0.97, relheight=0.85)

    def show_tooltip(self, event=None):
        """Show tooltip with hotkey information"""
        if self.tooltip_window:
            return

        x = self.info_icon.winfo_rootx() + 20
        y = self.info_icon.winfo_rooty() - 150

        self.tooltip_window = tk.Toplevel(self.root)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Create tooltip content
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

        self.tooltip = tk.Label(
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
        self.tooltip.pack()

    def hide_tooltip(self, event=None):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            self.tooltip = None

    def open_settings(self, event=None):
        """Open settings file in default editor and close Quip"""
        try:
            import subprocess

            # Open config file with default editor
            subprocess.Popen(
                ["xdg-open", str(config.config_file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if config.debug_mode:
                print(f"Opening settings: {config.config_file_path}")
        except Exception as e:
            if config.debug_mode:
                print(f"Failed to open settings: {e}")

        # Close current Quip window so fresh config loads on next spawn
        self.root.destroy()

    def undo_improvement(self, event=None):
        """Undo the last LLM improvement and restore original text"""
        if self.text_before_improvement is None:
            if config.debug_mode:
                print("DEBUG: No previous text to restore")
            return

        # Restore the text before improvement
        self.text.delete("1.0", "end")
        self.text.insert("1.0", self.text_before_improvement)

        # Update empty state overlay
        self.update_empty_state()

        # Clear the stored text (only allow one undo)
        self.text_before_improvement = None

        if config.debug_mode:
            print("DEBUG: Restored text before improvement")

    def improve_note(self, event=None):
        """Improve the current note using LLM"""
        if not config.llm_enabled:
            if config.debug_mode:
                print("DEBUG: LLM not enabled")
            return

        current_text = self.text.get("1.0", "end-1c").strip()
        if not current_text:
            if config.debug_mode:
                print("DEBUG: No text to improve")
            return

        try:
            from llm import llm_client, LLMError

            # Store original text for undo functionality
            self.text_before_improvement = current_text

            # Save original text and styling
            original_bg = self.text.cget("bg")
            original_cursor = self.text.cget("insertbackground")

            # Clear text and show waiting message
            self.text.delete("1.0", "end")
            self.text.insert("1.0", "✨ Improving with AI...")
            self.text.configure(
                bg="#3a3a3a",  # Slightly lighter background
                insertbackground="#888888",  # Dimmed cursor
            )
            self.text.config(state="disabled")  # Disable editing while processing
            self.root.update_idletasks()

            # Pass curator feedback as context if available
            curator_context = (
                self.current_curator_feedback if self.curator_mode else None
            )
            improved_text = llm_client.improve_note(current_text, curator_context)

            # Restore editing and replace with improved text
            self.text.config(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", improved_text)

            # Restore original styling
            self.text.configure(bg=original_bg, insertbackground=original_cursor)

            # Update empty state overlay
            self.update_empty_state()

            # Clear curator mode after improvement
            self.clear_curator_mode()

            if config.debug_mode:
                print("DEBUG: Note improved successfully")

        except LLMError as e:
            # Restore text and styling on error
            self.text.config(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", current_text)  # Restore original text
            self.text.configure(bg=original_bg, insertbackground=original_cursor)
            # Clear stored text since improvement failed
            self.text_before_improvement = None
            if config.debug_mode:
                print(f"DEBUG: LLM error: {e}")
        except Exception as e:
            # Restore text and styling on unexpected error
            self.text.config(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", current_text)  # Restore original text
            self.text.configure(bg=original_bg, insertbackground=original_cursor)
            # Clear stored text since improvement failed
            self.text_before_improvement = None
            if config.debug_mode:
                print(f"DEBUG: Unexpected error during improvement: {e}")

    def toggle_curator_mode(self, event=None):
        """Toggle curator feedback mode and get feedback for current note"""
        if not config.llm_enabled:
            if config.debug_mode:
                print("DEBUG: LLM not enabled for curator mode")
            return

        current_text = self.text.get("1.0", "end-1c").strip()
        if not current_text:
            if config.debug_mode:
                print("DEBUG: No text to curate")
            return

        if not self.curator_mode:
            # Show curator mode and get feedback
            self.show_curator_feedback(current_text)
        else:
            # Already in curator mode, refresh feedback
            self.show_curator_feedback(current_text)

    def show_curator_feedback(self, text):
        """Show curator feedback area and get LLM feedback"""
        try:
            from llm import LLMError

            # Show loading state in curator area
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", "🤔 Analyzing your note...")
            self.curator_text.config(state="disabled")

            # Show curator frame if not already visible
            if not self.curator_mode:
                self.curator_frame.pack(fill="both", expand=True, pady=(5, 0))
                self.expand_window()
                self.curator_mode = True

            self.root.update_idletasks()

            # Get curator feedback
            feedback = self.get_curator_feedback(text)

            # Update curator area with feedback
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", feedback)
            self.curator_text.config(state="disabled")

            # Store feedback for context in improvements
            self.current_curator_feedback = feedback

            if config.debug_mode:
                print("DEBUG: Curator feedback displayed")

        except LLMError as e:
            # Show error in curator area
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", f"❌ Error getting feedback: {e}")
            self.curator_text.config(state="disabled")
            if config.debug_mode:
                print(f"DEBUG: Curator LLM error: {e}")
        except Exception as e:
            # Show error in curator area
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", f"❌ Unexpected error: {e}")
            self.curator_text.config(state="disabled")
            if config.debug_mode:
                print(f"DEBUG: Curator unexpected error: {e}")

    def get_curator_feedback(self, text):
        """Get curator feedback from LLM"""
        from llm import llm_client, LLMError

        prompt = """You are a thoughtful note-taking curator helping someone capture clear, actionable thoughts. 

This person just captured a quick note. In 2-3 short questions or observations, help them clarify what's important about this note. Be concise and actionable.

Examples:
- "What's the specific next action here?"
- "Is there a deadline or timeline?"
- "Who else needs to know about this?"
- "What context would help you remember this later?"

Keep it brief and helpful."""

        messages = [
            {
                "role": "system",
                "content": "You are a helpful note-taking curator. Provide 2-3 short questions or observations to help improve notes. Be concise and actionable.",
            },
            {"role": "user", "content": f"{prompt}\n\nNote: {text}"},
        ]

        request_data = {
            "model": config.llm_model,
            "messages": messages,
            "max_tokens": config.llm_max_tokens,
            "temperature": config.llm_temperature,
        }

        if config.debug_mode:
            print("DEBUG: Getting curator feedback")
            print(f"DEBUG: Note text: '{text}'")

        response = llm_client._make_request("chat/completions", request_data)

        if "choices" not in response or not response["choices"]:
            raise LLMError("No response choices returned from API")

        content = response["choices"][0]["message"]["content"]
        return content.strip()

    def expand_window(self):
        """Expand window to show curator area"""
        if self.original_height is None:
            return

        # Expand height to accommodate curator area
        expanded_height = self.original_height + 200  # Add space for curator area

        # Get current window position
        current_geometry = self.root.geometry()
        width_height, x_y = current_geometry.split("+", 1)
        width, height = width_height.split("x")
        x, y = x_y.split("+")

        # Update geometry with new height
        new_geometry = f"{width}x{expanded_height}+{x}+{y}"
        self.root.geometry(new_geometry)

        if config.debug_mode:
            print(f"DEBUG: Expanded window from {height} to {expanded_height}")

    def clear_curator_mode(self):
        """Clear curator mode and hide feedback area"""
        if self.curator_mode:
            # Hide curator frame
            self.curator_frame.pack_forget()

            # Restore original window height
            if self.original_height is not None:
                current_geometry = self.root.geometry()
                width_height, x_y = current_geometry.split("+", 1)
                width, height = width_height.split("x")
                x, y = x_y.split("+")

                new_geometry = f"{width}x{self.original_height}+{x}+{y}"
                self.root.geometry(new_geometry)

            # Clear state
            self.curator_mode = False
            self.current_curator_feedback = None

            if config.debug_mode:
                print("DEBUG: Curator mode cleared")

    def init_audio(self):
        """Initialize audio feedback file paths"""
        try:
            sounds_dir = Path(__file__).parent / "sounds"
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

    def play_sound(self, sound_path):
        """Play a sound effect if available"""
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

    def on_tab_press(self, event):
        """Handle Tab key press - start timing for hold detection"""
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
                self.show_recording_overlay()
                if config.debug_mode:
                    print("DEBUG: Cancelled recording tail - back to normal recording")

            return "break"

        # Handle first press of physical key or new press after debounce period
        if not self.tab_physically_pressed:
            if config.debug_mode:
                print("DEBUG: Tab PHYSICALLY pressed (first time)")

            self.tab_press_time = current_time
            self.tab_physically_pressed = True
            self.tab_consumed_as_hold = False
            self.tab_release_time = None  # Clear release time

            # Schedule hold check after threshold
            self.root.after(int(self.tab_hold_threshold * 1000), self.check_tab_hold)
        else:
            # This is a keyboard repeat event - ignore it
            if config.debug_mode:
                print("DEBUG: Tab repeat event - ignoring")

        # Prevent default tab insertion for now
        return "break"

    def on_tab_release(self, event):
        """Handle Tab key release - determine if it was tap or hold"""
        current_time = time.time()

        if config.debug_mode:
            print("DEBUG: Tab PHYSICALLY released")

        if not self.tab_physically_pressed:
            return

        self.tab_physically_pressed = False
        self.tab_release_time = current_time  # Record release time for debouncing

        # Don't process release immediately if we're in recording mode
        # Wait for debounce period to see if it's re-pressed
        if self.recording_mode:
            if config.debug_mode:
                print("DEBUG: Tab released during recording - waiting for debounce")
            # Schedule a delayed check to see if we should stop recording
            self.root.after(
                int(self.release_debounce_time * 1000), self.check_tab_release_final
            )
        else:
            # Process immediate release for short taps
            self.process_tab_release()

        return "break"

    def check_tab_release_final(self):
        """Check if tab is still released after debounce period"""
        if not self.tab_physically_pressed and self.recording_mode:
            # Tab is still released after debounce - start recording tail period
            self.recording_tail_active = True

            if config.debug_mode:
                print(
                    f"DEBUG: Starting recording tail period ({self.recording_tail_time:.1f}s)"
                )

            # Update overlay to show we're in tail period
            self.show_recording_tail_overlay()

            # Schedule actual stop after tail period
            self.root.after(
                int(self.recording_tail_time * 1000), self.stop_recording_tail
            )

    def stop_recording_tail(self):
        """Stop recording after tail period expires"""
        if self.recording_tail_active and not self.tab_physically_pressed:
            # Tab is still released after tail period - actually stop recording
            self.recording_tail_active = False
            self.process_tab_release()
        elif self.tab_physically_pressed:
            # Tab was re-pressed during tail period - cancel tail and continue recording
            self.recording_tail_active = False
            if config.debug_mode:
                print("DEBUG: Tab re-pressed during tail period - continuing recording")
            self.show_recording_overlay()  # Go back to normal recording state

    def process_tab_release(self):
        """Process the actual tab release"""
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
        elif not self.tab_consumed_as_hold and hold_duration < self.tab_hold_threshold:
            # Quick tap - insert tab character
            cursor_pos = self.text.index("insert")
            self.text.insert("insert", "\t")
            new_cursor_pos = self.text.index("insert")
            current_text = self.text.get("1.0", "end-1c")
            if config.debug_mode:
                print(f"DEBUG: Quick tap ({hold_duration:.3f}s) - INSERTED TAB")
                print(f"DEBUG: Cursor moved from {cursor_pos} to {new_cursor_pos}")
                print(f"DEBUG: Text content now: '{repr(current_text)}'")
                print(f"DEBUG: Text length: {len(current_text)}")
        else:
            if config.debug_mode:
                print(
                    f"DEBUG: Hold duration {hold_duration:.3f}s - already handled or too long"
                )

    def check_tab_hold(self):
        """Check if tab is still being held after threshold"""
        if not self.tab_physically_pressed or self.recording_mode:
            return  # Tab was already released or already recording

        if config.debug_mode:
            print("DEBUG: Tab hold detected - starting recording mode")

        self.tab_consumed_as_hold = True  # Mark this press as consumed by hold
        self.start_voice_recording()

    def start_voice_recording(self):
        """Start voice recording mode with visual feedback"""
        if self.recording_mode:
            return

        self.recording_mode = True

        # Audio feedback: play start sound
        self.play_sound(self.sound_record_start)

        # Visual feedback: show recording overlay
        self.show_recording_overlay()

        # Start actual voice recording
        success = self.voice_recorder.start_recording()
        if not success:
            if config.debug_mode:
                print(
                    "DEBUG: Failed to start voice recording - falling back to text mode"
                )
            self.stop_voice_recording()
            return

        if config.debug_mode:
            print("DEBUG: Voice recording started")

    def stop_voice_recording(self):
        """Stop voice recording and process audio"""
        if not self.recording_mode:
            return

        self.recording_mode = False

        # Audio feedback: play stop sound
        self.play_sound(self.sound_record_stop)

        # Stop recording and get audio data
        audio_data = self.voice_recorder.stop_recording()

        if audio_data is not None and len(audio_data) > 0:
            # Show processing overlay
            self.show_processing_overlay()

            # Start transcription
            self.transcription_service.transcribe_async(audio_data)

            if config.debug_mode:
                print(
                    f"DEBUG: Voice recording stopped - {len(audio_data)} audio samples captured"
                )
        else:
            # No audio captured, just update to normal empty state
            self.update_empty_state()

            if config.debug_mode:
                print("DEBUG: Voice recording stopped - no audio data captured")

    def save_and_exit(self, event):
        note_text = self.text.get("1.0", "end-1c").strip()

        # Save if there's actual text content
        if note_text:
            # Get save path from config
            notes_file_path = Path(config.save_path)
            notes_dir = notes_file_path.parent
            notes_dir.mkdir(parents=True, exist_ok=True)

            # Append to file with newlines
            notes_file = notes_file_path
            with open(notes_file, "a", encoding="utf-8") as f:
                if notes_file.exists() and notes_file.stat().st_size > 0:
                    f.write(
                        f"\n\n{note_delimiter}\n\n"
                    )  # Add spacing only if file exists and isn't empty
                f.write(note_text)

        self.root.destroy()

    # Voice recording and transcription callbacks
    def on_voice_recording_start(self):
        """Callback when voice recording starts"""
        if config.debug_mode:
            print("DEBUG: Voice recording started (callback)")

    def on_voice_recording_stop(self):
        """Callback when voice recording stops"""
        if config.debug_mode:
            print("DEBUG: Voice recording stopped (callback)")

    def on_transcription_start(self):
        """Callback when transcription starts"""
        if config.debug_mode:
            print("DEBUG: Transcription started")

    def on_transcription_complete(self, transcribed_text):
        """Callback when transcription completes successfully"""
        if config.debug_mode:
            print(f"DEBUG: Transcription completed: '{transcribed_text}'")

        # Insert transcribed text and update overlay
        def update_text():
            if transcribed_text.strip():
                # Smart spacing: add space if needed
                cursor_pos = self.text.index("insert")
                text_to_insert = transcribed_text.strip()

                # Check if we need to add a space before the transcribed text
                if cursor_pos != "1.0":  # Not at the beginning of the text
                    char_before = self.text.get(f"{cursor_pos}-1c", cursor_pos)
                    if char_before and char_before not in [" ", "\n", "\t"]:
                        text_to_insert = " " + text_to_insert

                self.text.insert("insert", text_to_insert)

            # Update empty state overlay
            self.update_empty_state()

        # Update UI in main thread
        self.root.after(0, update_text)

    def on_transcription_error(self, error_message):
        """Callback when transcription fails"""
        if config.debug_mode:
            print(f"DEBUG: Transcription error: {error_message}")

        # Just update overlay back to normal state on error
        def update_text():
            # Don't insert error text, just reset to normal empty state
            self.update_empty_state()

        # Update UI in main thread
        self.root.after(0, update_text)

    def run(self):
        self.ensure_focus()  # Ensure focus when starting
        self.root.mainloop()


def validate_llm_config():
    """Validate and test LLM configuration"""
    from llm import llm_client, LLMError

    print("=== LLM Configuration Test ===")
    print()

    # Show current config
    print("📋 Current Configuration:")
    print(f"  Enabled: {config.llm_enabled}")
    print(f"  Base URL: {config.llm_base_url}")
    print(f"  Model: {config.llm_model}")
    print(f"  API Key: {'Set' if config.llm_api_key else 'Not set'}")
    print(f"  Timeout: {config.llm_timeout_seconds}s")
    print(f"  Max Tokens: {config.llm_max_tokens}")
    print(f"  Temperature: {config.llm_temperature}")
    print()

    if not config.llm_enabled:
        print("❌ LLM is disabled in configuration")
        print("   Enable it by setting 'enabled = true' in ~/.config/quip/config.toml")
        return

    if (
        not config.llm_api_key
        and "localhost" not in config.llm_base_url
        and "10.0.6.16" not in config.llm_base_url
    ):
        print("❌ No API key configured for cloud provider")
        print("   Set your API key in ~/.config/quip/config.toml")
        return

    # Test with sample text
    test_text = "hello wrld this mesage has bad grammer and speling"

    print(f'🧪 Testing with: "{test_text}"')
    print()

    try:
        print("⏳ Sending request to LLM...")
        improved_text = llm_client.improve_note(test_text)

        print("✅ Success!")
        print(f'📝 Original:  "{test_text}"')
        print(f'✨ Improved:  "{improved_text}"')
        print()
        print("🎉 LLM configuration is working correctly!")
        print("   You can now use Ctrl+I in Quip to improve your notes.")

    except LLMError as e:
        print(f"❌ LLM Error: {e}")

        # Provide helpful suggestions based on error
        error_str = str(e).lower()
        if "404" in error_str:
            print("💡 Suggestions:")
            print("   - Check if the base_url is correct")
            print("   - Verify the model name exists")
            if "generativelanguage" in config.llm_base_url:
                print("   - For Gemini, try model 'gemini-1.5-flash'")
        elif "401" in error_str or "403" in error_str:
            print("💡 Suggestions:")
            print("   - Check if your API key is valid")
            print("   - Verify API key has proper permissions")
        elif "connection" in error_str or "timeout" in error_str:
            print("💡 Suggestions:")
            print("   - Check if the service is running")
            print("   - Verify network connectivity")
            if "ollama" in config.llm_base_url.lower():
                print("   - Is Ollama running? Try: ollama list")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def get_version():
    """Get version from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"


def main():
    import sys

    # Handle CLI arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            from updater import UpdateChecker

            updater = UpdateChecker()
            success = updater.perform_update()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--check-update":
            from updater import UpdateChecker

            updater = UpdateChecker()
            update_info = updater.check_for_updates()
            if update_info:
                print(updater.update_available_message(update_info))
            else:
                print("✅ Quip is up to date")
            sys.exit(0)
        elif sys.argv[1] == "--version":
            print(f"Quip v{get_version()}")
            sys.exit(0)
        elif sys.argv[1] == "--validate-llm-config":
            validate_llm_config()
            sys.exit(0)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Quip - Frictionless thought capture")
            print()
            print("Usage:")
            print("  quip                          Start GUI mode")
            print("  quip --validate-llm-config    Test LLM configuration")
            print("  quip --check-update           Check for updates")
            print("  quip --update                 Perform update")
            print("  quip --version                Show version")
            print("  quip --help                   Show this help")
            sys.exit(0)

    # Normal GUI mode
    app = QuickNote()
    app.run()


if __name__ == "__main__":
    main()
