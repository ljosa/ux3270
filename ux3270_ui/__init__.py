"""
ux3270_ui - High-level library for IBM 3270-style terminal applications.

This library builds on ux3270 to provide common UI patterns and IBM 3270-like
visual styling for terminal applications.
"""

from .menu import Menu
from .form import Form
from .table import Table

__version__ = "0.1.0"
__all__ = ["Menu", "Form", "Table"]
