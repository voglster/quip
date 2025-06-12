import tkinter as tk
from pathlib import Path
import subprocess
import re
import sys

from config import config

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

    def save_and_exit(self, event):
        note_text = self.text.get("1.0", "end-1c").strip()
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
