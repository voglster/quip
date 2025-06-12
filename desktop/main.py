import tkinter as tk
from pathlib import Path

note_delimiter = "---"


class QuickNote:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Quip")

        # GNOME/Ubuntu specific window hints
        self.root.attributes("-type", "dialog")  # Makes it more compact on GNOME
        self.root.attributes("-topmost", True)

        # Dark mode colors
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"

        # Set window size and position (centered)
        window_width = 800
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # Configure the root window background
        self.root.configure(bg=bg_color)

        # Create a frame for padding
        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Create and configure the text widget
        self.text = tk.Text(
            frame,
            font=("Helvetica", 14),
            wrap="word",
            height=4,
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,  # Cursor color
            relief="flat",
            padx=10,
            pady=10,
        )
        self.text.pack(fill="both", expand=True)

        # Remove the default highlight colors
        self.text.configure(
            highlightthickness=1,
            highlightbackground="#404040",
            highlightcolor="#404040",
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
