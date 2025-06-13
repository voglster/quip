"""Curator functionality for note improvement and feedback."""

import tkinter as tk
from typing import Optional

from config import config


class CuratorManager:
    """Manages curator feedback and note improvement functionality."""

    def __init__(self, parent_frame: tk.Frame, window_manager):
        self.parent_frame = parent_frame
        self.window_manager = window_manager
        self.bg_color = "#2b2b2b"

        # State tracking
        self.curator_mode = False
        self.current_curator_feedback: Optional[str] = None
        self.text_before_improvement: Optional[str] = None

        # Create curator feedback area (initially hidden)
        self._create_curator_ui()

    def _create_curator_ui(self) -> None:
        """Create curator feedback UI components."""
        self.curator_frame = tk.Frame(self.parent_frame, bg=self.bg_color)

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

    def is_curator_mode_active(self) -> bool:
        """Check if curator mode is currently active."""
        return self.curator_mode

    def toggle_curator_mode(self, current_text: str) -> bool:
        """Toggle curator feedback mode and get feedback for current note.

        Args:
            current_text: Current note text content

        Returns:
            True if curator mode was activated/updated, False if LLM not available
        """
        if not config.llm_enabled:
            if config.debug_mode:
                print("DEBUG: LLM not enabled for curator mode")
            return False

        if not current_text.strip():
            if config.debug_mode:
                print("DEBUG: No text to curate")
            return False

        # Show/refresh curator feedback
        self.show_curator_feedback(current_text)
        return True

    def show_curator_feedback(self, text: str) -> None:
        """Show curator feedback area and get LLM feedback."""
        try:
            # Show loading state in curator area
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", "🤔 Analyzing your note...")
            self.curator_text.config(state="disabled")

            # Show curator frame if not already visible
            if not self.curator_mode:
                self.curator_frame.pack(fill="both", expand=True, pady=(5, 0))
                self.window_manager.expand_window()
                self.curator_mode = True

            # Get curator feedback
            feedback = self._get_curator_feedback(text)

            # Update curator area with feedback
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", feedback)
            self.curator_text.config(state="disabled")

            # Store feedback for context in improvements
            self.current_curator_feedback = feedback

            if config.debug_mode:
                print("DEBUG: Curator feedback displayed")

        except Exception as e:
            # Show error in curator area
            self.curator_text.config(state="normal")
            self.curator_text.delete("1.0", "end")
            self.curator_text.insert("1.0", f"❌ Error getting feedback: {e}")
            self.curator_text.config(state="disabled")
            if config.debug_mode:
                print(f"DEBUG: Curator error: {e}")

    def _get_curator_feedback(self, text: str) -> str:
        """Get curator feedback from LLM."""
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

    def clear_curator_mode(self) -> None:
        """Clear curator mode and hide feedback area."""
        if self.curator_mode:
            # Hide curator frame
            self.curator_frame.pack_forget()

            # Restore original window height
            self.window_manager.restore_original_height()

            # Clear state
            self.curator_mode = False
            self.current_curator_feedback = None

            if config.debug_mode:
                print("DEBUG: Curator mode cleared")

    def improve_note(self, current_text: str) -> tuple[bool, str]:
        """Improve the current note using LLM.

        Args:
            current_text: Current note text content

        Returns:
            Tuple of (success, improved_text_or_error_message)
        """
        if not config.llm_enabled:
            if config.debug_mode:
                print("DEBUG: LLM not enabled")
            return False, "LLM not enabled"

        if not current_text.strip():
            if config.debug_mode:
                print("DEBUG: No text to improve")
            return False, "No text to improve"

        try:
            from llm import llm_client

            # Store original text for undo functionality
            self.text_before_improvement = current_text

            # Pass curator feedback as context if available
            curator_context = (
                self.current_curator_feedback if self.curator_mode else None
            )
            improved_text = llm_client.improve_note(current_text, curator_context)

            # Clear curator mode after improvement
            self.clear_curator_mode()

            if config.debug_mode:
                print("DEBUG: Note improved successfully")

            return True, improved_text

        except Exception as e:
            # Clear stored text since improvement failed
            self.text_before_improvement = None
            if config.debug_mode:
                print(f"DEBUG: Error during improvement: {e}")
            return False, str(e)

    def undo_improvement(self) -> tuple[bool, str]:
        """Undo the last LLM improvement and restore original text.

        Returns:
            Tuple of (success, original_text_or_error_message)
        """
        if self.text_before_improvement is None:
            if config.debug_mode:
                print("DEBUG: No previous text to restore")
            return False, "No previous text to restore"

        # Get the text to restore
        original_text = self.text_before_improvement

        # Clear the stored text (only allow one undo)
        self.text_before_improvement = None

        if config.debug_mode:
            print("DEBUG: Restored text before improvement")

        return True, original_text
