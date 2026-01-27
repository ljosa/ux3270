"""
ux3270.panel - Low-level panel building blocks for IBM 3270-style applications.

This module provides the fundamental components for creating panels:
- Screen: Terminal screen management and input handling
- Field: Input field definition with positioning and attributes
- FieldType: Field type enumeration (TEXT, NUMERIC, PASSWORD, READONLY)
- Colors: IBM 3270 color definitions
"""

from .screen import Screen
from .field import Field, FieldType
from .colors import Colors

__all__ = ["Screen", "Field", "FieldType", "Colors"]
