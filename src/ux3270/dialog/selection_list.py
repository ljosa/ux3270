"""Selection list component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Optional, Dict, Any, Callable, Literal

from ux3270.panel import Colors


class SelectionColumn:
    """Represents a column definition in a selection list."""

    def __init__(self, name: str, width: Optional[int] = None,
                 align: Literal["left", "right"] = "left"):
        self.name = name
        self.width = width
        self.align = align


class SelectionList:
    """
    CUA selection list for F4=Prompt functionality.

    Displays a scrollable list where user can select an item by
    typing 'S' next to the item and pressing Enter.

    Follows CUA conventions:
    - Panel ID at top-left, title centered
    - Column headers in intensified text
    - Action input field per row for selection (type S=Select)
    - F3=Cancel, F6=Add (optional), F7=Backward, F8=Forward
    - Enter with 'S' action code selects the item
    """

    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    HEADER_ROW = 3
    DATA_START_ROW = 5

    HEADER_LINES = 5     # Title + instruction + blank + headers + separator
    FOOTER_LINES = 3     # Message + separator + function keys

    def __init__(self, title: str = "SELECTION LIST", panel_id: str = "",
                 instruction: str = "Type S to select item, press Enter"):
        """
        Initialize a selection list.

        Args:
            title: List title (displayed in uppercase per CUA)
            panel_id: Optional panel identifier
            instruction: Instruction text
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self._columns: List[SelectionColumn] = []
        self.rows: List[Dict[str, Any]] = []
        self.col_widths: List[int] = []
        self.current_row = 0  # First visible row
        self.action_inputs: List[str] = []  # Action code per row
        self.add_callback: Optional[Callable] = None

    def add_column(self, name: str, width: Optional[int] = None,
                   align: Literal["left", "right"] = "left") -> "SelectionList":
        """
        Add a column definition.

        Args:
            name: Column name (used as header and key in row data)
            width: Display width (None = auto-calculate from content)
            align: Text alignment ("left" or "right")

        Returns:
            Self for method chaining
        """
        self._columns.append(SelectionColumn(name, width, align))
        return self

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
        self.action_inputs.append("")
        return self

    def add_rows(self, rows: List[Dict[str, Any]]) -> "SelectionList":
        """
        Add multiple rows to the selection list.

        Args:
            rows: List of dictionaries with column values

        Returns:
            Self for method chaining
        """
        for row in rows:
            self.rows.append(row)
            self.action_inputs.append("")
        return self

    def _calculate_widths(self):
        """Calculate column widths based on content."""
        if not self._columns:
            return

        self.col_widths = []
        for col in self._columns:
            if col.width is not None:
                self.col_widths.append(col.width)
            else:
                self.col_widths.append(len(col.name))

        for row in self.rows:
            for i, col in enumerate(self._columns):
                if col.name in row and col.width is None:
                    val_len = len(str(row[col.name]))
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

    def _clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def _render(self, page_size: int, height: int, width: int,
                cursor_row: int, full_redraw: bool = True):
        """Render the selection list.

        Args:
            page_size: Number of data rows per page
            height: Terminal height
            width: Terminal width
            cursor_row: Current cursor row (relative to visible rows)
            full_redraw: If True, clear and redraw everything
        """
        self._calculate_widths()

        if full_redraw:
            self._clear()

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

            # Row 3: Column headers with Opt column
            if self._columns:
                self._move_cursor(self.HEADER_ROW, 0)
                # Opt column header (2 chars)
                header_parts = [Colors.header("Opt")]
                for i, col in enumerate(self._columns):
                    w = self.col_widths[i] if i < len(self.col_widths) else len(col.name)
                    if col.align == "right":
                        header_parts.append(Colors.header(col.name.rjust(w)))
                    else:
                        header_parts.append(Colors.header(col.name.ljust(w)))
                print("  " + "  ".join(header_parts), end="", flush=True)

                # Row 4: Separator
                self._move_cursor(self.HEADER_ROW + 1, 0)
                sep_parts = ["───"]  # Opt column (3 chars to match header)
                for w in self.col_widths:
                    sep_parts.append("─" * w)
                print(f"  {Colors.PROTECTED}{'──'.join(sep_parts)}{Colors.RESET}", end="", flush=True)

            # Data rows
            end_row = min(self.current_row + page_size, len(self.rows))
            visible_rows = self.rows[self.current_row:end_row]

            for i, row in enumerate(visible_rows):
                abs_idx = self.current_row + i
                self._move_cursor(self.DATA_START_ROW + i, 0)

                # Opt input field (2 chars visible, padded to 3 for alignment)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                if action_val:
                    action_display = action_val.ljust(3)
                else:
                    action_display = "__ "  # 2 underscores + space
                print(f"  {Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

                # Data columns
                for j, col in enumerate(self._columns):
                    w = self.col_widths[j] if j < len(self.col_widths) else 10
                    val = str(row.get(col.name, ""))
                    if col.align == "right":
                        formatted = val.rjust(w)
                    else:
                        formatted = val.ljust(w)
                    print(f"  {Colors.DEFAULT}{formatted}{Colors.RESET}", end="", flush=True)

            # Message line (height-3): Row count
            self._move_cursor(height - 3, 0)
            if self.rows:
                if len(self.rows) > page_size:
                    start_display = self.current_row + 1
                    end_display = min(self.current_row + page_size, len(self.rows))
                    count_msg = f"ROW {start_display} TO {end_display} OF {len(self.rows)}"
                else:
                    count_msg = f"ROWS {len(self.rows)}"
                self._move_cursor(height - 3, width - len(count_msg) - 1)
                print(Colors.info(count_msg), end="", flush=True)

            # Separator (height-2)
            self._move_cursor(height - 2, 0)
            print(Colors.dim("─" * width), end="", flush=True)

            # Function keys (height-1)
            self._move_cursor(height - 1, 0)
            hints = [Colors.info("F3=Cancel")]
            if self.add_callback:
                hints.append(Colors.info("F6=Add"))
            if len(self.rows) > page_size:
                if self.current_row > 0:
                    hints.append(Colors.info("F7=Up"))
                if self.current_row + page_size < len(self.rows):
                    hints.append(Colors.info("F8=Down"))
            print("  ".join(hints), end="", flush=True)
        else:
            # Partial update: refresh Opt input fields
            end_row = min(self.current_row + page_size, len(self.rows))
            for i in range(end_row - self.current_row):
                abs_idx = self.current_row + i
                self._move_cursor(self.DATA_START_ROW + i, 2)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                if action_val:
                    action_display = action_val.ljust(3)
                else:
                    action_display = "__ "
                print(f"{Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

        # Position cursor at current action input field
        if 0 <= cursor_row < page_size and cursor_row + self.current_row < len(self.rows):
            self._move_cursor(self.DATA_START_ROW + cursor_row, 2)

    def _read_key(self) -> str:
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
                    sys.stdin.read(1)  # ~
                    if seq3 == '3':
                        return 'F3'
                    elif seq3 == '7':
                        return 'F6'
                    elif seq3 == '8':
                        return 'F7'
                    elif seq3 == '9':
                        return 'F8'
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

        cursor_row = 0  # Cursor position relative to visible rows
        need_full_redraw = True

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                self._render(page_size, height, width, cursor_row,
                            full_redraw=need_full_redraw)
                need_full_redraw = False

                tty.setraw(fd)
                key = self._read_key()
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if key == 'F3' or key == '\x03':
                    self._clear()
                    return None

                elif key == 'F6' and self.add_callback:
                    self._clear()
                    result = self.add_callback()
                    if result:
                        return result
                    return None

                elif key == 'F7':
                    if self.current_row > 0:
                        self.current_row = max(0, self.current_row - page_size)
                        cursor_row = 0
                        need_full_redraw = True

                elif key == 'F8':
                    if self.current_row + page_size < len(self.rows):
                        self.current_row = min(len(self.rows) - 1, self.current_row + page_size)
                        cursor_row = 0
                        need_full_redraw = True

                elif key == '\t':
                    # Tab to next row
                    abs_row = self.current_row + cursor_row
                    if abs_row < len(self.rows) - 1:
                        if cursor_row < page_size - 1:
                            cursor_row += 1
                        elif self.current_row + page_size < len(self.rows):
                            self.current_row += 1
                            need_full_redraw = True

                elif key == 'UP':
                    if cursor_row > 0:
                        cursor_row -= 1
                    elif self.current_row > 0:
                        self.current_row -= 1
                        need_full_redraw = True

                elif key == 'DOWN':
                    abs_row = self.current_row + cursor_row
                    if cursor_row < page_size - 1 and abs_row < len(self.rows) - 1:
                        cursor_row += 1
                    elif self.current_row + page_size < len(self.rows):
                        self.current_row += 1
                        need_full_redraw = True

                elif key in ('\r', '\n'):
                    # Enter - find row with 'S' action
                    for i, action in enumerate(self.action_inputs):
                        if action.upper() == 'S':
                            self._clear()
                            return self.rows[i]
                    # No selection made, continue

                elif key == '\x7f' or key == '\x08':  # Backspace
                    abs_row = self.current_row + cursor_row
                    if abs_row < len(self.action_inputs):
                        self.action_inputs[abs_row] = ""

                elif len(key) == 1 and key.upper() == 'S':
                    # Type S - clear others (single select) and set this one
                    abs_row = self.current_row + cursor_row
                    for i in range(len(self.action_inputs)):
                        self.action_inputs[i] = ""
                    if abs_row < len(self.action_inputs):
                        self.action_inputs[abs_row] = "S"
                        # Auto-advance
                        if cursor_row < page_size - 1 and abs_row < len(self.rows) - 1:
                            cursor_row += 1
                        elif self.current_row + page_size < len(self.rows):
                            self.current_row += 1
                            need_full_redraw = True

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
