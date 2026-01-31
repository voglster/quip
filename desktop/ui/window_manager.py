"""Window management and positioning for Quip application."""

import re
import subprocess
import tkinter as tk
from typing import List, Optional, Tuple

from config import config


class MonitorInfo:
    """Information about a monitor."""

    def __init__(self, name: str, x: int, y: int, width: int, height: int):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this monitor's bounds."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


class WindowManager:
    """Manages window positioning, styling, and monitor detection."""

    # Base DPI that window dimensions are designed for
    BASE_DPI = 96.0

    def __init__(self, root: tk.Tk):
        self.root = root
        self.original_height: Optional[int] = None
        self.dpi_scale = self._detect_dpi_scale()

    def _detect_dpi_scale(self) -> float:
        """Detect DPI scale factor relative to standard 96 DPI."""
        try:
            dpi = self.root.winfo_fpixels("1i")  # pixels per inch
            scale = dpi / self.BASE_DPI
            # Clamp to reasonable range (1.0 to 4.0)
            scale = max(1.0, min(4.0, scale))
            if config.debug_mode:
                print(f"DEBUG: Detected DPI={dpi}, scale factor={scale:.2f}x")
            return scale
        except Exception:
            return 1.0  # Fallback to no scaling

    def setup_window_properties(self) -> None:
        """Configure window properties for borderless overlay behavior."""
        # Hide window initially to prevent flash
        self.root.withdraw()

        # Try different approaches for borderless window
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

        # Try to add transparency
        try:
            self.root.wm_attributes("-alpha", config.transparency)
        except tk.TclError:
            pass

    def detect_monitors(self) -> List[MonitorInfo]:
        """Detect monitor configuration using xrandr on Linux."""
        try:
            # Try xrandr first (most common on Linux)
            result = subprocess.run(
                ["xrandr"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return self._parse_xrandr_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: return single monitor based on tkinter values
        return [
            MonitorInfo(
                name="default",
                x=0,
                y=0,
                width=self.root.winfo_screenwidth(),
                height=self.root.winfo_screenheight(),
            )
        ]

    def _parse_xrandr_output(self, output: str) -> List[MonitorInfo]:
        """Parse xrandr output to get monitor positions and sizes."""
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
                    MonitorInfo(
                        name=name,
                        x=int(x),
                        y=int(y),
                        width=int(width),
                        height=int(height),
                    )
                )

        if not monitors:
            # Fallback
            monitors.append(
                MonitorInfo(
                    name="default",
                    x=0,
                    y=0,
                    width=self.root.winfo_screenwidth(),
                    height=self.root.winfo_screenheight(),
                )
            )

        return monitors

    def find_current_monitor(
        self, monitors: List[MonitorInfo]
    ) -> Optional[MonitorInfo]:
        """Find which monitor the cursor is currently on."""
        pointer_x = self.root.winfo_pointerx()
        pointer_y = self.root.winfo_pointery()

        if config.debug_mode:
            print(f"DEBUG: pointer x={pointer_x}, pointer y={pointer_y}")
            print(
                f"DEBUG: Detected monitors: {[f'{m.name}({m.x},{m.y},{m.width}x{m.height})' for m in monitors]}"
            )

        for monitor in monitors:
            if config.debug_mode:
                print(
                    f"DEBUG: Checking if cursor ({pointer_x}, {pointer_y}) is in monitor {monitor.name}: "
                    f"x={monitor.x}-{monitor.x + monitor.width}, y={monitor.y}-{monitor.y + monitor.height}"
                )

            if monitor.contains_point(pointer_x, pointer_y):
                return monitor

        return None

    def estimate_monitor_from_cursor(
        self, monitors: List[MonitorInfo]
    ) -> Tuple[int, int, int, int]:
        """Estimate monitor dimensions when cursor is in gap between monitors."""
        pointer_x = self.root.winfo_pointerx()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Multi-monitor setup with gaps - estimate monitor size
        if len(monitors) >= 2 and screen_width > 4000:
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

        return monitor_start_x, monitor_start_y, monitor_width, monitor_height

    def position_window_centered(self) -> None:
        """Position window centered on the current monitor."""
        # Apply DPI scaling to window dimensions
        window_width = int(config.window_width * self.dpi_scale)
        window_height = int(config.window_height * self.dpi_scale)
        self.original_height = window_height  # Store for expansion/collapse

        # Get monitor dimensions and find current monitor
        self.root.update_idletasks()  # Ensure window is ready
        monitors = self.detect_monitors()
        current_monitor = self.find_current_monitor(monitors)

        if current_monitor:
            monitor_start_x = current_monitor.x
            monitor_start_y = current_monitor.y
            monitor_width = current_monitor.width
            monitor_height = current_monitor.height
        else:
            # Cursor is in a gap between monitors or monitor not detected
            monitor_start_x, monitor_start_y, monitor_width, monitor_height = (
                self.estimate_monitor_from_cursor(monitors)
            )

        # Center on the current monitor
        center_x = monitor_start_x + int(monitor_width / 2 - window_width / 2)
        center_y = monitor_start_y + int(monitor_height / 2 - window_height / 2)

        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        if config.debug_mode:
            print(
                f"DEBUG: Positioned window at {center_x},{center_y} on monitor "
                f"{monitor_start_x},{monitor_start_y} {monitor_width}x{monitor_height}"
            )

    def expand_window(self, additional_height: int = 200) -> None:
        """Expand window height to accommodate additional content."""
        if self.original_height is None:
            return

        # Apply DPI scaling to additional height
        scaled_additional = int(additional_height * self.dpi_scale)
        expanded_height = self.original_height + scaled_additional

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

    def restore_original_height(self) -> None:
        """Restore window to its original height."""
        if self.original_height is None:
            return

        current_geometry = self.root.geometry()
        width_height, x_y = current_geometry.split("+", 1)
        width, height = width_height.split("x")
        x, y = x_y.split("+")

        new_geometry = f"{width}x{self.original_height}+{x}+{y}"
        self.root.geometry(new_geometry)

        if config.debug_mode:
            print(f"DEBUG: Restored window to original height {self.original_height}")

    def ensure_focus(self) -> None:
        """Ensure window has proper focus."""
        self.root.lift()  # Lift the window to the top
        self.root.focus_force()  # Force focus to the window

        # Also focus the text widget if available
        if hasattr(self, "text_widget") and self.text_widget:
            self.text_widget.focus_set()

    def show_window(self) -> None:
        """Show the window after configuration is complete."""
        self.root.deiconify()
        self.root.after(100, self.ensure_focus)
