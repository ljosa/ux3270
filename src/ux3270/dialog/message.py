"""Message display component for IBM 3270-style applications."""

import sys
import tty
import termios

from ux3270.panel import Colors


class MessagePanel:
    """
    CUA-style message panel for displaying information to the user.

    This is an information panel - displays a message and waits for
    acknowledgment (Enter or F3). No command line per CUA conventions
    for simple information panels.
    """

    def __init__(self, message: str = "", msg_type: str = "info",
                 panel_id: str = "", title: str = ""):
        """
        Initialize a message panel.

        Args:
            message: The message to display
            msg_type: One of "error", "success", "warning", "info"
            panel_id: Optional panel identifier
            title: Optional title
        """
        self.message = message
        self.msg_type = msg_type
        self.panel_id = panel_id.upper() if panel_id else ""
        self.title = title.upper() if title else ""

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80

    def _clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def show(self):
        """Display the message and wait for user acknowledgment."""
        height, width = self._get_terminal_size()

        self._clear()

        # Row 0: Panel ID and Title
        if self.panel_id:
            self._move_cursor(0, 0)
            print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            self._move_cursor(0, title_col)
            print(f"{Colors.title(self.title)}", end="", flush=True)

        # Message line (height-3)
        self._move_cursor(height - 3, 0)
        if self.msg_type == "error":
            print(Colors.error(self.message), end="", flush=True)
        elif self.msg_type == "success":
            print(Colors.success(self.message), end="", flush=True)
        elif self.msg_type == "warning":
            print(Colors.warning(self.message), end="", flush=True)
        else:
            print(Colors.info(self.message), end="", flush=True)

        # Separator (height-2)
        self._move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys (height-1)
        self._move_cursor(height - 1, 0)
        print(Colors.info("Enter=Continue"), end="", flush=True)

        # Wait for Enter or F3
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n', '\x03'):  # Enter or Ctrl+C
                    break
                if ch == '\x1b':  # Escape sequence
                    seq1 = sys.stdin.read(1)
                    if seq1 == '[':
                        seq2 = sys.stdin.read(1)
                        if seq2 == '1':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '3':
                                sys.stdin.read(1)  # Read ~
                                break  # F3
                    elif seq1 == 'O':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'R':  # F3
                            break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        self._clear()


def show_message(message: str, msg_type: str = "info",
                 panel_id: str = "", title: str = ""):
    """
    Convenience function to display a message panel.

    Args:
        message: The message to display
        msg_type: One of "error", "success", "warning", "info"
        panel_id: Optional panel identifier
        title: Optional title
    """
    panel = MessagePanel(message, msg_type, panel_id, title)
    panel.show()
