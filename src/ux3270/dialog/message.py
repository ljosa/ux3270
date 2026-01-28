"""Message display component for IBM 3270-style applications."""

from ux3270.panel import Screen, Colors


class MessagePanel:
    """
    CUA-style message panel for displaying information to the user.

    This is an information panel - displays a message and waits for
    acknowledgment (Enter or F3). No command line per CUA conventions
    for simple information panels.

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
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

    def _get_message_color(self) -> str:
        """Get the appropriate color for the message type."""
        if self.msg_type == "error":
            return Colors.ERROR
        elif self.msg_type == "success":
            return Colors.SUCCESS
        elif self.msg_type == "warning":
            return Colors.WARNING
        else:
            return Colors.PROTECTED

    def _build_screen(self, height: int, width: int) -> Screen:
        """Build a Screen with the message display."""
        screen = Screen()

        # Row 0: Panel ID and Title
        if self.panel_id:
            screen.add_text(0, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(0, title_col, self.title, Colors.INTENSIFIED)

        # Message line (height-3)
        screen.add_text(height - 3, 0, self.message, self._get_message_color())

        # Separator (height-2)
        screen.add_text(height - 2, 0, "─" * width, Colors.DIM)

        # Function keys (height-1)
        screen.add_text(height - 1, 0, "Enter=Continue", Colors.PROTECTED)

        return screen

    def show(self):
        """Display the message and wait for user acknowledgment."""
        height, width = self._get_terminal_size()
        screen = self._build_screen(height, width)
        screen.show()  # Returns on Enter, F3, or any AID key


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
