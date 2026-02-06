"""Form UI component for IBM 3270-style applications."""

import copy
from typing import Dict, Any, Optional, Callable, List, NamedTuple

from ux3270.panel import Screen, Field, FieldType, Colors


class _FieldLabel(NamedTuple):
    row: int
    label: str


class _StaticText(NamedTuple):
    row: int
    col: int
    text: str


class _FormItem(NamedTuple):
    kind: str  # "field" or "text"
    index: int


class Form:
    """
    High-level form builder with IBM 3270-style layout.

    Follows IBM CUA conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Labels in protected (turquoise) color
    - Input fields with underscores showing field length
    - Function key hints at bottom
    - F1 displays context-sensitive help

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

    # CUA layout: fields start after title (row 0) and instruction (row 1)
    BODY_START_ROW = 3

    def __init__(self, title: str = "", panel_id: str = "",
                 instruction: str = "", help_text: str = ""):
        """
        Initialize a form.

        Args:
            title: Form title (displayed in uppercase per IBM convention)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Optional instruction text (shown on row 2 per CUA)
            help_text: Panel-level help text shown when F1 is pressed
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.help_text = help_text
        self._fields: List[Field] = []
        self._field_help: Dict[str, str] = {}  # label -> help_text
        self._static_text: List[_StaticText] = []
        self._field_label_rows: List[_FieldLabel] = []
        self._items: List[_FormItem] = []
        self.current_row = self.BODY_START_ROW
        self.label_col = 2
        self.field_col = 20

    # Minimum gap between the longest label and the field column,
    # ensuring at least one visible dot in the leader.
    MIN_LABEL_FIELD_GAP = 4

    # Minimum visible field width; field_col is clamped so that at
    # least this many columns remain for input on the screen.
    MIN_FIELD_WIDTH = 10

    def add_field(
        self,
        label: str,
        length: int = 20,
        field_type: FieldType = FieldType.TEXT,
        default: str = "",
        required: bool = False,
        validator: Optional[Callable[[str], bool]] = None,
        prompt: Optional[Callable[[], Optional[str]]] = None,
        help_text: str = ""
    ) -> "Form":
        """
        Add a field to the form.

        Args:
            label: Field label
            length: Field length
            field_type: Field type
            default: Default value
            required: Whether field is required
            validator: Optional validation function
            prompt: Optional F4=Prompt callback; should return selected value
                   as string, or None if cancelled
            help_text: Help text shown when F1 is pressed on this field

        Returns:
            Self for method chaining
        """
        # Store label info for dynamic layout at render time
        self._field_label_rows.append(_FieldLabel(self.current_row, label))

        field = Field(
            row=self.current_row,
            col=0,  # will be computed in _build_screen
            length=length,
            field_type=field_type,
            label=label,
            default=default,
            required=required,
            validator=validator,
            prompt=prompt
        )
        self._fields.append(field)
        self._items.append(_FormItem("field", len(self._fields) - 1))
        if help_text:
            self._field_help[label] = help_text
        self.current_row += 2  # Add spacing between fields
        return self

    def add_text(self, text: str) -> "Form":
        """
        Add static text to the form.

        Args:
            text: Text to display

        Returns:
            Self for method chaining
        """
        self._static_text.append(_StaticText(self.current_row, self.label_col, text))
        self._items.append(_FormItem("text", len(self._static_text) - 1))
        self.current_row += 2
        return self

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

        # Title row
        if self.panel_id:
            screen.add_text(0, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(0, title_col, self.title, Colors.INTENSIFIED)

        # Instruction row
        if self.instruction:
            screen.add_text(1, 0, self.instruction, Colors.PROTECTED)

        # Compute field_col from ALL field labels (consistent across pages),
        # clamped so fields retain at least MIN_FIELD_WIDTH visible columns.
        if self._field_label_rows:
            max_label_len = max(len(label) for _, label in self._field_label_rows)
            field_col = max(self.field_col, self.label_col + max_label_len + self.MIN_LABEL_FIELD_GAP)
            field_col = min(field_col, width - self.MIN_FIELD_WIDTH)
        else:
            field_col = self.field_col

        # Slice items for the current page
        start = page * page_size
        end = min(start + page_size, len(self._items))
        visible_items = self._items[start:end]

        # Render visible items, remapping rows starting at BODY_START_ROW
        screen_row = self.BODY_START_ROW
        for item_type, idx in visible_items:
            if item_type == "field":
                field = self._fields[idx]
                _, label = self._field_label_rows[idx]
                # Render label with dot leader
                gap_start = self.label_col + len(label)
                leader = "".join(
                    "." if c != gap_start and c != field_col - 1
                    and c % 2 == field_col % 2
                    else " "
                    for c in range(gap_start, field_col)
                )
                screen.add_text(screen_row, self.label_col, label + leader, Colors.PROTECTED)
                # Copy the field so we don't mutate the Form's canonical list
                screen_field = copy.copy(field)
                screen_field.row = screen_row
                screen_field.col = field_col
                screen.add_field(screen_field)
            else:
                _, col, text = self._static_text[idx]
                screen.add_text(screen_row, col, text, Colors.PROTECTED)
            screen_row += 2

        # Footer separator
        screen.add_text(height - 2, 0, "-" * width, Colors.DIM)

        # Function keys
        fkeys_list = []
        if self.help_text or self._field_help:
            fkeys_list.append("F1=Help")
        fkeys_list.append("F3=Exit")
        # Show F4=Prompt if any field has a prompt callback
        if any(f.prompt for f in self._fields):
            fkeys_list.append("F4=Prompt")
        # Pagination keys
        if len(self._items) > page_size:
            if page > 0:
                fkeys_list.append("F7=Up")
            if end < len(self._items):
                fkeys_list.append("F8=Down")
        screen.add_text(height - 1, 0, "  ".join(fkeys_list), Colors.PROTECTED)

        return screen

    def _show_help(self, current_field_label: str, height: int, width: int):
        """Display help screen."""
        help_screen = Screen()

        # Title
        help_title = "HELP"
        title_col = max(0, (width - len(help_title)) // 2)
        help_screen.add_text(0, title_col, help_title, Colors.INTENSIFIED)

        row = 2

        # Panel-level help
        if self.help_text:
            help_screen.add_text(row, 2, self.help_text, Colors.PROTECTED)
            row += 2

        # Field-specific help
        field_help = self._field_help.get(current_field_label, "")
        if field_help:
            help_screen.add_text(row, 2, f"Field: {current_field_label}", Colors.INTENSIFIED)
            row += 1
            help_screen.add_text(row, 2, field_help, Colors.PROTECTED)
            row += 2

        # List all field help if no specific field help
        if not field_help and self._field_help:
            help_screen.add_text(row, 2, "Field Help:", Colors.INTENSIFIED)
            row += 1
            for label, text in self._field_help.items():
                help_screen.add_text(row, 4, f"{label}: {text}", Colors.PROTECTED)
                row += 1

        # Footer
        help_screen.add_text(height - 2, 0, "-" * width, Colors.DIM)
        help_screen.add_text(height - 1, 0, "Press Enter or F3 to return", Colors.PROTECTED)

        help_screen.show()

    _FOOTER_LINES = 2  # separator + fkeys

    def _page_size(self, height: int) -> int:
        """Compute how many items fit on one page (each item is 2 rows)."""
        return max(1, (height - self.BODY_START_ROW - self._FOOTER_LINES) // 2)

    def _restore_field_values(self, fields: Dict[str, Any]):
        """Restore field values from a result dict."""
        for field in self._fields:
            if field.label in fields:
                field.value = fields[field.label]

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Display the form and return field values.

        Returns:
            Dictionary of field values, or None if cancelled (F3)
        """
        height, width = self._get_terminal_size()
        page_size = self._page_size(height)
        page = 0

        while True:
            screen = self._build_screen(page, page_size, height, width)
            result = screen.show()

            if result is None:
                return None

            if result["aid"] == "F3":
                return None

            # Restore field values from the visible page before any action.
            # This MUST run before every page transition so edits on the
            # current page are preserved when the user navigates away.
            self._restore_field_values(result["fields"])

            if result["aid"] == "F1":
                current_field = result.get("current_field", "")
                self._show_help(current_field, height, width)
                continue

            if result["aid"] == "F4":
                current_field_label = result.get("current_field", "")
                for field in self._fields:
                    if field.label == current_field_label and field.prompt:
                        prompt_result = field.prompt()
                        if prompt_result is not None:
                            field.value = str(prompt_result)
                        break
                continue

            if result["aid"] in ("F7", "PGUP"):
                if page > 0:
                    page -= 1
                continue

            if result["aid"] in ("F8", "PGDN"):
                if (page + 1) * page_size < len(self._items):
                    page += 1
                continue

            # Enter: return values from ALL fields (not just visible page)
            return {field.label: field.value for field in self._fields}
