"""
ux3270 - A Python library for IBM 3270-like terminal applications.

This library provides a framework for creating terminal applications that use
an IBM 3270-like interaction model: the application creates a form or screen,
hands off control to the user to interact with it, and continues after the
user submits the form.

Subpackages:
    ux3270.panel - Low-level panel building blocks (Screen, Field, Colors)
    ux3270.dialog - High-level dialog components (Menu, Form, Table)
"""

# Re-export panel components for convenience
from .panel import Screen, Field, FieldType, Colors

# Re-export dialog components for convenience
from .dialog import Menu, Form, Table

__version__ = "0.1.0"
__all__ = [
    # Panel components
    "Screen", "Field", "FieldType", "Colors",
    # Dialog components
    "Menu", "Form", "Table",
]
