"""Work-with list component for IBM 3270-style applications."""

from typing import List, Dict, Any, Optional, Callable, Literal

from ux3270.panel import Screen, Colors, Field, FieldType


class ListColumn:
    """Represents a column definition in a work-with list."""

    def __init__(self, name: str, width: Optional[int] = None,
                 align: Literal["left", "right"] = "left"):
        self.name = name
        self.width = width
        self.align = align


class WorkWithList:
    """
    IBM 3270-style work-with list with action codes.

    Displays a list of records with an Opt input field per row.
    Users type action codes (2=Change, 4=Delete, etc.) and press Enter
    to process actions.

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

    # Opt field width (2 chars, standard for AS/400)
    OPT_FIELD_LENGTH = 2

    def __init__(self, title: str = "", panel_id: str = "", instruction: str = ""):
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction or "Type option, press Enter."
        self._columns: List[ListColumn] = []
        self.rows: List[Dict[str, Any]] = []
        self.actions: Dict[str, str] = {}  # code -> description
        self.add_callback: Optional[Callable] = None
        self.current_page = 0  # Current page for pagination
        self.current_row = 0  # Starting row position (used to calculate initial page)
        self._header_fields: List[Dict[str, Any]] = []  # Header field definitions

    def add_column(self, name: str, width: Optional[int] = None,
                   align: Literal["left", "right"] = "left") -> "WorkWithList":
        self._columns.append(ListColumn(name, width, align))
        return self

    def add_action(self, code: str, description: str) -> "WorkWithList":
        self.actions[code] = description
        return self

    def add_header_field(self, label: str, length: int = 10, default: str = "",
                         field_type: FieldType = FieldType.TEXT) -> "WorkWithList":
        self._header_fields.append({
            "label": label,
            "length": length,
            "default": default,
            "field_type": field_type,
            "value": default
        })
        return self

    def get_header_values(self) -> Dict[str, str]:
        return {f["label"]: f["value"] for f in self._header_fields}

    def set_add_callback(self, callback: Callable) -> "WorkWithList":
        self.add_callback = callback
        return self

    def add_row(self, **values) -> "WorkWithList":
        self.rows.append(values)
        return self

    def _calculate_widths(self) -> List[int]:
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
        actions_row = 3 + header_rows + (1 if header_rows else 0)
        column_headers_row = actions_row + 2
        data_start_row = column_headers_row + 2

        # Title
        if self.panel_id:
            screen.add_text(title_row, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(title_row, title_col, self.title, Colors.INTENSIFIED)

        # Instruction
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

        # Action codes legend
        if self.actions:
            legend_parts = [f"{code}={desc}" for code, desc in self.actions.items()]
            screen.add_text(actions_row, 2, "  ".join(legend_parts), Colors.PROTECTED)

        # Column headers
        header_text = "Opt"
        col_pos = 2 + 3 + 2  # After "Opt" + spacing
        for i, col in enumerate(self._columns):
            w = col_widths[i] if i < len(col_widths) else len(col.name)
            if col.align == "right":
                header_text += "  " + col.name.rjust(w)
            else:
                header_text += "  " + col.name.ljust(w)
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
                val = str(data_row.get(col.name, ""))
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
        fkeys = ["F3=Exit"]
        if self.add_callback:
            fkeys.append("F6=Add")
        if len(self.rows) > page_size:
            if page > 0:
                fkeys.append("F7=Up")
            if end_row_idx < len(self.rows):
                fkeys.append("F8=Down")
        screen.add_text(height - 1, 0, "  ".join(fkeys), Colors.PROTECTED)

        return screen

    def show(self) -> Optional[List[Dict[str, Any]]]:
        """
        Display the work-with list and handle user input.

        Returns:
            List of actions: [{"action": "2", "row": {...}}, ...]
            Empty list if no actions selected.
            None if cancelled (F3).
        """
        if not self.rows:
            return []

        height, width = self._get_terminal_size()
        # Calculate page size based on available space
        header_rows = len(self._header_fields)
        chrome_lines = 3 + header_rows + (1 if header_rows else 0) + 4 + 3  # title, instr, headers, actions, footer
        page_size = max(1, height - chrome_lines)

        # Calculate initial page from current_row position
        page = self.current_row // page_size if page_size > 0 else 0

        while True:
            screen = self._build_screen(page, page_size, height, width)
            result = screen.show()

            if result is None:
                return None

            aid = result["aid"]
            fields = result["fields"]

            # Update header field values
            for hf in self._header_fields:
                if hf["label"] in fields:
                    hf["value"] = fields[hf["label"]]

            if aid == "F3":
                return None

            elif aid == "F6" and self.add_callback:
                self.add_callback()
                return []  # Signal refresh

            elif aid == "F7" or aid == "PGUP":
                if page > 0:
                    page -= 1

            elif aid == "F8" or aid == "PGDN":
                start_idx = page * page_size
                if start_idx + page_size < len(self.rows):
                    page += 1

            elif aid == "ENTER":
                # Check for actions in Opt fields
                results = []
                for key, value in fields.items():
                    if key.startswith("opt_") and value:
                        row_idx = int(key.split("_")[1])
                        if value.upper() in self.actions and row_idx < len(self.rows):
                            results.append({
                                "action": value.upper(),
                                "row": self.rows[row_idx]
                            })
                if results:
                    return results
                # No actions - return empty (caller can check header values)
                return []

        return []

    # Backwards compatibility
    @property
    def header_fields(self) -> List[Dict[str, Any]]:
        return self._header_fields
