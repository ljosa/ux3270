"""Table display component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List

from ux3270.colors import Colors


class Table:
    """
    IBM 3270-style table/list display.

    Displays tabular data with column headers following IBM conventions:
    - Title at top
    - Column headers in intensified text
    - Data rows in default (green) color
    - Row count and function key hints at bottom
    """

    def __init__(self, title: str = "", columns: List[str] = None):
        """
        Initialize a table.

        Args:
            title: Table title (displayed in uppercase per IBM convention)
            columns: List of column headers
        """
        self.title = title.upper() if title else ""
        self.columns = columns or []
        self.rows: List[List[str]] = []
        self.col_widths: List[int] = []

    def add_row(self, *values) -> "Table":
        """
        Add a row to the table.

        Args:
            values: Column values for the row

        Returns:
            Self for method chaining
        """
        self.rows.append(list(values))
        return self

    def _calculate_widths(self):
        """Calculate column widths based on content."""
        if not self.columns:
            return

        self.col_widths = [len(col) for col in self.columns]

        for row in self.rows:
            for i, val in enumerate(row):
                if i < len(self.col_widths):
                    self.col_widths[i] = max(self.col_widths[i], len(str(val)))

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80  # IBM 3270 Model 2 standard

    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def render(self):
        """Render the table following IBM 3270 conventions."""
        self.clear()
        self._calculate_widths()
        height, width = self._get_terminal_size()

        # Row 1: Title with IBM 3270-style border
        if self.title:
            border = "═" * (len(self.title) + 2)
            print(f"{Colors.PROTECTED}╔{border}╗{Colors.RESET}")
            print(f"{Colors.PROTECTED}║{Colors.RESET} {Colors.title(self.title)} {Colors.PROTECTED}║{Colors.RESET}")
            print(f"{Colors.PROTECTED}╚{border}╝{Colors.RESET}")
            print()

        # Column headers (intensified per IBM convention)
        if self.columns:
            header_parts = []
            for i, col in enumerate(self.columns):
                w = self.col_widths[i] if i < len(self.col_widths) else len(col)
                header_parts.append(Colors.header(col.ljust(w)))
            print("  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(header_parts))

            # Separator line (protected color)
            sep_parts = []
            for w in self.col_widths:
                sep_parts.append("─" * w)
            print(f"  {Colors.PROTECTED}" + "─┼─".join(sep_parts) + f"{Colors.RESET}")

        # Data rows (default green color)
        for row in self.rows:
            row_parts = []
            for i, val in enumerate(row):
                w = self.col_widths[i] if i < len(self.col_widths) else len(str(val))
                row_parts.append(f"{Colors.DEFAULT}{str(val).ljust(w)}{Colors.RESET}")
            print(f"  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(row_parts))

        print()

        # Row count (IBM convention: "Row X of Y" or "X rows")
        if self.rows:
            count_msg = f"ROWS {len(self.rows)}"
            print(Colors.info(count_msg))

        # Move to bottom of screen for function key hints
        print(f"\033[{height - 1};1H", end="")
        print(Colors.dim("─" * min(78, width - 2)))
        print(Colors.info("F3=Return") + "  " + Colors.dim("Press Enter to continue"))

    def show(self):
        """Display the table and wait for user to press a key."""
        self.render()

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set raw mode for single character input
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Handle F3 escape sequence
            if ch == '\x1b':
                sys.stdin.read(2)  # Consume rest of escape sequence
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.clear()
