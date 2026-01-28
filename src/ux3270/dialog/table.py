"""Table display component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Optional

from ux3270.panel import Colors


class Table:
    """
    IBM 3270-style table/list display with pagination.

    Displays tabular data with column headers following CUA conventions:
    - Panel ID at top-left, title centered
    - Column headers in intensified text
    - Data rows in default (green) color
    - Row count/pagination info on message line
    - F7/F8 for page up/down (CUA standard)
    - Function keys at bottom
    """

    # CUA layout constants
    TITLE_ROW = 0
    HEADER_ROW = 2       # Column headers
    DATA_START_ROW = 4   # First data row (after header + separator)

    # Lines reserved for chrome
    HEADER_LINES = 4     # Title + blank + column header + separator
    FOOTER_LINES = 3     # Message + separator + function keys

    def __init__(self, title: str = "", columns: Optional[List[str]] = None,
                 panel_id: str = ""):
        """
        Initialize a table.

        Args:
            title: Table title (displayed in uppercase per IBM convention)
            columns: List of column headers
            panel_id: Optional panel identifier (shown at top-left per CUA)
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
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

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def render(self, page_size: int, height: int, width: int):
        """Render the table following CUA layout.

        CUA Layout (adapted for variable height):
        - Row 0: Panel ID (left) + Title (centered)
        - Row 2: Column headers
        - Row 3: Separator
        - Rows 4 to height-4: Data rows
        - Row height-3: Message line (row count/pagination)
        - Row height-2: Separator
        - Row height-1: Function keys
        """
        self.clear()
        self._calculate_widths()

        # Row 0: Panel ID (left) and Title (centered)
        self._move_cursor(self.TITLE_ROW, 0)
        if self.panel_id:
            print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            self._move_cursor(self.TITLE_ROW, title_col)
            print(f"{Colors.title(self.title)}", end="", flush=True)

        # Row 2: Column headers (intensified per CUA convention)
        if self.columns:
            self._move_cursor(self.HEADER_ROW, 0)
            header_parts = []
            for i, col in enumerate(self.columns):
                w = self.col_widths[i] if i < len(self.col_widths) else len(col)
                header_parts.append(Colors.header(col.ljust(w)))
            print("  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(header_parts), end="", flush=True)

            # Row 3: Separator line
            self._move_cursor(self.HEADER_ROW + 1, 0)
            sep_parts = []
            for w in self.col_widths:
                sep_parts.append("─" * w)
            print(f"  {Colors.PROTECTED}" + "─┼─".join(sep_parts) + f"{Colors.RESET}", end="", flush=True)

        # Data rows (paginated, default green color)
        end_row = min(self.current_row + page_size, len(self.rows))
        visible_rows = self.rows[self.current_row:end_row]

        for i, row in enumerate(visible_rows):
            self._move_cursor(self.DATA_START_ROW + i, 0)
            row_parts = []
            for j, val in enumerate(row):
                w = self.col_widths[j] if j < len(self.col_widths) else len(str(val))
                row_parts.append(f"{Colors.DEFAULT}{str(val).ljust(w)}{Colors.RESET}")
            print(f"  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(row_parts), end="", flush=True)

        # Message line (height-3): Row count and pagination info
        self._move_cursor(height - 3, 0)
        if self.rows:
            if len(self.rows) > page_size:
                start_display = self.current_row + 1
                end_display = min(self.current_row + page_size, len(self.rows))
                count_msg = f"ROW {start_display} TO {end_display} OF {len(self.rows)}"
            else:
                count_msg = f"ROWS {len(self.rows)}"
            print(Colors.info(count_msg), end="", flush=True)

        # Separator (height-2) - full width per CUA
        self._move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys (height-1)
        self._move_cursor(height - 1, 0)
        hints = [Colors.info("F3=Return")]
        if len(self.rows) > page_size:
            if self.current_row > 0:
                hints.append(Colors.info("F7=Up"))
            if self.current_row + page_size < len(self.rows):
                hints.append(Colors.info("F8=Down"))
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
