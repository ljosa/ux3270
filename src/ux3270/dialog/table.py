"""Table display component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List

from ux3270.panel import Colors


class Table:
    """
    IBM 3270-style table/list display with pagination.

    Displays tabular data with column headers following IBM conventions:
    - Title at top
    - Column headers in intensified text
    - Data rows in default (green) color
    - Row count and pagination info at bottom
    - F7/F8 for page up/down (IBM standard)
    """

    # Lines reserved for chrome (title box, headers, footer, etc.)
    HEADER_LINES = 6  # Title box (3) + blank + column header + separator
    FOOTER_LINES = 3  # Row count + separator + function keys

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
        self.current_row = 0  # First visible row index

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

    def _get_page_size(self, height: int) -> int:
        """Calculate number of data rows that fit on screen."""
        return max(1, height - self.HEADER_LINES - self.FOOTER_LINES)

    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def render(self, page_size: int, height: int, width: int):
        """Render the table following IBM 3270 conventions.

        Args:
            page_size: Number of data rows to display
            height: Terminal height
            width: Terminal width
        """
        self.clear()
        self._calculate_widths()

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

        # Data rows (paginated, default green color)
        end_row = min(self.current_row + page_size, len(self.rows))
        visible_rows = self.rows[self.current_row:end_row]

        for row in visible_rows:
            row_parts = []
            for i, val in enumerate(row):
                w = self.col_widths[i] if i < len(self.col_widths) else len(str(val))
                row_parts.append(f"{Colors.DEFAULT}{str(val).ljust(w)}{Colors.RESET}")
            print(f"  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(row_parts))

        # Row count and position (IBM convention: "Row X to Y of Z")
        print(f"\033[{height - 2};1H", end="")
        if self.rows:
            if len(self.rows) > page_size:
                # Show pagination info
                start_display = self.current_row + 1
                end_display = min(self.current_row + page_size, len(self.rows))
                count_msg = f"ROW {start_display} TO {end_display} OF {len(self.rows)}"
            else:
                count_msg = f"ROWS {len(self.rows)}"
            print(Colors.info(count_msg), end="")

        # Move to bottom of screen for function key hints (IBM 3270 convention)
        print(f"\033[{height - 1};1H", end="")
        print(Colors.dim("─" * min(78, width - 2)), end="")
        print(f"\033[{height};1H", end="")

        # Build function key hints based on pagination state
        hints = [Colors.info("F3=Return")]
        if len(self.rows) > page_size:
            if self.current_row > 0:
                hints.append(Colors.info("F7=Up"))
            if self.current_row + page_size < len(self.rows):
                hints.append(Colors.info("F8=Down"))
        hints.append(Colors.dim("Enter=Return"))

        print("  ".join(hints), end="", flush=True)

    def _read_key(self, fd) -> str:
        """Read a key, handling escape sequences for function keys."""
        ch = sys.stdin.read(1)

        # Handle escape sequences (function keys)
        if ch == '\x1b':
            seq1 = sys.stdin.read(1)
            if seq1 == '[':
                seq2 = sys.stdin.read(1)
                if seq2 == '1':
                    seq3 = sys.stdin.read(1)
                    seq4 = sys.stdin.read(1)  # Read the ~
                    if seq3 == '3':
                        return 'F3'
                    elif seq3 == '8':
                        return 'F7'
                    elif seq3 == '9':
                        return 'F8'
                # Some terminals use different sequences
                elif seq2 == '1' and seq1 == 'O':
                    pass
            elif seq1 == 'O':
                seq2 = sys.stdin.read(1)
                if seq2 == 'R':
                    return 'F3'
                elif seq2 == 'Q':
                    return 'F7'  # Some terminals
                elif seq2 == 'S':
                    return 'F8'  # Some terminals
            return 'ESC'

        return ch

    def show(self):
        """Display the table with pagination and wait for user input."""
        height, width = self._get_terminal_size()
        page_size = self._get_page_size(height)

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                self.render(page_size, height, width)

                # Set raw mode for single character input
                tty.setraw(fd)

                key = self._read_key(fd)

                # Restore settings before processing (in case we exit)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if key in ('F3', '\r', '\n', 'q', 'Q', '\x03'):
                    # F3, Enter, Q, or Ctrl+C = Return
                    break
                elif key == 'F7' or key == 'k' or key == 'K':
                    # Page up
                    if self.current_row > 0:
                        self.current_row = max(0, self.current_row - page_size)
                elif key == 'F8' or key == 'j' or key == 'J':
                    # Page down
                    if self.current_row + page_size < len(self.rows):
                        self.current_row = min(
                            len(self.rows) - 1,
                            self.current_row + page_size
                        )

        finally:
            # Ensure terminal settings are restored
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.clear()
