"""
ux3270.dialog - High-level dialog components for IBM 3270-style applications.

This module provides pre-built dialog patterns:
- Menu: Selection menu with single-key navigation
- Form: Data entry form with automatic field layout
- Table: Tabular data display with pagination
- WorkWithList: List with action codes for editing/deleting records
- SelectionList: F4=Prompt selection list for field lookups
- MessagePanel: Information/error message display
"""

from .menu import Menu
from .form import Form
from .table import Table
from .work_with_list import WorkWithList
from .selection_list import SelectionList
from .message import MessagePanel, show_message

__all__ = ["Menu", "Form", "Table", "WorkWithList", "SelectionList", "MessagePanel", "show_message"]
