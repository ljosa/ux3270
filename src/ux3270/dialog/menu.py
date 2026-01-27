"""Menu UI component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Callable, Optional

from ux3270.panel import Colors


class MenuItem:
    """Represents a menu item."""

    def __init__(self, key: str, label: str, action: Callable):
        """
        Initialize a menu item.

        Args:
            key: Single character key to select this item
            label: Display label for the menu item
            action: Function to call when item is selected
        """
        self.key = key
        self.label = label
        self.action = action


class Menu:
    """
    IBM 3270-style menu screen.

    Displays a list of options with single-key selection.
    Follows IBM CUA (Common User Access) conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Menu items in body area
    - Function keys at bottom
    """

    # CUA layout constants
    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    ITEMS_START_ROW = 3

    def __init__(self, title: str = "MAIN MENU", panel_id: str = "",
                 instruction: str = "Select an option"):
        """
        Initialize a menu.

        Args:
            title: Menu title (displayed in uppercase per IBM convention)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Instruction text (shown on row 2 per CUA)
        """
        self.title = title.upper()
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.items: List[MenuItem] = []

    def add_item(self, key: str, label: str, action: Callable) -> "Menu":
        """
        Add a menu item.

        Args:
            key: Single character key to select this item
            label: Display label
            action: Function to call when selected

        Returns:
            Self for method chaining
        """
        self.items.append(MenuItem(key, label, action))
        return self

    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80  # IBM 3270 Model 2 standard

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def render(self):
        """Render the menu following CUA layout.

        CUA Layout (adapted for variable height):
        - Row 0: Panel ID (left) + Title (centered)
        - Row 1: Instruction line
        - Rows 3+: Menu items
        - Row height-2: Separator
        - Row height-1: Function keys
        """
        self.clear()
        height, width = self._get_terminal_size()

        # Row 0: Panel ID (left) and Title (centered)
        self._move_cursor(self.TITLE_ROW, 0)
        if self.panel_id:
            print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            self._move_cursor(self.TITLE_ROW, title_col)
            print(f"{Colors.title(self.title)}", end="", flush=True)

        # Row 1: Instruction line
        if self.instruction:
            self._move_cursor(self.INSTRUCTION_ROW, 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

        # Menu items starting at row 3
        for i, item in enumerate(self.items):
            self._move_cursor(self.ITEMS_START_ROW + i, 2)
            key_display = Colors.intensified(item.key)
            print(f"{key_display} {Colors.PROTECTED}-{Colors.RESET} {item.label}", end="", flush=True)

        # Separator (height-2) - full width per CUA
        self._move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys (height-1)
        self._move_cursor(height - 1, 0)
        print(f"{Colors.info('F3=Exit')}", end="", flush=True)

    def _read_key(self, fd) -> str:
        """Read a key, handling escape sequences for function keys."""
        ch = sys.stdin.read(1)

        # Handle escape sequences (function keys, arrow keys)
        if ch == '\x1b':
            # Read potential escape sequence
            seq1 = sys.stdin.read(1)
            if seq1 == '[':
                seq2 = sys.stdin.read(1)
                # F3 is typically ESC [ 1 3 ~ or ESC O R
                if seq2 == '1':
                    seq3 = sys.stdin.read(1)
                    if seq3 == '3':
                        sys.stdin.read(1)  # Read the ~
                        return 'F3'
                elif seq2 == 'O':
                    seq3 = sys.stdin.read(1)
                    if seq3 == 'R':
                        return 'F3'
            elif seq1 == 'O':
                seq2 = sys.stdin.read(1)
                if seq2 == 'R':
                    return 'F3'
            # Not a recognized sequence, treat as escape
            return 'ESC'

        return ch

    def show(self) -> Optional[str]:
        """
        Display the menu and wait for user selection.

        Returns:
            Selected key, or None if user exits (F3 or X)
        """
        self.render()

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set raw mode for single character input
            tty.setraw(fd)

            while True:
                key = self._read_key(fd)

                # F3 = Exit (IBM standard), also support X and Ctrl+C
                if key == 'F3' or key.upper() == 'X' or key == '\x03':
                    return None

                # Find matching menu item
                for item in self.items:
                    if item.key.upper() == key.upper():
                        # Restore terminal settings before calling action
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        self.clear()
                        item.action()
                        return key

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def run(self):
        """Run the menu in a loop until user exits."""
        try:
            while True:
                result = self.show()
                if result is None:
                    self.clear()
                    break
        except KeyboardInterrupt:
            self.clear()
