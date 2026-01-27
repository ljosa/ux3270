"""Field definitions for terminal forms."""

from enum import Enum
from typing import Any, Optional, Callable


class FieldType(Enum):
    """Types of input fields."""
    TEXT = "text"
    PASSWORD = "password"
    NUMERIC = "numeric"
    READONLY = "readonly"


class Field:
    """
    Represents an input field on a terminal screen.
    
    An IBM 3270 field has attributes like position, length, protected status,
    and can have different display attributes.
    """
    
    def __init__(
        self,
        row: int,
        col: int,
        length: int,
        field_type: FieldType = FieldType.TEXT,
        label: str = "",
        default: str = "",
        required: bool = False,
        validator: Optional[Callable[[str], bool]] = None,
        help_text: str = "",
        prompt: Optional[Callable[[], Any]] = None
    ):
        """
        Initialize a field.

        Args:
            row: Row position (0-indexed)
            col: Column position (0-indexed)
            length: Maximum length of the field
            field_type: Type of field (text, password, numeric, readonly)
            label: Optional label to display before the field
            default: Default value
            required: Whether the field is required
            validator: Optional validation function
            help_text: Help text shown when F1 is pressed on this field
            prompt: Optional callback for F4=Prompt; should return selected value
                   as string, or None if cancelled
        """
        self.row = row
        self.col = col
        self.length = length
        self.field_type = field_type
        self.label = label
        self.default = default
        self.required = required
        self.validator = validator
        self.help_text = help_text
        self.prompt = prompt
        self._value = default
        
    @property
    def value(self) -> str:
        """Get the current field value."""
        return self._value
    
    @value.setter
    def value(self, val: str):
        """Set the field value."""
        self._value = val
        
    def validate(self) -> tuple[bool, str]:
        """
        Validate the field value.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.required and not self._value.strip():
            return False, f"{self.label or 'Field'} is required"
            
        if self.validator and not self.validator(self._value):
            return False, f"{self.label or 'Field'} has invalid value"
            
        return True, ""
        
    def render_label_col(self) -> int:
        """Calculate the column position for the label.

        CUA convention: * Label: <space> [input field]
        Required fields have asterisk prefix.
        So we need room for: optional asterisk + label text + colon + space
        """
        if not self.label:
            return self.col
        # Place label before the field: label + ": " (colon + space)
        offset = len(self.label) + 2
        # Add space for required indicator "* "
        if self.required:
            offset += 2
        return self.col - offset
