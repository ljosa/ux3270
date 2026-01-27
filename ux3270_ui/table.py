"""Table display component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Dict, Any


class Table:
    """
    IBM 3270-style table/list display.
    
    Displays tabular data with column headers and scrolling.
    """
    
    def __init__(self, title: str = "", columns: List[str] = None):
        """
        Initialize a table.
        
        Args:
            title: Table title
            columns: List of column headers
        """
        self.title = title
        self.columns = columns or []
        self.rows: List[List[str]] = []
        self.col_widths: List[int] = []
        
    def add_row(self, *values) -> "Table":
        """
        Add a row to the table.
        
        Args:
            values: Column values for the row
            
        Returns:
            Self for method chaining
        """
        self.rows.append(list(values))
        return self
        
    def _calculate_widths(self):
        """Calculate column widths based on content."""
        if not self.columns:
            return
            
        self.col_widths = [len(col) for col in self.columns]
        
        for row in self.rows:
            for i, val in enumerate(row):
                if i < len(self.col_widths):
                    self.col_widths[i] = max(self.col_widths[i], len(str(val)))
                    
    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)
        
    def render(self):
        """Render the table."""
        self.clear()
        self._calculate_widths()
        
        # Display title
        if self.title:
            print("╔" + "═" * (len(self.title) + 2) + "╗")
            print(f"║ \033[1m{self.title}\033[0m ║")
            print("╚" + "═" * (len(self.title) + 2) + "╝")
            print()
            
        # Display column headers
        if self.columns:
            header_parts = []
            for i, col in enumerate(self.columns):
                width = self.col_widths[i] if i < len(self.col_widths) else len(col)
                header_parts.append(f"\033[1m{col.ljust(width)}\033[0m")
            print("  " + " │ ".join(header_parts))
            
            # Separator line
            sep_parts = []
            for width in self.col_widths:
                sep_parts.append("─" * width)
            print("  " + "─┼─".join(sep_parts))
            
        # Display rows
        for row in self.rows:
            row_parts = []
            for i, val in enumerate(row):
                width = self.col_widths[i] if i < len(self.col_widths) else len(str(val))
                row_parts.append(str(val).ljust(width))
            print("  " + " │ ".join(row_parts))
            
        print()
        if self.rows:
            print(f"\033[2mTotal: {len(self.rows)} rows\033[0m")
            
    def show(self):
        """Display the table and wait for user to press a key."""
        self.render()
        print("\n\033[2mPress any key to continue...\033[0m")
        
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Set raw mode for single character input
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.clear()
