import tkinter as tk
from pathlib import Path

note_delimiter = "---"


class QuickNote:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quip")

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
                "-alpha", 0.98
            )  # Slight transparency can help with antialiasing
        except tk.TclError:
            pass

        # Dark mode colors
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"

        # Set window size and position (centered on primary monitor)
        window_width = 800
        window_height = 150

        # Get the primary monitor dimensions
        self.root.update_idletasks()  # Ensure window is ready
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # For multi-monitor setups, use winfo_width/height of root to get primary monitor
        # Center on primary monitor (assume primary is left-most at 0,0)
        primary_width = self.root.winfo_vrootwidth() // max(
            1, screen_width // 1920
        )  # Rough estimate
        primary_height = self.root.winfo_vrootheight() // max(
            1, screen_height // 1080
        )  # Rough estimate

        # Fallback: just use the first monitor's typical dimensions
        if primary_width > 3840:  # Multi-monitor detected
            primary_width = 1920  # Assume standard monitor width
            primary_height = 1080  # Assume standard monitor height
        else:
            primary_width = screen_width
            primary_height = screen_height

        center_x = int(primary_width / 2 - window_width / 2)
        center_y = int(primary_height / 2 - window_height / 2)
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
        self.text.bind("<Escape>", lambda e: self.root.destroy())

        # Ensure proper focus
        self.root.after(100, self.ensure_focus)

        # Bind window manager delete window protocol
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def ensure_focus(self):
        """Ensure window has proper focus"""
        self.root.lift()  # Lift the window to the top
        self.root.focus_force()  # Force focus to the window
        self.text.focus_set()  # Set focus to the text widget

    def save_and_exit(self, event):
        note_text = self.text.get("1.0", "end-1c").strip()
        if note_text:
            # Create directory if it doesn't exist
            notes_dir = Path.home() / "notes" / "5. Inbox"
            notes_dir.mkdir(parents=True, exist_ok=True)

            # Append to file with newlines
            notes_file = notes_dir / "Inbox.md"
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
    app = QuickNote()
    app.run()


if __name__ == "__main__":
    main()
