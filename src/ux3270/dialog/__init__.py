"""
ux3270.dialog - High-level dialog components for IBM 3270-style applications.

This module provides pre-built dialog patterns:
- Menu: Selection menu with single-key navigation
- Form: Data entry form with automatic field layout
- Table: Tabular data display with pagination
"""

from .menu import Menu
from .form import Form
from .table import Table

__all__ = ["Menu", "Form", "Table"]
