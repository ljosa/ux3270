"""Table display component for IBM 3270-style applications."""

from typing import List, Optional, Literal, Dict, Any

from ux3270.panel import Screen, Field, FieldType, Colors


class TableColumn:
    """Represents a column definition in a table."""

    def __init__(self, name: str, width: Optional[int] = None,
                 align: Literal["left", "right"] = "left"):
        """
        Initialize a column.

        Args:
            name: Column name (used as header)
            width: Display width (None = auto-calculate from content)
            align: Text alignment ("left" or "right")
        """
        self.name = name
        self.width = width
        self.align = align


class Table:
    """
    IBM 3270-style table/list display with pagination.

    Displays tabular data with column headers following CUA conventions:
    - Panel ID at top-left, title centered
    - Optional header fields (e.g., "Position to" filter)
    - Column headers in intensified text
    - Data rows in default (green) color
    - Row count/pagination info on message line
    - F7/F8 for page up/down (CUA standard)
    - Function keys at bottom

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

    def __init__(self, title: str = "", panel_id: str = "", instruction: str = ""):
        """
        Initialize a table.

        Args:
            title: Table title (displayed in uppercase per IBM convention)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Optional instruction text
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self._columns: List[TableColumn] = []
        self.rows: List[List[str]] = []
        self._header_fields: List[Dict[str, Any]] = []
        self.current_row = 0  # First visible row index

    def add_column(self, name: str, width: Optional[int] = None,
                   align: Literal["left", "right"] = "left") -> "Table":
        """
        Add a column definition.

        Args:
            name: Column name (used as header)
            width: Display width (None = auto-calculate from content)
            align: Text alignment ("left" or "right")

        Returns:
            Self for method chaining
        """
        self._columns.append(TableColumn(name, width, align))
        return self

    def add_header_field(self, label: str, length: int = 10, default: str = "",
                         field_type: FieldType = FieldType.TEXT) -> "Table":
        """
        Add a header field (e.g., "Position to" filter).

        Args:
            label: Field label
            length: Field length
            default: Default value
            field_type: Field type

        Returns:
            Self for method chaining
        """
        self._header_fields.append({
            "label": label,
            "length": length,
            "default": default,
            "field_type": field_type,
            "value": default
        })
        return self

    def get_header_values(self) -> Dict[str, str]:
        """Get current header field values."""
        return {f["label"]: f["value"] for f in self._header_fields}

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
            for i, val in enumerate(row):
                if i < len(widths) and self._columns[i].width is None:
                    widths[i] = max(widths[i], len(str(val)))

        return widths

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
        col_widths = self._calculate_widths()

        # Calculate layout
        header_rows = len(self._header_fields)
        title_row = 0
        instruction_row = 1
        header_fields_start = 3
        column_headers_row = 3 + header_rows + (1 if header_rows else 0)
        data_start_row = column_headers_row + 2

        # Title
        if self.panel_id:
            screen.add_text(title_row, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(title_row, title_col, self.title, Colors.INTENSIFIED)

        # Instruction
        if self.instruction:
            screen.add_text(instruction_row, 0, self.instruction, Colors.PROTECTED)

        # Header fields
        for i, hf in enumerate(self._header_fields):
            row = header_fields_start + i
            label_text = f"{hf['label']} . . ."
            screen.add_text(row, 2, label_text, Colors.PROTECTED)
            col = 2 + len(label_text) + 1
            field = Field(row=row, col=col, length=hf["length"],
                         field_type=hf["field_type"], label=hf["label"],
                         default=hf["value"])
            screen.add_field(field)

        # Column headers
        if self._columns:
            header_parts = []
            for i, col in enumerate(self._columns):
                w = col_widths[i] if i < len(col_widths) else len(col.name)
                if col.align == "right":
                    header_parts.append(col.name.rjust(w))
                else:
                    header_parts.append(col.name.ljust(w))
            header_text = " │ ".join(header_parts)
            screen.add_text(column_headers_row, 2, header_text, Colors.INTENSIFIED)

            # Separator line
            sep_parts = ["─" * w for w in col_widths]
            sep_text = "─┼─".join(sep_parts)
            screen.add_text(column_headers_row + 1, 2, sep_text, Colors.PROTECTED)

        # Data rows
        start_row_idx = page * page_size
        end_row_idx = min(start_row_idx + page_size, len(self.rows))
        visible_rows = self.rows[start_row_idx:end_row_idx]

        for i, data_row in enumerate(visible_rows):
            screen_row = data_start_row + i
            row_parts = []
            for j, val in enumerate(data_row):
                w = col_widths[j] if j < len(col_widths) else len(str(val))
                col = self._columns[j] if j < len(self._columns) else None
                if col and col.align == "right":
                    row_parts.append(str(val).rjust(w))
                else:
                    row_parts.append(str(val).ljust(w))
            row_text = " │ ".join(row_parts)
            screen.add_text(screen_row, 2, row_text, Colors.DEFAULT)

        # Row count message
        if self.rows:
            if len(self.rows) > page_size:
                count_msg = f"ROW {start_row_idx + 1} TO {end_row_idx} OF {len(self.rows)}"
            else:
                count_msg = f"ROWS {len(self.rows)}"
            screen.add_text(height - 3, width - len(count_msg) - 1, count_msg, Colors.PROTECTED)

        # Separator
        screen.add_text(height - 2, 0, "─" * width, Colors.DIM)

        # Function keys
        fkeys = ["F3=Return"]
        if len(self.rows) > page_size:
            if page > 0:
                fkeys.append("F7=Up")
            if end_row_idx < len(self.rows):
                fkeys.append("F8=Down")
        screen.add_text(height - 1, 0, "  ".join(fkeys), Colors.PROTECTED)

        return screen

    def show(self) -> Optional[Dict[str, str]]:
        """
        Display the table with pagination and wait for user input.

        Returns:
            Dictionary of header field values, or None if no header fields.
        """
        height, width = self._get_terminal_size()

        # Calculate page size based on available space
        header_rows = len(self._header_fields)
        chrome_lines = 3 + header_rows + (1 if header_rows else 0) + 4 + 3
        page_size = max(1, height - chrome_lines)

        # Calculate initial page from current_row
        page = self.current_row // page_size if page_size > 0 else 0

        while True:
            screen = self._build_screen(page, page_size, height, width)
            result = screen.show()

            if result is None:
                return self.get_header_values() if self._header_fields else None

            aid = result["aid"]
            fields = result["fields"]

            # Update header field values
            for hf in self._header_fields:
                if hf["label"] in fields:
                    hf["value"] = fields[hf["label"]]

            if aid == "F3" or aid == "ENTER":
                return self.get_header_values() if self._header_fields else None

            elif aid == "F7" or aid == "PGUP":
                if page > 0:
                    page -= 1

            elif aid == "F8" or aid == "PGDN":
                start_idx = page * page_size
                if start_idx + page_size < len(self.rows):
                    page += 1
