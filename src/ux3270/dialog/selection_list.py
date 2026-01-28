"""Selection list component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Optional, Dict, Any, Callable

from ux3270.panel import Colors


class SelectionList:
    """
    CUA selection list for F4=Prompt functionality.

    Displays a scrollable list where user can select an item by:
    - Typing 'S' next to the item and pressing Enter
    - Positioning cursor on a row and pressing Enter

    Follows CUA conventions:
    - Panel ID at top-left, title centered
    - Column headers in intensified text
    - Action column for selection (S=Select)
    - F3=Cancel, F6=Add (optional), F7=Backward, F8=Forward
    - Enter with 'S' action code selects the item
    """

    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    HEADER_ROW = 3
    DATA_START_ROW = 5

    HEADER_LINES = 5     # Title + instruction + blank + headers + separator
    FOOTER_LINES = 3     # Message + separator + function keys

    def __init__(self, title: str = "SELECTION LIST", columns: Optional[List[str]] = None,
                 panel_id: str = "", instruction: str = "Type S to select item"):
        """
        Initialize a selection list.

        Args:
            title: List title (displayed in uppercase per CUA)
            columns: Column headers (excluding the action column)
            panel_id: Optional panel identifier
            instruction: Instruction text
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.columns = columns or []
        self.rows: List[Dict[str, Any]] = []
        self.col_widths: List[int] = []
        self.current_row = 0  # First visible row
        self.action_col_width = 3  # Width for "S" action column
        self.add_callback: Optional[Callable] = None

    def set_add_callback(self, callback: Callable) -> "SelectionList":
        """
        Set callback for F6=Add.

        The callback should add a new item and return it as a dictionary
        with the same keys as the list columns. If the callback returns
        an item, it will be returned as the selection. If it returns None,
        the selection list returns None.

        Args:
            callback: Function to call when F6 is pressed.

        Returns:
            Self for method chaining
        """
        self.add_callback = callback
        return self

    def add_row(self, **values) -> "SelectionList":
        """
        Add a row to the selection list.

        Args:
            **values: Column name to value mapping

        Returns:
            Self for method chaining
        """
        self.rows.append(values)
        return self

    def add_rows(self, rows: List[Dict[str, Any]]) -> "SelectionList":
        """
        Add multiple rows to the selection list.

        Args:
            rows: List of dictionaries with column values

        Returns:
            Self for method chaining
        """
        self.rows.extend(rows)
        return self

    def _calculate_widths(self):
        """Calculate column widths based on content."""
        if not self.columns:
            return

        self.col_widths = [len(col) for col in self.columns]

        for row in self.rows:
            for i, col in enumerate(self.columns):
                if col in row:
                    val_len = len(str(row[col]))
                    if i < len(self.col_widths):
                        self.col_widths[i] = max(self.col_widths[i], val_len)

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80

    def _get_page_size(self, height: int) -> int:
        """Calculate number of data rows that fit on screen."""
        return max(1, height - self.HEADER_LINES - self.FOOTER_LINES)

    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def render(self, page_size: int, height: int, width: int,
               actions: Dict[int, str], cursor_row: int):
        """Render the selection list.

        Args:
            page_size: Number of data rows per page
            height: Terminal height
            width: Terminal width
            actions: Dict mapping row index to action code
            cursor_row: Current cursor row (relative to visible rows)
        """
        self.clear()
        self._calculate_widths()

        # Row 0: Panel ID and Title
        self._move_cursor(self.TITLE_ROW, 0)
        if self.panel_id:
            print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            self._move_cursor(self.TITLE_ROW, title_col)
            print(f"{Colors.title(self.title)}", end="", flush=True)

        # Row 1: Instruction
        if self.instruction:
            self._move_cursor(self.INSTRUCTION_ROW, 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

        # Row 3: Column headers with action column
        if self.columns:
            self._move_cursor(self.HEADER_ROW, 0)
            # Action column header
            print(f"  {Colors.header('S')}", end="", flush=True)
            print(f" {Colors.PROTECTED}│{Colors.RESET} ", end="", flush=True)
            # Data column headers
            header_parts = []
            for i, col in enumerate(self.columns):
                w = self.col_widths[i] if i < len(self.col_widths) else len(col)
                header_parts.append(Colors.header(col.ljust(w)))
            print(f" {Colors.PROTECTED}│{Colors.RESET} ".join(header_parts), end="", flush=True)

            # Row 4: Separator
            self._move_cursor(self.HEADER_ROW + 1, 0)
            print(f"  {Colors.PROTECTED}─", end="", flush=True)
            print(f"─┼─", end="", flush=True)
            sep_parts = ["─" * w for w in self.col_widths]
            print("─┼─".join(sep_parts) + f"{Colors.RESET}", end="", flush=True)

        # Data rows
        end_row = min(self.current_row + page_size, len(self.rows))
        visible_rows = self.rows[self.current_row:end_row]

        for i, row in enumerate(visible_rows):
            abs_idx = self.current_row + i
            self._move_cursor(self.DATA_START_ROW + i, 0)

            # Highlight current row
            if i == cursor_row:
                print(f"{Colors.REVERSE}", end="", flush=True)

            # Action column
            action = actions.get(abs_idx, " ")
            print(f"  {Colors.INPUT}{action}{Colors.RESET}", end="", flush=True)

            if i == cursor_row:
                print(f"{Colors.REVERSE}", end="", flush=True)

            print(f" {Colors.PROTECTED}│{Colors.RESET} ", end="", flush=True)

            # Data columns
            row_parts = []
            for j, col in enumerate(self.columns):
                w = self.col_widths[j] if j < len(self.col_widths) else 10
                val = str(row.get(col, ""))
                if i == cursor_row:
                    row_parts.append(f"{Colors.REVERSE}{val.ljust(w)}{Colors.RESET}")
                else:
                    row_parts.append(f"{Colors.DEFAULT}{val.ljust(w)}{Colors.RESET}")
            print(f" {Colors.PROTECTED}│{Colors.RESET} ".join(row_parts), end="", flush=True)

            if i == cursor_row:
                print(f"{Colors.RESET}", end="", flush=True)

        # Message line (height-3): Row count
        self._move_cursor(height - 3, 0)
        if self.rows:
            if len(self.rows) > page_size:
                start_display = self.current_row + 1
                end_display = min(self.current_row + page_size, len(self.rows))
                count_msg = f"ROW {start_display} TO {end_display} OF {len(self.rows)}"
            else:
                count_msg = f"ROW 1 TO {len(self.rows)} OF {len(self.rows)}"
            print(Colors.info(count_msg), end="", flush=True)

        # Separator (height-2)
        self._move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys (height-1)
        self._move_cursor(height - 1, 0)
        hints = [Colors.info("F3=Cancel")]
        if self.add_callback:
            hints.append(Colors.info("F6=Add"))
        hints.append(Colors.info("Enter=Select"))
        if len(self.rows) > page_size:
            if self.current_row > 0:
                hints.append(Colors.info("F7=Bkwd"))
            if self.current_row + page_size < len(self.rows):
                hints.append(Colors.info("F8=Fwd"))
        print("  ".join(hints), end="", flush=True)

    def _read_key(self, fd) -> str:
        """Read a key, handling escape sequences."""
        ch = sys.stdin.read(1)

        if ch == '\x1b':
            seq1 = sys.stdin.read(1)
            if seq1 == '[':
                seq2 = sys.stdin.read(1)
                if seq2 == 'A':
                    return 'UP'
                elif seq2 == 'B':
                    return 'DOWN'
                elif seq2 == '1':
                    seq3 = sys.stdin.read(1)
                    seq4 = sys.stdin.read(1)
                    if seq3 == '3':
                        return 'F3'
                    elif seq3 == '7':
                        return 'F6'
                    elif seq3 == '8':
                        return 'F7'
                    elif seq3 == '9':
                        return 'F8'
                elif seq2 == '5':
                    sys.stdin.read(1)  # ~
                    return 'PGUP'
                elif seq2 == '6':
                    sys.stdin.read(1)  # ~
                    return 'PGDN'
            elif seq1 == 'O':
                seq2 = sys.stdin.read(1)
                if seq2 == 'R':
                    return 'F3'
                elif seq2 == 'Q':
                    return 'F6'
            return 'ESC'

        return ch

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Display the selection list and wait for user selection.

        Returns:
            Selected row as dictionary, or None if cancelled
        """
        if not self.rows:
            return None

        height, width = self._get_terminal_size()
        page_size = self._get_page_size(height)

        actions: Dict[int, str] = {}  # Row index to action code
        cursor_row = 0  # Cursor position relative to visible rows

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                self.render(page_size, height, width, actions, cursor_row)

                tty.setraw(fd)
                key = self._read_key(fd)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if key == 'F3' or key == '\x03':
                    # Cancel
                    break

                elif key == 'F6' and self.add_callback:
                    # Add new item
                    self.clear()
                    result = self.add_callback()
                    if result:
                        # Return the new item as the selection
                        return result
                    # Add was cancelled, return None
                    return None

                elif key in ('\r', '\n'):
                    # Enter - check for action or select current row
                    # First check if any row has 'S' action
                    for idx, action in actions.items():
                        if action.upper() == 'S':
                            self.clear()
                            return self.rows[idx]
                    # Otherwise select current row
                    abs_idx = self.current_row + cursor_row
                    if 0 <= abs_idx < len(self.rows):
                        self.clear()
                        return self.rows[abs_idx]

                elif key == 'UP':
                    if cursor_row > 0:
                        cursor_row -= 1
                    elif self.current_row > 0:
                        self.current_row -= 1

                elif key == 'DOWN':
                    if cursor_row < page_size - 1 and self.current_row + cursor_row < len(self.rows) - 1:
                        cursor_row += 1
                    elif self.current_row + page_size < len(self.rows):
                        self.current_row += 1

                elif key in ('F7', 'PGUP'):
                    if self.current_row > 0:
                        self.current_row = max(0, self.current_row - page_size)
                        cursor_row = 0

                elif key in ('F8', 'PGDN'):
                    if self.current_row + page_size < len(self.rows):
                        self.current_row = min(len(self.rows) - page_size,
                                               self.current_row + page_size)
                        cursor_row = 0

                elif key.upper() == 'S':
                    # Toggle S action on current row
                    abs_idx = self.current_row + cursor_row
                    if abs_idx in actions and actions[abs_idx].upper() == 'S':
                        del actions[abs_idx]
                    else:
                        # Clear other S actions (single select)
                        actions.clear()
                        actions[abs_idx] = 'S'

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.clear()

        return None
