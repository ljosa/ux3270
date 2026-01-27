"""Menu UI component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Callable, Optional

from ux3270.colors import Colors


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
    Follows IBM CUA (Common User Access) conventions.
    """

    def __init__(self, title: str = "MAIN MENU"):
        """
        Initialize a menu.

        Args:
            title: Menu title (displayed in uppercase per IBM convention)
        """
        self.title = title.upper()
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

    def _get_terminal_height(self) -> int:
        """Get terminal height."""
        try:
            import os
            return os.get_terminal_size().lines
        except Exception:
            return 24  # IBM 3270 Model 2 standard

    def render(self):
        """Render the menu following IBM 3270 conventions."""
        self.clear()
        height = self._get_terminal_height()

        # Row 1: Title with IBM 3270-style border
        border = "═" * (len(self.title) + 2)
        print(f"{Colors.PROTECTED}╔{border}╗{Colors.RESET}")
        print(f"{Colors.PROTECTED}║{Colors.RESET} {Colors.title(self.title)} {Colors.PROTECTED}║{Colors.RESET}")
        print(f"{Colors.PROTECTED}╚{border}╝{Colors.RESET}")
        print()

        # Menu items with IBM 3270 styling
        for item in self.items:
            key_display = Colors.intensified(item.key)
            print(f"  {key_display} {Colors.DEFAULT}-{Colors.RESET} {item.label}")

        # Move to bottom of screen for function key hints (IBM 3270 convention)
        # Leave 2 lines at bottom: one for hints, one for messages
        print(f"\033[{height - 1};1H", end="")
        print(Colors.dim("─" * 78))
        print(Colors.info("F3=Exit") + "  " + Colors.dim("Enter selection number"))

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
                    print(Colors.info("***"))
                    break
        except KeyboardInterrupt:
            self.clear()
            print(Colors.info("***"))
