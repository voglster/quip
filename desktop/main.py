import tkinter as tk
from pathlib import Path
import subprocess
import re

from config import config

note_delimiter = "---"


class QuickNote:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quip")

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

        # Create a frame for padding
        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create and configure the text widget with minimal padding
        self.text = tk.Text(
            frame,
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
            print("Quip v0.1.0")
            sys.exit(0)

    # Normal GUI mode
    app = QuickNote()
    app.run()


if __name__ == "__main__":
    main()
