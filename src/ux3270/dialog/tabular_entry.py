"""Tabular entry component for IBM 3270-style applications."""

from typing import List, Dict, Any, Optional, Callable

from ux3270.panel import Screen, Field, FieldType, Colors


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

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

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

    def _get_col_position(self, col_idx: int) -> int:
        """Get the starting column position for a column index."""
        pos = 2  # Initial indent
        for i, col in enumerate(self.columns):
            if i == col_idx:
                return pos
            pos += col.width + 2  # width + 2 spaces
        return pos

    def _truncate(self, text: str, max_width: int) -> str:
        """Truncate text to fit width, adding '>' indicator if truncated."""
        if len(text) <= max_width:
            return text
        if max_width <= 1:
            return text[:max_width]
        return text[:max_width - 1] + ">"

    def _build_screen(self, page: int, page_size: int, height: int, width: int) -> Screen:
        """Build a Screen with all text and fields for the current page."""
        screen = Screen()

        # Layout constants
        title_row = 0
        instruction_row = 1
        header_row = 3
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
        header_parts = []
        for col in self.columns:
            if col.editable and col.required:
                header_parts.append(self._truncate(f"*{col.name}", col.width).ljust(col.width))
            else:
                header_parts.append(self._truncate(col.name, col.width).ljust(col.width))
        header_text = "  ".join(header_parts)
        screen.add_text(header_row, 2, header_text, Colors.INTENSIFIED)

        # Separator (dashes under each column)
        sep_parts = ["-" * col.width for col in self.columns]
        sep_text = "  ".join(sep_parts)
        screen.add_text(header_row + 1, 2, sep_text, Colors.PROTECTED)

        # Data rows
        start_row_idx = page * page_size
        end_row_idx = min(start_row_idx + page_size, len(self.rows))

        for display_idx, row_idx in enumerate(range(start_row_idx, end_row_idx)):
            row = self.rows[row_idx]
            screen_row = data_start_row + display_idx

            col_pos = 2
            for col_idx, col in enumerate(self.columns):
                if col.editable:
                    # Add Field for editable cell
                    current_val = self.values[row_idx].get(col.name, "")
                    field = Field(
                        row=screen_row,
                        col=col_pos,
                        length=col.width,
                        field_type=col.field_type,
                        label=f"{col.name}_{row_idx}",
                        default=current_val,
                        required=col.required,
                        validator=col.validator
                    )
                    screen.add_field(field)
                else:
                    # Static text
                    val = self._truncate(str(row.get(col.name, "")), col.width).ljust(col.width)
                    screen.add_text(screen_row, col_pos, val, Colors.PROTECTED)

                col_pos += col.width + 2  # width + 2 spaces

        # Error line
        if self.error_message:
            screen.add_text(height - 4, 0, self.error_message, Colors.ERROR)

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
        fkeys = ["F3=Cancel", "Enter=Submit"]
        if len(self.rows) > page_size:
            if page > 0:
                fkeys.append("F7=Up")
            if end_row_idx < len(self.rows):
                fkeys.append("F8=Down")
        screen.add_text(height - 1, 0, "  ".join(fkeys), Colors.PROTECTED)

        return screen

    def _validate_all(self) -> Optional[str]:
        """
        Validate all editable fields.

        Returns:
            Error message for first validation failure, or None if all valid.
        """
        for row_idx, row_values in enumerate(self.values):
            for col in self.columns:
                if not col.editable:
                    continue

                val = row_values.get(col.name, "")

                # Required check
                if col.required and not val.strip():
                    return f"Row {row_idx + 1}: {col.name} is required"

                # Numeric check
                if col.field_type == FieldType.NUMERIC and val.strip():
                    if not val.replace('.', '').replace('-', '').isdigit():
                        return f"Row {row_idx + 1}: {col.name} must be numeric"

                # Custom validator
                if col.validator and val.strip():
                    if not col.validator(val):
                        return f"Row {row_idx + 1}: {col.name} is invalid"

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
        # Calculate page size
        header_lines = 5  # Title + instruction + blank + headers + separator
        footer_lines = 4  # Error + message + separator + function keys
        page_size = max(1, height - header_lines - footer_lines)

        page = self.current_row // page_size if page_size > 0 else 0

        while True:
            screen = self._build_screen(page, page_size, height, width)
            result = screen.show()

            if result is None:
                return None

            aid = result["aid"]
            fields = result["fields"]

            # Update values from fields
            for key, value in fields.items():
                # Field labels are "colname_rowidx"
                if "_" in key:
                    parts = key.rsplit("_", 1)
                    if len(parts) == 2:
                        col_name, row_idx_str = parts
                        try:
                            row_idx = int(row_idx_str)
                            if row_idx < len(self.values) and col_name in self.values[row_idx]:
                                self.values[row_idx][col_name] = value
                        except ValueError:
                            pass

            if aid == "F3":
                return None

            elif aid == "ENTER":
                # Validate and submit
                self.error_message = self._validate_all() or ""
                if not self.error_message:
                    return [dict(self.rows[i], **self.values[i]) for i in range(len(self.rows))]
                # Error - continue to redisplay with error message

            elif aid == "F7" or aid == "PGUP":
                if page > 0:
                    page -= 1
                    self.error_message = ""

            elif aid == "F8" or aid == "PGDN":
                start_idx = page * page_size
                if start_idx + page_size < len(self.rows):
                    page += 1
                    self.error_message = ""
