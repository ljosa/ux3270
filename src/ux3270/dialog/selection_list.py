"""Selection list component for IBM 3270-style applications."""

from typing import List, Optional, Dict, Any, Callable, Literal

from ux3270.panel import Screen, Field, FieldType, Colors
from ux3270.dialog.layout import shrink_widths_to_fit


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

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

    # Opt field width (2 chars, standard for AS/400)
    OPT_FIELD_LENGTH = 2

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
        self.add_callback: Optional[Callable] = None
        self.current_page = 0

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
        return self

    def _calculate_widths(self, available_width: int) -> List[int]:
        """Calculate column widths based on content, fitting within available width."""
        if not self._columns:
            return []

        # Calculate natural widths
        widths = []
        for col in self._columns:
            if col.width is not None:
                widths.append(col.width)
            else:
                widths.append(len(col.name))

        for row in self.rows:
            for i, col in enumerate(self._columns):
                if col.name in row and col.width is None:
                    val_len = len(str(row[col.name]))
                    if i < len(widths):
                        widths[i] = max(widths[i], val_len)

        # Fixed width = indent(2) + Opt(3) + gaps(2 per col)
        num_cols = len(widths)
        fixed_width = 2 + 3 + (2 * num_cols)

        min_widths = [min(len(col.name), 5) for col in self._columns]

        return shrink_widths_to_fit(widths, min_widths, fixed_width, available_width)

    def _truncate(self, text: str, max_width: int) -> str:
        """Truncate text to fit width, adding '>' indicator if truncated."""
        if len(text) <= max_width:
            return text
        if max_width <= 1:
            return text[:max_width]
        return text[:max_width - 1] + ">"

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80

    def _build_screen(self, page: int, page_size: int, height: int, width: int) -> Screen:
        """Build a Screen with all text and fields for the current page."""
        screen = Screen()
        col_widths = self._calculate_widths(width)

        # Layout constants
        title_row = 0
        instruction_row = 1
        column_headers_row = 3
        data_start_row = 5

        # Title
        if self.panel_id:
            screen.add_text(title_row, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(title_row, title_col, self.title, Colors.INTENSIFIED)

        # Instruction
        screen.add_text(instruction_row, 0, self.instruction, Colors.PROTECTED)

        # Column headers
        header_text = "Opt"
        for i, col in enumerate(self._columns):
            w = col_widths[i] if i < len(col_widths) else len(col.name)
            name = self._truncate(col.name, w)
            if col.align == "right":
                header_text += "  " + name.rjust(w)
            else:
                header_text += "  " + name.ljust(w)
        screen.add_text(column_headers_row, 2, header_text, Colors.INTENSIFIED)

        # Separator (dashes under each column)
        sep = "---"  # Opt column
        for w in col_widths:
            sep += "  " + "-" * w
        screen.add_text(column_headers_row + 1, 2, sep, Colors.PROTECTED)

        # Data rows with Opt fields
        start_row_idx = page * page_size
        end_row_idx = min(start_row_idx + page_size, len(self.rows))
        visible_rows = self.rows[start_row_idx:end_row_idx]

        for i, data_row in enumerate(visible_rows):
            screen_row = data_start_row + i

            # Opt input field
            opt_field = Field(row=screen_row, col=2, length=self.OPT_FIELD_LENGTH,
                             label=f"opt_{start_row_idx + i}")
            screen.add_field(opt_field)

            # Data columns (as text)
            col_pos = 2 + 3 + 2  # After Opt field + spacing
            for j, col in enumerate(self._columns):
                w = col_widths[j] if j < len(col_widths) else 10
                val = self._truncate(str(data_row.get(col.name, "")), w)
                if col.align == "right":
                    display_val = val.rjust(w)
                else:
                    display_val = val.ljust(w)
                screen.add_text(screen_row, col_pos, display_val, Colors.DEFAULT)
                col_pos += w + 2

        # Row count message
        if self.rows:
            if len(self.rows) > page_size:
                count_msg = f"ROW {start_row_idx + 1} TO {end_row_idx} OF {len(self.rows)}"
            else:
                count_msg = f"ROWS {len(self.rows)}"
            screen.add_text(height - 3, width - len(count_msg) - 1, count_msg, Colors.PROTECTED)

        # Separator
        screen.add_text(height - 2, 0, "-" * width, Colors.DIM)

        # Function keys
        fkeys = ["F3=Cancel"]
        if self.add_callback:
            fkeys.append("F6=Add")
        if len(self.rows) > page_size:
            if page > 0:
                fkeys.append("F7=Up")
            if end_row_idx < len(self.rows):
                fkeys.append("F8=Down")
        screen.add_text(height - 1, 0, "  ".join(fkeys), Colors.PROTECTED)

        return screen

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Display the selection list and wait for user selection.

        Returns:
            Selected row as dictionary, or None if cancelled
        """
        if not self.rows:
            return None

        height, width = self._get_terminal_size()
        # Calculate page size based on available space
        chrome_lines = 5 + 3  # header rows + footer
        page_size = max(1, height - chrome_lines)

        page = 0

        while True:
            screen = self._build_screen(page, page_size, height, width)
            result = screen.show()

            if result is None:
                return None

            aid = result["aid"]
            fields = result["fields"]

            if aid == "F3":
                return None

            elif aid == "F6" and self.add_callback:
                new_item = self.add_callback()
                if new_item:
                    return new_item
                return None

            elif aid == "F7" or aid == "PGUP":
                if page > 0:
                    page -= 1

            elif aid == "F8" or aid == "PGDN":
                start_idx = page * page_size
                if start_idx + page_size < len(self.rows):
                    page += 1

            elif aid == "ENTER":
                # Check for 'S' selection in Opt fields
                for key, value in fields.items():
                    if key.startswith("opt_") and value.upper() == "S":
                        row_idx = int(key.split("_")[1])
                        if row_idx < len(self.rows):
                            return self.rows[row_idx]
                # No selection made, continue
