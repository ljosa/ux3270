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

    # CUA layout constants (0-indexed row offsets from edges)
    TITLE_ROW = 0           # Row for panel ID and title
    INSTRUCTION_ROW = 1     # Row for instruction text
    BODY_START_ROW = 2      # First row of panel body

    def __init__(self, title: str = "", panel_id: str = "", instruction: str = "",
                 help_text: str = "", show_command_line: bool = False):
        """
        Initialize a screen.

        Args:
            title: Optional title to display at the top of the screen
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Optional instruction text (shown on row 2 per CUA)
            help_text: Help text shown when F1 is pressed (panel-level help)
            show_command_line: Whether to show command line (CUA standard)
        """
        self.title = title.upper() if title else ""
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.help_text = help_text
        self.show_command_line = show_command_line
        self.fields: List[Field] = []
        self.static_text: Dict[tuple[int, int], str] = {}
        self.error_message: str = ""
        self.short_message: str = ""  # Short message at top-right
        self._command_value: str = ""  # Current command line value

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

    def render(self, in_command_line: bool = False, current_field: "Field" = None):
        """Render the screen with all fields and text following CUA layout.

        CUA Layout (adapted for variable height):
        - Row 0: Panel ID (left) + Title (centered) + Short message (right)
        - Row 1: Instruction line
        - Rows 2 to height-5: Panel body (fields, static text)
        - Row height-4: Message line (long messages/errors)
        - Row height-3: Command line (Command ===>)
        - Row height-2: Separator
        - Row height-1: Function keys

        Args:
            in_command_line: Whether cursor is in command line (for display)
            current_field: Current field (for context-sensitive function keys)
        """
        self.clear()
        height = self.get_screen_height()
        width = self.get_screen_width()

        # Row 0: Panel ID (left), Title (centered), Short message (right)
        self.move_cursor(self.TITLE_ROW, 0)
        if self.panel_id:
            print(f"{Colors.PROTECTED}{self.panel_id}{Colors.RESET}", end="", flush=True)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            self.move_cursor(self.TITLE_ROW, title_col)
            print(f"{Colors.title(self.title)}", end="", flush=True)
        if self.short_message:
            msg_col = max(0, width - len(self.short_message) - 1)
            self.move_cursor(self.TITLE_ROW, msg_col)
            print(f"{Colors.info(self.short_message)}", end="", flush=True)

        # Row 1: Instruction line - CUA standard
        if self.instruction:
            self.move_cursor(self.INSTRUCTION_ROW, 0)
            print(f"{Colors.PROTECTED}{self.instruction}{Colors.RESET}", end="", flush=True)

        # Display static text (protected color)
        for (row, col), text in self.static_text.items():
            self.move_cursor(row, col)
            print(f"{Colors.PROTECTED}{text}{Colors.RESET}", end="", flush=True)

        # Display fields with labels
        for field in self.fields:
            # Display label with required indicator (* before label) per CUA
            if field.label:
                self.move_cursor(field.row, field.render_label_col())
                if field.required:
                    print(f"{Colors.INTENSIFIED}*{Colors.RESET} ", end="", flush=True)
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

        # Message line (height-4): long messages/errors
        if self.error_message:
            self.move_cursor(height - 4, 0)
            print(Colors.error(self.error_message), end="", flush=True)

        # Command line (height-3) - CUA standard
        if self.show_command_line:
            self.move_cursor(height - 3, 0)
            print(f"{Colors.PROTECTED}Command ===>{Colors.RESET} ", end="", flush=True)
            print(f"{Colors.INPUT}{self._command_value}{Colors.RESET}", end="", flush=True)
            cmd_remaining = 60 - len(self._command_value)
            if cmd_remaining > 0:
                print(f"{Colors.DIM}{'_' * cmd_remaining}{Colors.RESET}", end="", flush=True)

        # Separator line (height-2) - full width per CUA
        self.move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys (height-1) - CUA standard, context-sensitive
        self.move_cursor(height - 1, 0)
        fkeys = [Colors.info('F1=Help')]
        if current_field and current_field.prompt:
            fkeys.append(Colors.info('F4=Prompt'))
        fkeys.append(Colors.info('F3=Cancel'))
        fkeys.append(Colors.info('Enter=Submit'))
        print("  ".join(fkeys), end="", flush=True)

    def _show_help(self, field: Field):
        """
        Display help panel for the current field or screen.

        Shows field-specific help if available, otherwise panel-level help.
        CUA convention: help panel with F3=Return to dismiss.
        """
        self.clear()
        height = self.get_screen_height()
        width = self.get_screen_width()

        # Title row
        self.move_cursor(0, 0)
        print(f"{Colors.title('HELP')}", end="", flush=True)

        # Help content
        help_content = field.help_text if field.help_text else self.help_text
        if help_content:
            self.move_cursor(2, 2)
            print(f"{Colors.PROTECTED}{help_content}{Colors.RESET}", end="", flush=True)
        else:
            self.move_cursor(2, 2)
            print(f"{Colors.PROTECTED}No help available for this field.{Colors.RESET}", end="", flush=True)

        # If field has a label, show it
        if field.label:
            self.move_cursor(4, 2)
            print(f"{Colors.PROTECTED}Field: {field.label}{Colors.RESET}", end="", flush=True)

        # Separator
        self.move_cursor(height - 2, 0)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function keys
        self.move_cursor(height - 1, 0)
        print(f"{Colors.info('F3=Return')}  {Colors.info('Enter=Return')}", end="", flush=True)

        # Wait for key press
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n', '\x03'):  # Enter or Ctrl+C
                    break
                if ch == '\x1b':  # Escape sequence
                    seq1 = sys.stdin.read(1)
                    if seq1 == '[':
                        seq2 = sys.stdin.read(1)
                        if seq2 == '1':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '3':
                                sys.stdin.read(1)  # Read ~
                                break  # F3
                    elif seq1 == 'O':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'R':  # F3
                            break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # Re-render the main screen
        self.render()

    # Class-level insert mode state (shared across fields, like real 3270)
    _insert_mode = False

    def get_input(self, field: Field) -> str:
        """
        Get user input for a field with IBM 3270-style editing.

        Supports:
        - Left/Right arrows: cursor movement within field
        - Home/End: beginning/end of field data
        - Delete: delete character at cursor
        - Insert: toggle insert/overwrite mode
        - Backspace: delete character before cursor
        - Ctrl+E or Shift+End: Erase EOF (clear to end of field)
        - F1: Show help for the current field
        - F4: Prompt (request selection list)

        Args:
            field: Field to get input for

        Returns:
            Action string (SUBMIT, NEXT, PREV, CANCEL)
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
                        elif seq2 == 'D':  # Left arrow
                            if cursor_pos > 0:
                                cursor_pos -= 1
                        elif seq2 == 'C':  # Right arrow
                            if cursor_pos < len(value):
                                cursor_pos += 1
                        elif seq2 == 'H':  # Home
                            cursor_pos = 0
                        elif seq2 == 'F':  # End
                            cursor_pos = len(value)
                        elif seq2 == '1':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '~':  # Home (alternate)
                                cursor_pos = 0
                            elif seq3 == '1':
                                sys.stdin.read(1)  # Read the ~
                                # F1 - Show help
                                field.value = value
                                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                                self._show_help(field)
                                tty.setraw(fd)
                            elif seq3 == '3':
                                sys.stdin.read(1)  # Read the ~
                                return "CANCEL"  # F3
                            elif seq3 == '4':
                                sys.stdin.read(1)  # Read the ~
                                # F4 - Prompt (selection list)
                                field.value = value
                                return "PROMPT"
                            elif seq3 == ';':
                                # Could be Shift+End (ESC [ 1 ; 2 F)
                                seq4 = sys.stdin.read(1)
                                seq5 = sys.stdin.read(1)
                                if seq4 == '2' and seq5 == 'F':
                                    # Erase EOF - clear from cursor to end
                                    value = value[:cursor_pos]
                        elif seq2 == '2':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '~':  # Insert
                                Screen._insert_mode = not Screen._insert_mode
                        elif seq2 == '3':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '~':  # Delete
                                if cursor_pos < len(value):
                                    value = value[:cursor_pos] + value[cursor_pos+1:]
                        elif seq2 == '4':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '~':  # End (alternate)
                                cursor_pos = len(value)
                    elif seq1 == 'O':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'P':  # F1
                            field.value = value
                            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                            self._show_help(field)
                            tty.setraw(fd)
                        elif seq2 == 'R':  # F3
                            return "CANCEL"
                        elif seq2 == 'S':  # F4
                            field.value = value
                            return "PROMPT"
                        elif seq2 == 'H':  # Home (alternate)
                            cursor_pos = 0
                        elif seq2 == 'F':  # End (alternate)
                            cursor_pos = len(value)
                elif ch == '\x7f' or ch == '\x08':  # Backspace
                    if cursor_pos > 0:
                        value = value[:cursor_pos-1] + value[cursor_pos:]
                        cursor_pos -= 1
                elif ch == '\x05':  # Ctrl+E = Erase EOF
                    value = value[:cursor_pos]
                elif ch == '\x03':  # Ctrl+C - also treat as cancel
                    return "CANCEL"
                elif ch.isprintable():
                    # Handle field type constraints
                    if field.field_type == FieldType.NUMERIC and not ch.isdigit():
                        continue

                    if Screen._insert_mode:
                        # Insert mode: insert character, shift rest right
                        if len(value) < field.length:
                            value = value[:cursor_pos] + ch + value[cursor_pos:]
                            cursor_pos += 1
                    else:
                        # Overwrite mode (3270 default): replace or append
                        if cursor_pos < len(value):
                            value = value[:cursor_pos] + ch + value[cursor_pos+1:]
                            cursor_pos += 1
                        elif len(value) < field.length:
                            value = value + ch
                            cursor_pos += 1

        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _get_command_input(self) -> str:
        """
        Get user input for the command line with IBM 3270-style editing.

        Returns:
            Action string (SUBMIT, NEXT, PREV, CANCEL)
        """
        height = self.get_screen_height()
        cmd_row = height - 3
        cmd_col = 13  # After "Command ===> "

        self.move_cursor(cmd_row, cmd_col)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)

            value = self._command_value
            cursor_pos = len(value)
            max_length = 60

            while True:
                # Display current value
                self.move_cursor(cmd_row, cmd_col)
                print(f"{Colors.INPUT}{value}{Colors.RESET}", end="", flush=True)
                print(f"{Colors.DIM}{'_' * (max_length - len(value))}{Colors.RESET}", end="", flush=True)
                self.move_cursor(cmd_row, cmd_col + cursor_pos)

                ch = sys.stdin.read(1)

                if ch == '\r' or ch == '\n':
                    self._command_value = value
                    return "SUBMIT"
                elif ch == '\t':
                    self._command_value = value
                    return "NEXT"
                elif ch == '\x1b':
                    seq1 = sys.stdin.read(1)
                    if seq1 == '[':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'Z':  # Shift+Tab
                            self._command_value = value
                            return "PREV"
                        elif seq2 == 'D':  # Left
                            if cursor_pos > 0:
                                cursor_pos -= 1
                        elif seq2 == 'C':  # Right
                            if cursor_pos < len(value):
                                cursor_pos += 1
                        elif seq2 == 'H':  # Home
                            cursor_pos = 0
                        elif seq2 == 'F':  # End
                            cursor_pos = len(value)
                        elif seq2 == '1':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '3':
                                sys.stdin.read(1)
                                return "CANCEL"
                        elif seq2 == '3':
                            seq3 = sys.stdin.read(1)
                            if seq3 == '~':  # Delete
                                if cursor_pos < len(value):
                                    value = value[:cursor_pos] + value[cursor_pos+1:]
                    elif seq1 == 'O':
                        seq2 = sys.stdin.read(1)
                        if seq2 == 'R':
                            return "CANCEL"
                elif ch == '\x7f' or ch == '\x08':  # Backspace
                    if cursor_pos > 0:
                        value = value[:cursor_pos-1] + value[cursor_pos:]
                        cursor_pos -= 1
                elif ch == '\x03':  # Ctrl+C
                    return "CANCEL"
                elif ch.isprintable():
                    if len(value) < max_length:
                        if Screen._insert_mode:
                            value = value[:cursor_pos] + ch + value[cursor_pos:]
                        else:
                            if cursor_pos < len(value):
                                value = value[:cursor_pos] + ch + value[cursor_pos+1:]
                            else:
                                value = value + ch
                        cursor_pos += 1

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _find_first_editable_field(self) -> int:
        """Find index of first editable field."""
        for i, field in enumerate(self.fields):
            if field.field_type != FieldType.READONLY:
                return i
        return -1

    def _find_last_editable_field(self) -> int:
        """Find index of last editable field."""
        for i in range(len(self.fields) - 1, -1, -1):
            if self.fields[i].field_type != FieldType.READONLY:
                return i
        return -1

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

        current_field_idx = self._find_first_editable_field()
        in_command_line = False

        if current_field_idx < 0:
            # All fields are readonly, just display and wait for enter
            self.render()
            input(f"\n{Colors.dim('Press Enter to continue...')}")
            return self._get_results()

        try:
            while True:
                current_field = self.fields[current_field_idx] if not in_command_line else None
                self.render(in_command_line=in_command_line, current_field=current_field)

                if in_command_line:
                    action = self._get_command_input()
                else:
                    action = self.get_input(current_field)

                if action == "NEXT":
                    self.error_message = ""  # Clear error on navigation
                    if in_command_line:
                        # From command line, go to first field
                        in_command_line = False
                        current_field_idx = self._find_first_editable_field()
                    else:
                        # Move to next editable field
                        next_idx = current_field_idx + 1
                        while next_idx < len(self.fields):
                            if self.fields[next_idx].field_type != FieldType.READONLY:
                                current_field_idx = next_idx
                                break
                            next_idx += 1
                        else:
                            # Past last field - go to command line if enabled
                            if self.show_command_line:
                                in_command_line = True
                            else:
                                current_field_idx = self._find_first_editable_field()

                elif action == "PREV":
                    self.error_message = ""  # Clear error on navigation
                    if in_command_line:
                        # From command line, go to last field
                        in_command_line = False
                        current_field_idx = self._find_last_editable_field()
                    else:
                        # Move to previous editable field
                        prev_idx = current_field_idx - 1
                        while prev_idx >= 0:
                            if self.fields[prev_idx].field_type != FieldType.READONLY:
                                current_field_idx = prev_idx
                                break
                            prev_idx -= 1
                        else:
                            # Before first field - go to command line if enabled
                            if self.show_command_line:
                                in_command_line = True
                            else:
                                current_field_idx = self._find_last_editable_field()

                elif action == "CANCEL":
                    # F3 = Cancel/Return (IBM standard)
                    self.clear()
                    return None

                elif action == "PROMPT":
                    # F4 = Prompt (selection list)
                    current_field = self.fields[current_field_idx]
                    if current_field.prompt:
                        # Call the prompt callback
                        result = current_field.prompt()
                        if result is not None:
                            # Set field value to the result
                            current_field.value = str(result)

                elif action == "SUBMIT":
                    # Check for CUA command line commands
                    cmd = self._command_value.strip().upper()
                    if cmd in ("=X", "CANCEL"):
                        # =X is CUA standard for exit/cancel
                        self.clear()
                        return None

                    # Validate all fields
                    valid = True
                    for idx, field in enumerate(self.fields):
                        is_valid, error = field.validate()
                        if not is_valid:
                            self.error_message = error
                            # Move cursor to the invalid field
                            if field.field_type != FieldType.READONLY:
                                current_field_idx = idx
                                in_command_line = False
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
        # Include command line value if shown
        if self.show_command_line and self._command_value:
            results["_command"] = self._command_value
        return results
