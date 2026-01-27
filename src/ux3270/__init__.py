"""
ux3270 - A Python library for IBM 3270-like terminal applications.

This library provides a framework for creating terminal applications that use
an IBM 3270-like interaction model: the application creates a form or screen,
hands off control to the user to interact with it, and continues after the
user submits the form.
"""

from .screen import Screen
from .field import Field, FieldType
from .colors import Colors

__version__ = "0.1.0"
__all__ = ["Screen", "Field", "FieldType", "Colors"]
