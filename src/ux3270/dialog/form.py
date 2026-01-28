"""Form UI component for IBM 3270-style applications."""

from typing import Dict, Any, Optional, Callable

from ux3270.panel import Screen, Field, FieldType


class Form:
    """
    High-level form builder with IBM 3270-style layout.

    Follows IBM CUA conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Labels in protected (turquoise) color
    - Input fields with underscores showing field length
    - Function key hints at bottom
    """

    # CUA layout: fields start after title (row 0) and instruction (row 1)
    BODY_START_ROW = 3

    def __init__(self, title: str = "", panel_id: str = "",
                 instruction: str = "", help_text: str = "",
                 show_command_line: bool = False):
        """
        Initialize a form.

        Args:
            title: Form title (displayed in uppercase per IBM convention)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Optional instruction text (shown on row 2 per CUA)
            help_text: Panel-level help text shown when F1 is pressed
            show_command_line: Whether to show command line (CUA standard)
        """
        self.title = title.upper() if title else ""
        self.screen = Screen(self.title, panel_id=panel_id, instruction=instruction,
                            help_text=help_text, show_command_line=show_command_line)
        self.current_row = self.BODY_START_ROW
        self.label_col = 2
        self.field_col = 20

    def add_field(
        self,
        label: str,
        length: int = 20,
        field_type: FieldType = FieldType.TEXT,
        default: str = "",
        required: bool = False,
        validator: Optional[Callable[[str], bool]] = None,
        help_text: str = "",
        prompt: Optional[Callable[[], Optional[str]]] = None
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
            help_text: Help text shown when F1 is pressed on this field
            prompt: Optional F4=Prompt callback; should return selected value
                   as string, or None if cancelled

        Returns:
            Self for method chaining
        """
        field = Field(
            row=self.current_row,
            col=self.field_col,
            length=length,
            field_type=field_type,
            label=label,
            default=default,
            required=required,
            validator=validator,
            help_text=help_text,
            prompt=prompt
        )
        self.screen.add_field(field)
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
        self.screen.add_text(self.current_row, self.label_col, text)
        self.current_row += 2
        return self

    def set_short_message(self, message: str) -> "Form":
        """
        Set a short message to display at top-right of screen.

        Args:
            message: Short message text (e.g., "ROWS 1 TO 10")

        Returns:
            Self for method chaining
        """
        self.screen.short_message = message
        return self

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Display the form and return results.

        Returns:
            Dictionary of field values, or None if cancelled
        """
        return self.screen.show()
