"""Form UI component for IBM 3270-style applications."""

from typing import Dict, Any, List, Optional, Callable
from ux3270 import Screen, Field, FieldType


class Form:
    """
    High-level form builder with IBM 3270-style layout.
    
    Automatically handles layout and spacing for fields.
    """
    
    def __init__(self, title: str = ""):
        """
        Initialize a form.
        
        Args:
            title: Form title
        """
        self.title = title
        self.screen = Screen(title)
        self.current_row = 2
        self.label_col = 2
        self.field_col = 20
        
    def add_field(
        self,
        label: str,
        length: int = 20,
        field_type: FieldType = FieldType.TEXT,
        default: str = "",
        required: bool = False,
        validator: Optional[Callable[[str], bool]] = None
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
            validator=validator
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
        
    def show(self) -> Dict[str, Any]:
        """
        Display the form and return results.
        
        Returns:
            Dictionary of field values
        """
        return self.screen.show()
