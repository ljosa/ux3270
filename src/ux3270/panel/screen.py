"""Screen management for IBM 3270-like terminal applications.

This module emulates a 3270 terminal's behavior:
- Accepts a screen definition (text at positions with colors, field definitions)
- Renders everything to the terminal
- Handles all field input internally (cursor movement, editing, navigation)
- Returns field values when user presses an AID key (Enter, F3, etc.)
"""

import sys
import tty
import termios
from typing import List, Optional, Dict, Any, Tuple

from .field import Field, FieldType
from .colors import Colors


class Screen:
    """
    Emulates an IBM 3270 terminal screen.

    The screen accepts:
    - Text at positions with optional colors (protected content)
    - Field definitions (unprotected, editable areas)

    When show() is called, the terminal:
    - Renders all text and fields
    - Handles all keyboard input (field editing, navigation)
    - Returns when user presses an AID key (Enter, F3, etc.)
    """

    def __init__(self):
        """Initialize an empty screen."""
        self.fields: List[Field] = []
        self._text: List[Tuple[int, int, str, str]] = []  # (row, col, text, color)
        self._width: Optional[int] = None
        self._height: Optional[int] = None
        self._any_key_mode: bool = False  # Return on any key press (for menus)

    def set_any_key_mode(self, enabled: bool = True) -> "Screen":
        """
        Enable any-key mode where show() returns on any key press.

        Used for menus where single-key selection is needed.

        Args:
            enabled: Whether to enable any-key mode

        Returns:
            Self for method chaining
        """
        self._any_key_mode = enabled
        return self

    def add_field(self, field: Field) -> "Screen":
        """
        Add an input field to the screen.

        Args:
            field: Field definition with position, length, type, etc.

        Returns:
            Self for method chaining
        """
        self.fields.append(field)
        return self

    def add_text(self, row: int, col: int, text: str,
                 color: str = Colors.PROTECTED) -> "Screen":
        """
        Add text to the screen at a specific position.

        Args:
            row: Row position (0-indexed)
            col: Column position (0-indexed)
            text: Text to display
            color: ANSI color code (default: protected/turquoise)

        Returns:
            Self for method chaining
        """
        self._text.append((row, col, text, color))
        return self

    def get_height(self) -> int:
        """Get terminal height."""
        if self._height:
            return self._height
        try:
            import os
            return os.get_terminal_size().lines
        except Exception:
            return 24  # IBM 3270 Model 2 standard

    def get_width(self) -> int:
        """Get terminal width."""
        if self._width:
            return self._width
        try:
            import os
            return os.get_terminal_size().columns
        except Exception:
            return 80  # IBM 3270 Model 2 standard

    def _clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _move_cursor(self, row: int, col: int):
        """Move cursor to specified position (0-indexed)."""
        print(f"\033[{row + 1};{col + 1}H", end="", flush=True)

    def _render_field(self, field: Field):
        """Render a single field with its current value and underscores."""
        self._move_cursor(field.row, field.col)

        if field.field_type == FieldType.READONLY:
            print(f"{Colors.DEFAULT}{field.value}{Colors.RESET}", end="", flush=True)
        elif field.field_type == FieldType.PASSWORD:
            display = "*" * len(field.value)
            remaining = field.length - len(field.value)
            print(f"{Colors.INPUT}{display}{Colors.RESET}", end="", flush=True)
            if remaining > 0:
                print(f"{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)
        else:
            remaining = field.length - len(field.value)
            print(f"{Colors.INPUT}{field.value}{Colors.RESET}", end="", flush=True)
            if remaining > 0:
                print(f"{Colors.DIM}{'_' * remaining}{Colors.RESET}", end="", flush=True)

    def render(self):
        """Render the entire screen (text and fields)."""
        self._clear()

        # Render all text
        for row, col, text, color in self._text:
            self._move_cursor(row, col)
            print(f"{color}{text}{Colors.RESET}", end="", flush=True)

        # Render all fields
        for field in self.fields:
            self._render_field(field)

    def _read_key(self) -> str:
        """
        Read a key from stdin, handling escape sequences.

        Returns:
            Key identifier string
        """
        ch = sys.stdin.read(1)

        if ch == '\r' or ch == '\n':
            return 'ENTER'
        elif ch == '\t':
            return 'TAB'
        elif ch == '\x7f' or ch == '\x08':
            return 'BACKSPACE'
        elif ch == '\x03':
            return 'CTRL_C'
        elif ch == '\x05':
            return 'CTRL_E'
        elif ch == '\x1b':
            seq1 = sys.stdin.read(1)
            if seq1 == '[':
                seq2 = sys.stdin.read(1)
                if seq2 == 'A':
                    return 'UP'
                elif seq2 == 'B':
                    return 'DOWN'
                elif seq2 == 'C':
                    return 'RIGHT'
                elif seq2 == 'D':
                    return 'LEFT'
                elif seq2 == 'H':
                    return 'HOME'
                elif seq2 == 'F':
                    return 'END'
                elif seq2 == 'Z':
                    return 'SHIFT_TAB'
                elif seq2 == '1':
                    seq3 = sys.stdin.read(1)
                    if seq3 == '~':
                        return 'HOME'
                    elif seq3 == '1':
                        sys.stdin.read(1)
                        return 'F1'
                    elif seq3 == '3':
                        sys.stdin.read(1)
                        return 'F3'
                    elif seq3 == '4':
                        sys.stdin.read(1)
                        return 'F4'
                    elif seq3 == '5':
                        sys.stdin.read(1)
                        return 'F5'
                    elif seq3 == '7':
                        sys.stdin.read(1)
                        return 'F6'
                    elif seq3 == '8':
                        sys.stdin.read(1)
                        return 'F7'
                    elif seq3 == '9':
                        sys.stdin.read(1)
                        return 'F8'
                    elif seq3 == ';':
                        seq4 = sys.stdin.read(1)
                        seq5 = sys.stdin.read(1)
                        if seq4 == '2' and seq5 == 'F':
                            return 'SHIFT_END'
                elif seq2 == '2':
                    seq3 = sys.stdin.read(1)
                    if seq3 == '~':
                        return 'INSERT'
                    elif seq3 == '0':
                        sys.stdin.read(1)
                        return 'F9'
                    elif seq3 == '1':
                        sys.stdin.read(1)
                        return 'F10'
                elif seq2 == '3':
                    seq3 = sys.stdin.read(1)
                    if seq3 == '~':
                        return 'DELETE'
                elif seq2 == '4':
                    seq3 = sys.stdin.read(1)
                    if seq3 == '~':
                        return 'END'
                elif seq2 == '5':
                    sys.stdin.read(1)
                    return 'PGUP'
                elif seq2 == '6':
                    sys.stdin.read(1)
                    return 'PGDN'
            elif seq1 == 'O':
                seq2 = sys.stdin.read(1)
                if seq2 == 'P':
                    return 'F1'
                elif seq2 == 'Q':
                    return 'F2'
                elif seq2 == 'R':
                    return 'F3'
                elif seq2 == 'S':
                    return 'F4'
                elif seq2 == 'H':
                    return 'HOME'
                elif seq2 == 'F':
                    return 'END'
            return 'ESC'

        return ch

    # Class-level insert mode (shared across fields, like real 3270)
    _insert_mode = False

    def _handle_field_key(self, field: Field, key: str, cursor_pos: int) -> Tuple[str, int]:
        """
        Handle a key press for a field.

        Args:
            field: The field being edited
            key: Key identifier
            cursor_pos: Current cursor position within field

        Returns:
            Tuple of (action, new_cursor_pos)
        """
        if field.field_type == FieldType.READONLY:
            if key == 'TAB':
                return "NEXT", cursor_pos
            elif key == 'SHIFT_TAB':
                return "PREV", cursor_pos
            elif key == 'ENTER':
                return "ENTER", cursor_pos
            elif key in ('F3', 'CTRL_C'):
                return "F3", cursor_pos
            elif key == 'UP':
                return "UP", cursor_pos
            elif key == 'DOWN':
                return "DOWN", cursor_pos
            return "", cursor_pos

        value = field.value

        # AID keys (return control to caller)
        if key == 'ENTER':
            return "ENTER", cursor_pos
        elif key in ('F3', 'CTRL_C'):
            return "F3", cursor_pos
        elif key == 'F1':
            return "F1", cursor_pos
        elif key == 'F4':
            return "F4", cursor_pos
        elif key == 'F5':
            return "F5", cursor_pos
        elif key == 'F6':
            return "F6", cursor_pos
        elif key == 'F7':
            return "F7", cursor_pos
        elif key == 'F8':
            return "F8", cursor_pos
        elif key == 'PGUP':
            return "PGUP", cursor_pos
        elif key == 'PGDN':
            return "PGDN", cursor_pos

        # Field navigation
        elif key == 'TAB':
            return "NEXT", cursor_pos
        elif key == 'SHIFT_TAB':
            return "PREV", cursor_pos
        elif key == 'UP':
            return "UP", cursor_pos
        elif key == 'DOWN':
            return "DOWN", cursor_pos

        # Cursor movement within field
        elif key == 'LEFT':
            if cursor_pos > 0:
                cursor_pos -= 1
        elif key == 'RIGHT':
            if cursor_pos < len(value):
                cursor_pos += 1
        elif key == 'HOME':
            cursor_pos = 0
        elif key == 'END':
            cursor_pos = len(value)

        # Editing
        elif key == 'BACKSPACE':
            if cursor_pos > 0:
                field.value = value[:cursor_pos-1] + value[cursor_pos:]
                cursor_pos -= 1
        elif key == 'DELETE':
            if cursor_pos < len(value):
                field.value = value[:cursor_pos] + value[cursor_pos+1:]
        elif key == 'INSERT':
            Screen._insert_mode = not Screen._insert_mode
        elif key in ('CTRL_E', 'SHIFT_END'):
            field.value = value[:cursor_pos]

        # Character input
        elif len(key) == 1 and key.isprintable():
            if field.field_type == FieldType.NUMERIC:
                if not (key.isdigit() or key in '.-'):
                    return "", cursor_pos

            if Screen._insert_mode:
                if len(value) < field.length:
                    field.value = value[:cursor_pos] + key + value[cursor_pos:]
                    cursor_pos += 1
            else:
                if cursor_pos < len(value):
                    field.value = value[:cursor_pos] + key + value[cursor_pos+1:]
                    cursor_pos += 1
                elif len(value) < field.length:
                    field.value = value + key
                    cursor_pos += 1

            # Auto-advance when field is full
            if len(field.value) >= field.length:
                return "FULL", cursor_pos

        return "", cursor_pos

    def _find_next_field(self, current_idx: int) -> int:
        """Find next editable field index, wrapping around."""
        if not self.fields:
            return -1

        editable = [(i, f) for i, f in enumerate(self.fields)
                    if f.field_type != FieldType.READONLY]
        if not editable:
            return -1

        # Find current position in editable list
        current_editable_idx = -1
        for i, (idx, _) in enumerate(editable):
            if idx == current_idx:
                current_editable_idx = i
                break

        # Move to next (or first if not found/at end)
        next_editable_idx = (current_editable_idx + 1) % len(editable)
        return editable[next_editable_idx][0]

    def _find_prev_field(self, current_idx: int) -> int:
        """Find previous editable field index, wrapping around."""
        if not self.fields:
            return -1

        editable = [(i, f) for i, f in enumerate(self.fields)
                    if f.field_type != FieldType.READONLY]
        if not editable:
            return -1

        current_editable_idx = -1
        for i, (idx, _) in enumerate(editable):
            if idx == current_idx:
                current_editable_idx = i
                break

        prev_editable_idx = (current_editable_idx - 1) % len(editable)
        return editable[prev_editable_idx][0]

    def _find_field_above(self, current_idx: int) -> int:
        """Find field above current one (by row position)."""
        if current_idx < 0 or current_idx >= len(self.fields):
            return current_idx

        current = self.fields[current_idx]
        candidates = [(i, f) for i, f in enumerate(self.fields)
                      if f.row < current.row and f.field_type != FieldType.READONLY]

        if not candidates:
            return current_idx

        # Find closest by row, then by column distance
        candidates.sort(key=lambda x: (-x[1].row, abs(x[1].col - current.col)))
        return candidates[0][0]

    def _find_field_below(self, current_idx: int) -> int:
        """Find field below current one (by row position)."""
        if current_idx < 0 or current_idx >= len(self.fields):
            return current_idx

        current = self.fields[current_idx]
        candidates = [(i, f) for i, f in enumerate(self.fields)
                      if f.row > current.row and f.field_type != FieldType.READONLY]

        if not candidates:
            return current_idx

        candidates.sort(key=lambda x: (x[1].row, abs(x[1].col - current.col)))
        return candidates[0][0]

    def _find_first_editable(self) -> int:
        """Find index of first editable field."""
        for i, f in enumerate(self.fields):
            if f.field_type != FieldType.READONLY:
                return i
        return -1

    def show(self) -> Optional[Dict[str, Any]]:
        """
        Display the screen and handle user input.

        Returns:
            Dictionary with:
            - "aid": The AID key pressed (ENTER, F3, F6, etc.)
            - "fields": Dict mapping field labels to values
            Returns None if no fields defined.
        """
        if not self.fields:
            # No fields - just display and wait for key
            self.render()
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    key = self._read_key()
                    # AID keys always return
                    if key in ('ENTER', 'F3', 'CTRL_C', 'F1', 'F4', 'F5', 'F6', 'F7', 'F8'):
                        self._clear()
                        return {"aid": key if key != 'CTRL_C' else 'F3', "fields": {}, "key": key}
                    # In any-key mode, return on printable characters too
                    if self._any_key_mode and len(key) == 1 and key.isprintable():
                        self._clear()
                        return {"aid": "KEY", "fields": {}, "key": key}
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        current_field_idx = self._find_first_editable()
        if current_field_idx < 0:
            current_field_idx = 0

        cursor_pos = len(self.fields[current_field_idx].value)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            while True:
                # Render screen
                self.render()

                # Position cursor in current field
                field = self.fields[current_field_idx]
                self._move_cursor(field.row, field.col + cursor_pos)

                # Read and handle key
                tty.setraw(fd)
                key = self._read_key()
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                action, cursor_pos = self._handle_field_key(field, key, cursor_pos)

                # AID keys - return control to caller
                if action in ('ENTER', 'F3', 'F1', 'F4', 'F5', 'F6', 'F7', 'F8', 'PGUP', 'PGDN'):
                    self._clear()
                    fields_dict = {}
                    for f in self.fields:
                        key_name = f.label if f.label else f"field_{self.fields.index(f)}"
                        fields_dict[key_name] = f.value
                    # Include current field label for context-sensitive help
                    current_field_label = field.label if field.label else ""
                    return {"aid": action, "fields": fields_dict, "current_field": current_field_label}

                # Field navigation
                elif action == "NEXT" or action == "FULL":
                    new_idx = self._find_next_field(current_field_idx)
                    if new_idx != current_field_idx:
                        current_field_idx = new_idx
                        cursor_pos = len(self.fields[current_field_idx].value)

                elif action == "PREV":
                    new_idx = self._find_prev_field(current_field_idx)
                    if new_idx != current_field_idx:
                        current_field_idx = new_idx
                        cursor_pos = len(self.fields[current_field_idx].value)

                elif action == "UP":
                    new_idx = self._find_field_above(current_field_idx)
                    if new_idx != current_field_idx:
                        current_field_idx = new_idx
                        cursor_pos = min(cursor_pos, len(self.fields[current_field_idx].value))

                elif action == "DOWN":
                    new_idx = self._find_field_below(current_field_idx)
                    if new_idx != current_field_idx:
                        current_field_idx = new_idx
                        cursor_pos = min(cursor_pos, len(self.fields[current_field_idx].value))

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def get_field_values(self) -> Dict[str, str]:
        """Get all field values as a dictionary."""
        result = {}
        for f in self.fields:
            key = f.label if f.label else f"field_{self.fields.index(f)}"
            result[key] = f.value
        return result
