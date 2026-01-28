"""Tabular entry component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Dict, Any, Optional, Callable

from ux3270.panel import Colors, FieldType


class Column:
    """Represents a column definition in a tabular entry."""

    def __init__(self, name: str, width: int = 10, editable: bool = False,
                 field_type: FieldType = FieldType.TEXT,
                 required: bool = False,
                 validator: Optional[Callable[[str], bool]] = None):
        """
        Initialize a column.

        Args:
            name: Column name (used as header and key in results)
            width: Display width
            editable: Whether this column contains input fields
            field_type: Field type for editable columns
            required: Whether editable field is required
            validator: Optional validation function for editable fields
        """
        self.name = name
        self.width = width
        self.editable = editable
        self.field_type = field_type
        self.required = required
        self.validator = validator


class TabularEntry:
    """
    IBM 3270-style tabular entry with mixed static and input columns.

    Displays a table where some columns are editable input fields and
    others are static display text. Supports multi-row data entry.

    Follows CUA conventions:
    - Panel ID at top-left, title centered
    - Column headers in intensified text
    - Static columns in turquoise (protected)
    - Input columns in green with underscore placeholders
    - Tab navigates between editable cells
    - F7/F8 for pagination
    - Enter submits, F3 cancels
    """

    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    HEADER_ROW = 3
    DATA_START_ROW = 5

    HEADER_LINES = 5     # Title + instruction + blank + headers + separator
    FOOTER_LINES = 4     # Error + message + separator + function keys

    def __init__(self, title: str = "", panel_id: str = "",
                 instruction: str = "Enter values and press Enter to submit"):
        """
        Initialize a tabular entry.

        Args:
            title: Table title (displayed in uppercase per CUA)
            panel_id: Optional panel identifier
            instruction: Instruction text
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.columns: List[Column] = []
        self.rows: List[Dict[str, Any]] = []
        self.values: List[Dict[str, str]] = []  # Current input values per row
        self.current_row = 0  # First visible row (for pagination)
        self.error_message = ""

    def add_column(self, name: str, width: int = 10, editable: bool = False,
                   field_type: FieldType = FieldType.TEXT,
                   required: bool = False,
                   validator: Optional[Callable[[str], bool]] = None) -> "TabularEntry":
        """
        Add a column definition.

        Args:
            name: Column name
            width: Display width
            editable: Whether this column is an input field
            field_type: Field type (TEXT, NUMERIC, etc.)
            required: Whether field is required (editable columns only)
            validator: Optional validation function

        Returns:
            Self for method chaining
        """
        self.columns.append(Column(name, width, editable, field_type, required, validator))
        return self

    def add_row(self, **values) -> "TabularEntry":
        """
        Add a data row.

        Args:
            **values: Column name to value mapping

        Returns:
            Self for method chaining
        """
        self.rows.append(values)
        # Initialize editable values
        row_values = {}
        for col in self.columns:
            if col.editable:
                row_values[col.name] = str(values.get(col.name, ""))
        self.values.append(row_values)
        return self

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

    def _get_editable_cells(self, page_size: int) -> List[tuple]:
        """Get list of (row_idx, col_idx, col) for editable cells on current page."""
        cells = []
        end_row = min(self.current_row + page_size, len(self.rows))
        for row_idx in range(self.current_row, end_row):
            for col_idx, col in enumerate(self.columns):
                if col.editable:
                    cells.append((row_idx, col_idx, col))
        return cells

    def _get_col_position(self, col_idx: int) -> int:
        """Get the starting column position for a column index."""
        pos = 2  # Initial indent
        for i, col in enumerate(self.columns):
            if i == col_idx:
                return pos
            pos += col.width + 3  # width + separator
        return pos

    def _render(self, page_size: int, height: int, width: int,
                current_cell: int, cursor_pos: int, cells: List[tuple],
                full_redraw: bool = True):
        """Render the tabular entry."""
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
            self._move_cursor(self.INSTRUCTION_ROW, 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

            # Row 3: Column headers
            self._move_cursor(self.HEADER_ROW, 0)
            header_parts = []
            for col in self.columns:
                # Show * for required editable columns
                if col.editable and col.required:
                    header_parts.append(Colors.header(f"*{col.name}"[:col.width].ljust(col.width)))
                else:
                    header_parts.append(Colors.header(col.name[:col.width].ljust(col.width)))
            print("  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(header_parts), end="", flush=True)

            # Row 4: Separator
            self._move_cursor(self.HEADER_ROW + 1, 0)
            sep_parts = ["─" * col.width for col in self.columns]
            print(f"  {Colors.PROTECTED}" + "─┼─".join(sep_parts) + f"{Colors.RESET}", end="", flush=True)

            # Data rows
            end_row = min(self.current_row + page_size, len(self.rows))
            for display_idx, row_idx in enumerate(range(self.current_row, end_row)):
                row = self.rows[row_idx]
                self._move_cursor(self.DATA_START_ROW + display_idx, 0)

                cell_parts = []
                for col_idx, col in enumerate(self.columns):
                    if col.editable:
                        # Input field - green with underscore placeholder
                        val = self.values[row_idx].get(col.name, "")
                        display_val = val[:col.width].ljust(col.width)
                        remaining = col.width - len(val)
                        if remaining > 0:
                            display_val = f"{Colors.INPUT}{val}{Colors.DIM}{'_' * remaining}{Colors.RESET}"
                        else:
                            display_val = f"{Colors.INPUT}{val[:col.width]}{Colors.RESET}"
                        cell_parts.append(display_val)
                    else:
                        # Static field - turquoise
                        val = str(row.get(col.name, ""))[:col.width].ljust(col.width)
                        cell_parts.append(f"{Colors.PROTECTED}{val}{Colors.RESET}")

                print("  " + f" {Colors.PROTECTED}│{Colors.RESET} ".join(cell_parts), end="", flush=True)

            # Error line (height-4)
            self._move_cursor(height - 4, 0)
            print(" " * width, end="", flush=True)  # Clear line
            if self.error_message:
                self._move_cursor(height - 4, 0)
                print(Colors.error(self.error_message), end="", flush=True)

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
            hints = [Colors.info("F3=Cancel"), Colors.info("Enter=Submit")]
            if len(self.rows) > page_size:
                if self.current_row > 0:
                    hints.append(Colors.info("F7=Up"))
                if self.current_row + page_size < len(self.rows):
                    hints.append(Colors.info("F8=Down"))
            print("  ".join(hints), end="", flush=True)
        else:
            # Partial update: refresh only editable cells on current page
            end_row = min(self.current_row + page_size, len(self.rows))
            for display_idx, row_idx in enumerate(range(self.current_row, end_row)):
                for col_idx, col in enumerate(self.columns):
                    if col.editable:
                        col_pos = self._get_col_position(col_idx)
                        self._move_cursor(self.DATA_START_ROW + display_idx, col_pos)
                        val = self.values[row_idx].get(col.name, "")
                        remaining = col.width - len(val)
                        if remaining > 0:
                            print(f"{Colors.INPUT}{val}{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)
                        else:
                            print(f"{Colors.INPUT}{val[:col.width]}{Colors.RESET}", end="", flush=True)

        # Position cursor at current cell
        if cells and 0 <= current_cell < len(cells):
            row_idx, col_idx, col = cells[current_cell]
            display_row = row_idx - self.current_row
            col_pos = self._get_col_position(col_idx)
            self._move_cursor(self.DATA_START_ROW + display_row, col_pos + cursor_pos)

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
                elif seq2 == 'C':
                    return 'RIGHT'
                elif seq2 == 'D':
                    return 'LEFT'
                elif seq2 == 'H':
                    return 'HOME'
                elif seq2 == 'F':
                    return 'END'
                elif seq2 == '1':
                    seq3 = sys.stdin.read(1)
                    seq4 = sys.stdin.read(1)
                    if seq3 == '3':
                        return 'F3'
                    elif seq3 == '8':
                        return 'F7'
                    elif seq3 == '9':
                        return 'F8'
                    elif seq3 == '~':
                        return 'HOME'
                elif seq2 == '2':
                    sys.stdin.read(1)
                    return 'INSERT'
                elif seq2 == '3':
                    sys.stdin.read(1)
                    return 'DELETE'
                elif seq2 == '4':
                    sys.stdin.read(1)
                    return 'END'
            elif seq1 == 'O':
                seq2 = sys.stdin.read(1)
                if seq2 == 'R':
                    return 'F3'
                elif seq2 == 'H':
                    return 'HOME'
                elif seq2 == 'F':
                    return 'END'
            return 'ESC'

        return ch

    def _validate(self) -> Optional[tuple]:
        """
        Validate all editable fields.

        Returns:
            (row_idx, col, error_message) for first validation failure,
            or None if all valid.
        """
        for row_idx, row_values in enumerate(self.values):
            for col in self.columns:
                if not col.editable:
                    continue

                val = row_values.get(col.name, "")

                # Required check
                if col.required and not val.strip():
                    return (row_idx, col, f"{col.name} is required")

                # Numeric check
                if col.field_type == FieldType.NUMERIC and val.strip():
                    if not val.replace('.', '').replace('-', '').isdigit():
                        return (row_idx, col, f"{col.name} must be numeric")

                # Custom validator
                if col.validator and val.strip():
                    if not col.validator(val):
                        return (row_idx, col, f"{col.name} is invalid")

        return None

    def show(self) -> Optional[List[Dict[str, Any]]]:
        """
        Display the tabular entry and process user input.

        Returns:
            List of dicts with row data (original + edited values),
            or None if cancelled.
        """
        if not self.rows:
            return []

        height, width = self._get_terminal_size()
        page_size = self._get_page_size(height)

        cells = self._get_editable_cells(page_size)
        if not cells:
            # No editable cells, just display
            self._render(page_size, height, width, 0, 0, [], full_redraw=True)
            return [dict(self.rows[i], **self.values[i]) for i in range(len(self.rows))]

        current_cell = 0
        cursor_pos = 0
        insert_mode = True
        need_full_redraw = True

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                # Recalculate cells if page changed
                cells = self._get_editable_cells(page_size)
                if not cells:
                    break

                # Clamp current_cell to valid range
                if current_cell >= len(cells):
                    current_cell = len(cells) - 1
                if current_cell < 0:
                    current_cell = 0

                row_idx, col_idx, col = cells[current_cell]
                val = self.values[row_idx].get(col.name, "")

                # Clamp cursor position
                cursor_pos = min(cursor_pos, len(val))

                self._render(page_size, height, width, current_cell, cursor_pos,
                            cells, full_redraw=need_full_redraw)
                need_full_redraw = False

                tty.setraw(fd)
                key = self._read_key()
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if key == 'F3' or key == '\x03':
                    self._clear()
                    return None

                elif key in ('\r', '\n'):
                    # Validate and submit
                    validation_error = self._validate()
                    if validation_error:
                        err_row_idx, err_col, err_msg = validation_error
                        self.error_message = err_msg

                        # Find the cell index for the error field
                        for i, (r_idx, c_idx, c) in enumerate(cells):
                            if r_idx == err_row_idx and c.name == err_col.name:
                                # Check if error row is on current page
                                if err_row_idx < self.current_row or err_row_idx >= self.current_row + page_size:
                                    self.current_row = err_row_idx
                                    cells = self._get_editable_cells(page_size)
                                    for i, (r_idx, c_idx, c) in enumerate(cells):
                                        if r_idx == err_row_idx and c.name == err_col.name:
                                            current_cell = i
                                            break
                                else:
                                    current_cell = i
                                cursor_pos = 0
                                break
                        need_full_redraw = True
                    else:
                        # Success - return results
                        self._clear()
                        return [dict(self.rows[i], **self.values[i]) for i in range(len(self.rows))]

                elif key == '\t':
                    # Tab to next editable cell
                    self.error_message = ""
                    if current_cell < len(cells) - 1:
                        current_cell += 1
                        cursor_pos = 0
                    row_idx, col_idx, col = cells[current_cell]
                    # Check if we need to scroll
                    if row_idx >= self.current_row + page_size:
                        self.current_row = row_idx
                        need_full_redraw = True

                elif key == '\x1b[Z' or key == 'BACKTAB':  # Shift+Tab
                    self.error_message = ""
                    if current_cell > 0:
                        current_cell -= 1
                        cursor_pos = 0
                    row_idx, col_idx, col = cells[current_cell]
                    if row_idx < self.current_row:
                        self.current_row = row_idx
                        need_full_redraw = True

                elif key == 'UP':
                    # Move to same column in previous row
                    self.error_message = ""
                    row_idx, col_idx, col = cells[current_cell]
                    for i, (r, c, _) in enumerate(cells):
                        if r == row_idx - 1 and c == col_idx:
                            current_cell = i
                            cursor_pos = 0
                            if r < self.current_row:
                                self.current_row = r
                                need_full_redraw = True
                            break

                elif key == 'DOWN':
                    # Move to same column in next row
                    self.error_message = ""
                    row_idx, col_idx, col = cells[current_cell]
                    for i, (r, c, _) in enumerate(cells):
                        if r == row_idx + 1 and c == col_idx:
                            current_cell = i
                            cursor_pos = 0
                            if r >= self.current_row + page_size:
                                self.current_row = r - page_size + 1
                                need_full_redraw = True
                            break

                elif key == 'LEFT':
                    if cursor_pos > 0:
                        cursor_pos -= 1

                elif key == 'RIGHT':
                    if cursor_pos < len(val):
                        cursor_pos += 1

                elif key == 'HOME':
                    cursor_pos = 0

                elif key == 'END':
                    cursor_pos = len(val)

                elif key == 'INSERT':
                    insert_mode = not insert_mode

                elif key == 'DELETE':
                    if cursor_pos < len(val):
                        val = val[:cursor_pos] + val[cursor_pos + 1:]
                        self.values[row_idx][col.name] = val

                elif key == '\x7f' or key == '\x08':  # Backspace
                    if cursor_pos > 0:
                        val = val[:cursor_pos - 1] + val[cursor_pos:]
                        self.values[row_idx][col.name] = val
                        cursor_pos -= 1

                elif key == '\x05':  # Ctrl+E - Erase to end of field
                    val = val[:cursor_pos]
                    self.values[row_idx][col.name] = val

                elif len(key) == 1 and key.isprintable():
                    # Type character
                    if col.field_type == FieldType.NUMERIC:
                        if not (key.isdigit() or key in '.-'):
                            continue

                    if insert_mode:
                        if len(val) < col.width:
                            val = val[:cursor_pos] + key + val[cursor_pos:]
                            cursor_pos += 1
                    else:
                        if cursor_pos < col.width:
                            val = val[:cursor_pos] + key + val[cursor_pos + 1:]
                            cursor_pos += 1

                    self.values[row_idx][col.name] = val

                elif key == 'F7':
                    if self.current_row > 0:
                        self.current_row = max(0, self.current_row - page_size)
                        current_cell = 0
                        cursor_pos = 0
                        need_full_redraw = True

                elif key == 'F8':
                    if self.current_row + page_size < len(self.rows):
                        self.current_row = min(len(self.rows) - page_size,
                                              self.current_row + page_size)
                        current_cell = 0
                        cursor_pos = 0
                        need_full_redraw = True

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return None
