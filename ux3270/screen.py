"""Screen management for IBM 3270-like terminal applications."""

import sys
import tty
import termios
from typing import List, Optional, Dict, Any

from .field import Field, FieldType
from .colors import Colors


class Screen:
    """
    Manages a terminal screen with IBM 3270-like interaction model.

    The screen can contain multiple fields, display text, and handle user input.
    After creating a screen with fields, call show() to hand off control to the
    user. The method returns when the user submits the form.

    Follows IBM CUA conventions:
    - Title at top in intensified (white) text
    - Labels in protected (turquoise) color
    - Input fields in green with underscores showing field length
    - Error messages in red
    - Function key hints at bottom of screen
    """

    def __init__(self, title: str = ""):
        """
        Initialize a screen.

        Args:
            title: Optional title to display at the top of the screen
        """
        self.title = title.upper() if title else ""
        self.fields: List[Field] = []
        self.static_text: Dict[tuple[int, int], str] = {}
        self.error_message: str = ""

    def add_field(self, field: Field) -> "Screen":
        """
        Add a field to the screen.

        Args:
            field: Field to add

        Returns:
            Self for method chaining
        """
        self.fields.append(field)
        return self

    def add_text(self, row: int, col: int, text: str) -> "Screen":
        """
        Add static text to the screen.

        Args:
            row: Row position (0-indexed)
            col: Column position (0-indexed)
            text: Text to display

        Returns:
            Self for method chaining
        """
        self.static_text[(row, col)] = text
        return self

    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def get_screen_height(self) -> int:
        """Get terminal height."""
        try:
            import os
            return os.get_terminal_size().lines
        except Exception:
            return 24  # IBM 3270 Model 2 standard

    def get_screen_width(self) -> int:
        """Get terminal width."""
        try:
            import os
            return os.get_terminal_size().columns
        except Exception:
            return 80  # IBM 3270 Model 2 standard

    def render(self):
        """Render the screen with all fields and text."""
        self.clear()
        height = self.get_screen_height()
        width = self.get_screen_width()

        # Display title (IBM convention: intensified, at top)
        if self.title:
            self.move_cursor(0, 0)
            title_display = f"═══ {self.title} ═══"
            print(f"{Colors.title(title_display)}", flush=True)

        # Display static text (protected color)
        for (row, col), text in self.static_text.items():
            self.move_cursor(row, col)
            print(f"{Colors.PROTECTED}{text}{Colors.RESET}", end="", flush=True)

        # Display fields with labels
        for field in self.fields:
            # Display label if present (protected/turquoise color per IBM convention)
            # IBM 3270 layout: "Label: " with space before input field
            if field.label:
                self.move_cursor(field.row, field.render_label_col())
                print(f"{Colors.PROTECTED}{field.label}:{Colors.RESET} ", end="", flush=True)

            # Display field value
            self.move_cursor(field.row, field.col)
            if field.field_type == FieldType.READONLY:
                # Readonly fields: dimmed/protected
                print(f"{Colors.DIM}{field.value}{Colors.RESET}", end="", flush=True)
            elif field.field_type == FieldType.PASSWORD:
                # Password fields: show asterisks in input color
                print(f"{Colors.INPUT}{'*' * len(field.value)}{Colors.RESET}", end="", flush=True)
            else:
                # Input fields: green (IBM standard for unprotected)
                print(f"{Colors.INPUT}{field.value}{Colors.RESET}", end="", flush=True)

            # Show field placeholder (underscores indicate field length)
            remaining = field.length - len(field.value)
            if remaining > 0 and field.field_type != FieldType.READONLY:
                print(f"{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)

        # Display error message if present (red per IBM convention)
        if self.error_message:
            self.move_cursor(height - 3, 0)
            print(Colors.error(self.error_message), end="", flush=True)

        # Display function key hints at bottom (IBM 3270 convention)
        self.move_cursor(height - 2, 0)
        print(Colors.dim("─" * min(78, width - 2)), end="", flush=True)
        self.move_cursor(height - 1, 0)
        hints = (
            f"{Colors.info('F3=Cancel')}  "
            f"{Colors.info('Enter=Submit')}  "
            f"{Colors.info('Tab=Next')}"
        )
        print(hints, end="", flush=True)

    def get_input(self, field: Field) -> str:
        """
        Get user input for a field.

        Args:
            field: Field to get input for

        Returns:
            User input string
        """
        if field.field_type == FieldType.READONLY:
            return field.value

        self.move_cursor(field.row, field.col)

        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # Set raw mode for character-by-character input
            tty.setraw(fd)

            value = field.value
            cursor_pos = len(value)

            while True:
                # Display current value
                self.move_cursor(field.row, field.col)
                display_value = value
                if field.field_type == FieldType.PASSWORD:
                    display_value = "*" * len(value)

                # Show value in input color, placeholders dimmed
                print(f"{Colors.INPUT}{display_value}{Colors.RESET}", end="", flush=True)
                print(f"{Colors.DIM}{'_' * (field.length - len(value))}{Colors.RESET}", end="", flush=True)
                self.move_cursor(field.row, field.col + cursor_pos)

                # Read character
                ch = sys.stdin.read(1)

                # Handle special characters
                if ch == '\r' or ch == '\n':  # Enter
                    field.value = value
                    return "SUBMIT"
                elif ch == '\t':  # Tab
                    field.value = value
                    return "NEXT"
                elif ch == '\x1b':  # Escape sequence
                    seq1 = sys.stdin.read(1)
                    if seq1 == '[':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'Z':  # Shift+Tab
                            field.value = value
                            return "PREV"
                        elif seq2 == '1':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '3':
                                sys.stdin.read(1)  # Read the ~
                                return "CANCEL"  # F3
                    elif seq1 == 'O':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'R':  # F3
                            return "CANCEL"
                elif ch == '\x7f' or ch == '\x08':  # Backspace
                    if cursor_pos > 0:
                        value = value[:cursor_pos-1] + value[cursor_pos:]
                        cursor_pos -= 1
                elif ch == '\x03':  # Ctrl+C - also treat as cancel
                    return "CANCEL"
                elif ch.isprintable() and len(value) < field.length:
                    # Handle field type constraints
                    if field.field_type == FieldType.NUMERIC and not ch.isdigit():
                        continue
                    value = value[:cursor_pos] + ch + value[cursor_pos:]
                    cursor_pos += 1

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def show(self) -> Dict[str, Any]:
        """
        Display the screen and handle user interaction.

        This implements the IBM 3270 interaction model: the application creates
        a form, hands off control to the user, and continues after submission.

        Returns:
            Dictionary mapping field labels to values
        """
        if not self.fields:
            raise ValueError("Screen must have at least one field")

        current_field_idx = 0

        # Skip readonly fields initially
        while (current_field_idx < len(self.fields) and
               self.fields[current_field_idx].field_type == FieldType.READONLY):
            current_field_idx += 1

        if current_field_idx >= len(self.fields):
            # All fields are readonly, just display and wait for enter
            self.render()
            input(f"\n{Colors.dim('Press Enter to continue...')}")
            return self._get_results()

        try:
            while True:
                self.error_message = ""
                self.render()

                current_field = self.fields[current_field_idx]
                action = self.get_input(current_field)

                if action == "NEXT":
                    # Move to next editable field
                    next_idx = current_field_idx + 1
                    while next_idx < len(self.fields):
                        if self.fields[next_idx].field_type != FieldType.READONLY:
                            current_field_idx = next_idx
                            break
                        next_idx += 1
                    else:
                        # Wrap to first field
                        current_field_idx = 0
                        while (current_field_idx < len(self.fields) and
                               self.fields[current_field_idx].field_type == FieldType.READONLY):
                            current_field_idx += 1

                elif action == "PREV":
                    # Move to previous editable field
                    prev_idx = current_field_idx - 1
                    while prev_idx >= 0:
                        if self.fields[prev_idx].field_type != FieldType.READONLY:
                            current_field_idx = prev_idx
                            break
                        prev_idx -= 1
                    else:
                        # Wrap to last field
                        current_field_idx = len(self.fields) - 1
                        while (current_field_idx >= 0 and
                               self.fields[current_field_idx].field_type == FieldType.READONLY):
                            current_field_idx -= 1

                elif action == "CANCEL":
                    # F3 = Cancel/Return (IBM standard)
                    self.clear()
                    return None

                elif action == "SUBMIT":
                    # Validate all fields
                    valid = True
                    for field in self.fields:
                        is_valid, error = field.validate()
                        if not is_valid:
                            self.error_message = error
                            valid = False
                            break

                    if valid:
                        self.clear()
                        return self._get_results()

        except KeyboardInterrupt:
            # Ctrl+C during raw mode - treat as cancel
            self.clear()
            return None

    def _get_results(self) -> Dict[str, Any]:
        """Get results as a dictionary."""
        results = {}
        for field in self.fields:
            key = field.label if field.label else f"field_{self.fields.index(field)}"
            results[key] = field.value
        return results
