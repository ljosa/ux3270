"""Work-with list component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Dict, Any, Optional, Callable, Literal

from ux3270.panel import Colors, FieldType


class HeaderField:
    """Represents a header field definition."""

    def __init__(self, label: str, length: int = 10, default: str = "",
                 field_type: FieldType = FieldType.TEXT):
        self.label = label
        self.length = length
        self.default = default
        self.field_type = field_type
        self.value = default


class ListColumn:
    """Represents a column definition in a work-with list."""

    def __init__(self, name: str, width: Optional[int] = None,
                 align: Literal["left", "right"] = "left"):
        """
        Initialize a column.

        Args:
            name: Column name (used as header and key in row data)
            width: Display width (None = auto-calculate from content)
            align: Text alignment ("left" or "right")
        """
        self.name = name
        self.width = width
        self.align = align


class WorkWithList:
    """
    IBM 3270-style work-with list with action codes.

    Displays a list of records with an action input field per row.
    Users type action codes (2=Change, 4=Delete, etc.) and press Enter
    to process multiple actions at once.

    Supports optional header fields above the list for filtering/positioning.

    Follows CUA conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Optional header fields for filtering
    - Action codes legend
    - Action input field per row
    - F6=Add for adding new records
    - F7/F8 for pagination
    - F3 to exit
    """

    # Base CUA layout constants (adjusted dynamically for header fields)
    TITLE_ROW = 0
    INSTRUCTION_ROW = 1

    # Lines reserved for chrome (base, without header fields)
    BASE_HEADER_LINES = 7  # Title + instruction + blank + actions + blank + header + separator
    FOOTER_LINES = 3       # Message + separator + function keys

    def __init__(self, title: str = "", columns: Optional[List[str]] = None,
                 panel_id: str = "", instruction: str = ""):
        """
        Initialize a work-with list.

        Args:
            title: List title (displayed in uppercase per IBM convention)
            columns: List of column headers (excluding the Action column).
                    For more control, use add_column() instead.
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Instruction text (default provided if empty)
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction or "Type action code, press Enter to process."
        # Convert simple column names to ListColumn objects
        self._columns: List[ListColumn] = []
        if columns:
            for col in columns:
                self._columns.append(ListColumn(col))
        self.rows: List[Dict[str, Any]] = []
        self.actions: Dict[str, str] = {}  # code -> description
        self.add_callback: Optional[Callable] = None
        self.current_row = 0  # First visible row index
        self.action_inputs: List[str] = []  # Action code entered per row
        self.header_fields: List[HeaderField] = []

    def add_column(self, name: str, width: Optional[int] = None,
                   align: Literal["left", "right"] = "left") -> "WorkWithList":
        """
        Add a column definition.

        Args:
            name: Column name (used as header and key in row data)
            width: Display width (None = auto-calculate from content)
            align: Text alignment ("left" or "right")

        Returns:
            Self for method chaining
        """
        self._columns.append(ListColumn(name, width, align))
        return self

    def _get_layout(self) -> Dict[str, int]:
        """Calculate layout row positions based on header fields."""
        header_field_rows = len(self.header_fields)
        return {
            "title": 0,
            "instruction": 1,
            "header_fields_start": 3 if header_field_rows > 0 else -1,
            "actions": 3 + header_field_rows + (1 if header_field_rows > 0 else 0),
            "column_headers": 3 + header_field_rows + (1 if header_field_rows > 0 else 0) + 2,
            "data_start": 3 + header_field_rows + (1 if header_field_rows > 0 else 0) + 4,
            "header_lines": self.BASE_HEADER_LINES + header_field_rows + (1 if header_field_rows > 0 else 0),
        }

    def add_header_field(self, label: str, length: int = 10, default: str = "",
                         field_type: FieldType = FieldType.TEXT) -> "WorkWithList":
        """
        Add a header field above the list (for filtering/positioning).

        Args:
            label: Field label
            length: Field length
            default: Default value
            field_type: Field type (TEXT, NUMERIC)

        Returns:
            Self for method chaining
        """
        self.header_fields.append(HeaderField(label, length, default, field_type))
        return self

    def get_header_values(self) -> Dict[str, str]:
        """Get current header field values."""
        return {f.label: f.value for f in self.header_fields}

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
        if not self._columns:
            return []

        widths = []
        for col in self._columns:
            if col.width is not None:
                widths.append(col.width)
            else:
                widths.append(len(col.name))

        for row in self.rows:
            for i, col in enumerate(self._columns):
                if col.name in row and col.width is None:
                    widths[i] = max(widths[i], len(str(row[col.name])))

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
        layout = self._get_layout()
        return max(1, height - layout["header_lines"] - self.FOOTER_LINES)

    def _clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def _render(self, page_size: int, height: int, width: int,
                cursor_row: int, cursor_col: int, in_header: bool = False,
                header_field_idx: int = 0, header_cursor_pos: int = 0,
                full_redraw: bool = True):
        """Render the work-with list.

        Args:
            full_redraw: If True, clear screen and redraw everything.
                        If False, only update action fields and cursor.
        """
        layout = self._get_layout()
        col_widths = self._calculate_widths()

        if full_redraw:
            self._clear()

            # Row 0: Panel ID (left) and Title (centered)
            self._move_cursor(layout["title"], 0)
            if self.panel_id:
                print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
            if self.title:
                title_col = max(0, (width - len(self.title)) // 2)
                self._move_cursor(layout["title"], title_col)
                print(f"{Colors.title(self.title)}", end="", flush=True)

            # Row 1: Instruction
            self._move_cursor(layout["instruction"], 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

            # Header fields (if any)
            if self.header_fields:
                for i, field in enumerate(self.header_fields):
                    self._move_cursor(layout["header_fields_start"] + i, 2)
                    print(f"{Colors.PROTECTED}{field.label} . . .{Colors.RESET} ", end="", flush=True)
                    # Input field
                    val = field.value
                    remaining = field.length - len(val)
                    print(f"{Colors.INPUT}{val}", end="", flush=True)
                    if remaining > 0:
                        print(f"{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)

            # Action codes legend
            if self.actions:
                self._move_cursor(layout["actions"], 2)
                legend_parts = [f"{code}={desc}" for code, desc in self.actions.items()]
                print(f"{Colors.PROTECTED}{('  ').join(legend_parts)}{Colors.RESET}", end="", flush=True)

            # Column headers
            self._move_cursor(layout["column_headers"], 0)
            header_parts = [Colors.header("Act")]
            for i, col in enumerate(self._columns):
                w = col_widths[i] if i < len(col_widths) else len(col.name)
                if col.align == "right":
                    header_parts.append(Colors.header(col.name.rjust(w)))
                else:
                    header_parts.append(Colors.header(col.name.ljust(w)))
            print("  " + "  ".join(header_parts), end="", flush=True)

            # Separator
            self._move_cursor(layout["column_headers"] + 1, 0)
            sep_parts = ["───"]  # Action column
            for w in col_widths:
                sep_parts.append("─" * w)
            print(f"  {Colors.PROTECTED}{'──'.join(sep_parts)}{Colors.RESET}", end="", flush=True)

            # Data rows (full render includes row data)
            end_row = min(self.current_row + page_size, len(self.rows))
            visible_rows = self.rows[self.current_row:end_row]

            for i, row in enumerate(visible_rows):
                abs_idx = self.current_row + i
                self._move_cursor(layout["data_start"] + i, 0)

                # Action input field (green, underscore if empty)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                action_display = action_val.ljust(1) if action_val else "_"
                print(f"  {Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

                # Data columns
                for j, col in enumerate(self._columns):
                    w = col_widths[j] if j < len(col_widths) else 10
                    val_str = str(row.get(col.name, ""))
                    if col.align == "right":
                        val = val_str.rjust(w)
                    else:
                        val = val_str.ljust(w)
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
            # Partial update: refresh header fields and action input fields
            if self.header_fields:
                for i, field in enumerate(self.header_fields):
                    # Calculate position after label
                    label_len = len(field.label) + 7  # " . . . "
                    self._move_cursor(layout["header_fields_start"] + i, 2 + label_len)
                    val = field.value
                    remaining = field.length - len(val)
                    print(f"{Colors.INPUT}{val}", end="", flush=True)
                    if remaining > 0:
                        print(f"{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)

            end_row = min(self.current_row + page_size, len(self.rows))
            for i in range(end_row - self.current_row):
                abs_idx = self.current_row + i
                self._move_cursor(layout["data_start"] + i, 2)
                action_val = self.action_inputs[abs_idx] if abs_idx < len(self.action_inputs) else ""
                action_display = action_val.ljust(1) if action_val else "_"
                print(f"{Colors.DEFAULT}{action_display}{Colors.RESET}", end="", flush=True)

        # Position cursor
        if in_header and self.header_fields:
            field = self.header_fields[header_field_idx]
            label_len = len(field.label) + 7
            self._move_cursor(layout["header_fields_start"] + header_field_idx,
                            2 + label_len + header_cursor_pos)
        elif 0 <= cursor_row < page_size and cursor_row + self.current_row < len(self.rows):
            self._move_cursor(layout["data_start"] + cursor_row, 2 + cursor_col)

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
                elif seq2 == 'Z':
                    return 'BACKTAB'
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
                elif seq2 == '3':
                    sys.stdin.read(1)  # ~
                    return 'DELETE'
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
            empty list if Enter pressed with no actions (check get_header_values()),
            or None if user exits with F3.
        """
        height, width = self._get_terminal_size()
        page_size = self._get_page_size(height)

        # Cursor state
        in_header = len(self.header_fields) > 0  # Start in header if fields exist
        header_field_idx = 0
        header_cursor_pos = 0
        cursor_row = 0  # Row within current page (for list area)
        cursor_col = 0  # Column within action field (always 0 for single char)
        need_full_redraw = True

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                self._render(page_size, height, width, cursor_row, cursor_col,
                            in_header, header_field_idx, header_cursor_pos,
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
                    self.add_callback()
                    return []

                elif key == 'F7':
                    if self.current_row > 0:
                        self.current_row = max(0, self.current_row - page_size)
                        cursor_row = 0
                        in_header = False
                        need_full_redraw = True

                elif key == 'F8':
                    if self.current_row + page_size < len(self.rows):
                        self.current_row = min(len(self.rows) - 1, self.current_row + page_size)
                        cursor_row = 0
                        in_header = False
                        need_full_redraw = True

                elif key == '\t':
                    if in_header:
                        if header_field_idx < len(self.header_fields) - 1:
                            header_field_idx += 1
                            header_cursor_pos = 0
                        else:
                            # Move to list area
                            in_header = False
                            cursor_row = 0
                    else:
                        # Move to next row in list
                        abs_row = self.current_row + cursor_row
                        if abs_row < len(self.rows) - 1:
                            if cursor_row < page_size - 1:
                                cursor_row += 1
                            elif self.current_row + page_size < len(self.rows):
                                self.current_row += 1
                                need_full_redraw = True

                elif key == 'BACKTAB':
                    if in_header:
                        if header_field_idx > 0:
                            header_field_idx -= 1
                            header_cursor_pos = len(self.header_fields[header_field_idx].value)
                    else:
                        if cursor_row > 0:
                            cursor_row -= 1
                        elif self.header_fields:
                            in_header = True
                            header_field_idx = len(self.header_fields) - 1
                            header_cursor_pos = len(self.header_fields[header_field_idx].value)

                elif key == 'UP':
                    if in_header:
                        if header_field_idx > 0:
                            header_field_idx -= 1
                            header_cursor_pos = min(header_cursor_pos,
                                                   len(self.header_fields[header_field_idx].value))
                    else:
                        if cursor_row > 0:
                            cursor_row -= 1
                        elif self.current_row > 0:
                            self.current_row -= 1
                            need_full_redraw = True
                        elif self.header_fields:
                            in_header = True
                            header_field_idx = len(self.header_fields) - 1
                            header_cursor_pos = 0

                elif key == 'DOWN':
                    if in_header:
                        if header_field_idx < len(self.header_fields) - 1:
                            header_field_idx += 1
                            header_cursor_pos = min(header_cursor_pos,
                                                   len(self.header_fields[header_field_idx].value))
                        elif self.rows:
                            in_header = False
                            cursor_row = 0
                    else:
                        abs_row = self.current_row + cursor_row
                        if cursor_row < page_size - 1 and abs_row < len(self.rows) - 1:
                            cursor_row += 1
                        elif self.current_row + page_size < len(self.rows):
                            self.current_row += 1
                            need_full_redraw = True

                elif key == 'LEFT':
                    if in_header:
                        if header_cursor_pos > 0:
                            header_cursor_pos -= 1

                elif key == 'RIGHT':
                    if in_header:
                        field = self.header_fields[header_field_idx]
                        if header_cursor_pos < len(field.value):
                            header_cursor_pos += 1

                elif key == 'HOME':
                    if in_header:
                        header_cursor_pos = 0

                elif key == 'END':
                    if in_header:
                        header_cursor_pos = len(self.header_fields[header_field_idx].value)

                elif key in ('\r', '\n'):
                    # Check for actions
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
                    # No actions - return empty (caller can check header values)
                    self._clear()
                    return []

                elif key == '\x7f' or key == '\x08':  # Backspace
                    if in_header:
                        field = self.header_fields[header_field_idx]
                        if header_cursor_pos > 0:
                            field.value = field.value[:header_cursor_pos - 1] + field.value[header_cursor_pos:]
                            header_cursor_pos -= 1
                    else:
                        abs_row = self.current_row + cursor_row
                        if abs_row < len(self.action_inputs):
                            self.action_inputs[abs_row] = ""

                elif key == 'DELETE':
                    if in_header:
                        field = self.header_fields[header_field_idx]
                        if header_cursor_pos < len(field.value):
                            field.value = field.value[:header_cursor_pos] + field.value[header_cursor_pos + 1:]

                elif len(key) == 1 and key.isprintable():
                    if in_header:
                        field = self.header_fields[header_field_idx]
                        if field.field_type == FieldType.NUMERIC:
                            if not (key.isdigit() or key in '.-'):
                                continue
                        if len(field.value) < field.length:
                            field.value = field.value[:header_cursor_pos] + key + field.value[header_cursor_pos:]
                            header_cursor_pos += 1
                    else:
                        abs_row = self.current_row + cursor_row
                        if abs_row < len(self.action_inputs):
                            self.action_inputs[abs_row] = key.upper()
                            # Auto-advance
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
