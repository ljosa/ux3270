"""Work-with list component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Dict, Any, Optional, Callable

from ux3270.panel import Colors


class WorkWithList:
    """
    IBM 3270-style work-with list with action codes.

    Displays a list of records with an action input field per row.
    Users type action codes (2=Change, 4=Delete, etc.) and press Enter
    to process multiple actions at once.

    Follows CUA conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Action codes legend
    - Action input field per row
    - F6=Add for adding new records
    - F7/F8 for pagination
    - F3 to exit
    """

    # CUA layout constants
    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    ACTIONS_ROW = 3      # Action codes legend
    HEADER_ROW = 5       # Column headers
    DATA_START_ROW = 7   # First data row

    # Lines reserved for chrome
    HEADER_LINES = 7     # Title + instruction + blank + actions + blank + header + separator
    FOOTER_LINES = 3     # Message + separator + function keys

    def __init__(self, title: str = "", columns: List[str] = None,
                 panel_id: str = "", instruction: str = ""):
        """
        Initialize a work-with list.

        Args:
            title: List title (displayed in uppercase per IBM convention)
            columns: List of column headers (excluding the Action column)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Instruction text (default provided if empty)
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction or "Type action code, press Enter to process."
        self.columns = columns or []
        self.rows: List[Dict[str, Any]] = []
        self.actions: Dict[str, str] = {}  # code -> description
        self.add_callback: Optional[Callable] = None
        self.current_row = 0  # First visible row index
        self.action_inputs: List[str] = []  # Action code entered per row

    def add_action(self, code: str, description: str) -> "WorkWithList":
        """
        Define an available action code.

        Args:
            code: Single character or short code (e.g., "2", "4", "D")
            description: Description shown in legend (e.g., "Change", "Delete")

        Returns:
            Self for method chaining
        """
        self.actions[code.upper()] = description
        return self

    def set_add_callback(self, callback: Callable) -> "WorkWithList":
        """
        Set callback for F6=Add.

        Args:
            callback: Function to call when F6 is pressed. Should handle
                     adding a new record (e.g., show a Form).

        Returns:
            Self for method chaining
        """
        self.add_callback = callback
        return self

    def add_row(self, **values) -> "WorkWithList":
        """
        Add a row to the list.

        Args:
            **values: Column name -> value pairs

        Returns:
            Self for method chaining
        """
        self.rows.append(values)
        self.action_inputs.append("")
        return self

    def _calculate_widths(self) -> List[int]:
        """Calculate column widths based on content."""
        if not self.columns:
            return []

        widths = [len(col) for col in self.columns]

        for row in self.rows:
            for i, col in enumerate(self.columns):
                if col in row:
                    widths[i] = max(widths[i], len(str(row[col])))

        return widths

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
                cursor_row: int, cursor_col: int, full_redraw: bool = True):
        """Render the work-with list.

        Args:
            full_redraw: If True, clear screen and redraw everything.
                        If False, only update action fields and cursor.
        """
        col_widths = self._calculate_widths()

        if full_redraw:
            self._clear()

            # Row 0: Panel ID (left) and Title (centered)
            self._move_cursor(self.TITLE_ROW, 0)
            if self.panel_id:
                print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
            if self.title:
                title_col = max(0, (width - len(self.title)) // 2)
                self._move_cursor(self.TITLE_ROW, title_col)
                print(f"{Colors.title(self.title)}", end="", flush=True)

            # Row 1: Instruction
            self._move_cursor(self.INSTRUCTION_ROW, 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

            # Row 3: Action codes legend
            if self.actions:
                self._move_cursor(self.ACTIONS_ROW, 2)
                legend_parts = [f"{code}={desc}" for code, desc in self.actions.items()]
                print(f"{Colors.PROTECTED}{('  ').join(legend_parts)}{Colors.RESET}", end="", flush=True)

            # Row 5: Column headers
            self._move_cursor(self.HEADER_ROW, 0)
            header_parts = [Colors.header("Act")]
            for i, col in enumerate(self.columns):
                w = col_widths[i] if i < len(col_widths) else len(col)
                header_parts.append(Colors.header(col.ljust(w)))
            print("  " + "  ".join(header_parts), end="", flush=True)

            # Row 6: Separator
            self._move_cursor(self.HEADER_ROW + 1, 0)
            sep_parts = ["───"]  # Action column
            for w in col_widths:
                sep_parts.append("─" * w)
            print(f"  {Colors.PROTECTED}{'──'.join(sep_parts)}{Colors.RESET}", end="", flush=True)

            # Data rows (full render includes row data)
            end_row = min(self.current_row + page_size, len(self.rows))
            visible_rows = self.rows[self.current_row:end_row]

            for i, row in enumerate(visible_rows):
                abs_idx = self.current_row + i
                self._move_cursor(self.DATA_START_ROW + i, 0)

                # Action input field (green, underscore if empty)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                action_display = action_val.ljust(1) if action_val else "_"
                print(f"  {Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

                # Data columns
                for j, col in enumerate(self.columns):
                    w = col_widths[j] if j < len(col_widths) else 10
                    val = str(row.get(col, "")).ljust(w)
                    print(f"  {Colors.DEFAULT}{val}{Colors.RESET}", end="", flush=True)

            # Message line (height-3): Row count
            self._move_cursor(height - 3, 0)
            if self.rows:
                if len(self.rows) > page_size:
                    start_display = self.current_row + 1
                    end_display = min(self.current_row + page_size, len(self.rows))
                    count_msg = f"ROW {start_display} TO {end_display} OF {len(self.rows)}"
                else:
                    count_msg = f"ROWS {len(self.rows)}"
                # Right-align the count message
                self._move_cursor(height - 3, width - len(count_msg) - 1)
                print(Colors.info(count_msg), end="", flush=True)

            # Separator (height-2)
            self._move_cursor(height - 2, 0)
            print(Colors.dim("─" * width), end="", flush=True)

            # Function keys (height-1)
            self._move_cursor(height - 1, 0)
            hints = [Colors.info("F3=Exit")]
            if self.add_callback:
                hints.append(Colors.info("F6=Add"))
            if len(self.rows) > page_size:
                if self.current_row > 0:
                    hints.append(Colors.info("F7=Up"))
                if self.current_row + page_size < len(self.rows):
                    hints.append(Colors.info("F8=Down"))
            print("  ".join(hints), end="", flush=True)
        else:
            # Partial update: just refresh action input fields
            end_row = min(self.current_row + page_size, len(self.rows))
            for i in range(end_row - self.current_row):
                abs_idx = self.current_row + i
                self._move_cursor(self.DATA_START_ROW + i, 2)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                action_display = action_val.ljust(1) if action_val else "_"
                print(f"{Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

        # Position cursor at current action input field
        if 0 <= cursor_row < page_size and cursor_row + self.current_row < len(self.rows):
            self._move_cursor(self.DATA_START_ROW + cursor_row, 2 + cursor_col)

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
                    seq4 = sys.stdin.read(1)  # ~
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

    def show(self) -> Optional[List[Dict[str, Any]]]:
        """
        Display the work-with list and process user input.

        Returns:
            List of {"action": code, "row": row_data} for each row with an action,
            or None if user exits with F3.
        """
        height, width = self._get_terminal_size()
        page_size = self._get_page_size(height)

        # Cursor position within visible area
        cursor_row = 0  # Row within current page
        cursor_col = 0  # Column within action field (always 0 for single char)
        need_full_redraw = True  # First render is always full

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                self._render(page_size, height, width, cursor_row, cursor_col,
                            full_redraw=need_full_redraw)
                need_full_redraw = False  # Reset after render
                tty.setraw(fd)

                key = self._read_key()
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                abs_row = self.current_row + cursor_row

                if key == 'F3' or key == '\x03':  # F3 or Ctrl+C
                    self._clear()
                    return None

                elif key == 'F6' and self.add_callback:
                    self._clear()
                    self.add_callback()
                    # Return empty list so caller's loop rebuilds with fresh data
                    return []

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

                elif key == 'UP':
                    if cursor_row > 0:
                        cursor_row -= 1
                        # No full redraw needed - just move cursor
                    elif self.current_row > 0:
                        self.current_row -= 1
                        need_full_redraw = True  # Page scrolled

                elif key == 'DOWN':
                    if cursor_row < page_size - 1 and abs_row < len(self.rows) - 1:
                        cursor_row += 1
                        # No full redraw needed - just move cursor
                    elif self.current_row + page_size < len(self.rows):
                        self.current_row += 1
                        need_full_redraw = True  # Page scrolled

                elif key == '\t':  # Tab - move to next row
                    if abs_row < len(self.rows) - 1:
                        if cursor_row < page_size - 1:
                            cursor_row += 1
                        elif self.current_row + page_size < len(self.rows):
                            self.current_row += 1
                            cursor_row = 0
                            need_full_redraw = True

                elif key in ('\r', '\n'):  # Enter - process actions
                    results = []
                    for i, action in enumerate(self.action_inputs):
                        if action and action.upper() in self.actions:
                            results.append({
                                "action": action.upper(),
                                "row": self.rows[i]
                            })
                    if results:
                        self._clear()
                        return results
                    # If no actions entered, just continue

                elif key == '\x7f' or key == '\x08':  # Backspace/Delete
                    if abs_row < len(self.action_inputs):
                        self.action_inputs[abs_row] = ""
                    # Partial redraw will update action field

                elif len(key) == 1 and key.isprintable():
                    # Type action code
                    if abs_row < len(self.action_inputs):
                        self.action_inputs[abs_row] = key.upper()
                        # Auto-advance to next row
                        if cursor_row < page_size - 1 and abs_row < len(self.rows) - 1:
                            cursor_row += 1
                        elif self.current_row + page_size < len(self.rows):
                            self.current_row += 1
                            need_full_redraw = True

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def refresh_data(self, rows: List[Dict[str, Any]]):
        """
        Refresh the list data (e.g., after F6=Add).

        Args:
            rows: New list of row data
        """
        self.rows = rows
        self.action_inputs = [""] * len(rows)
        self.current_row = 0
