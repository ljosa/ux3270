# Migration Guide: ux3270 Architecture Refactoring

This guide covers the breaking changes from the recent refactoring that separated concerns between the panel layer (terminal emulation) and dialog layer (controllers).

## Overview

The key architectural change: **Screen is now a low-level terminal emulator**. It accepts a screen definition (text + fields) and handles all rendering and input internally. Dialogs build Screen definitions and hand off control to Screen.

## Screen API Changes

### Before
```python
from ux3270.panel import Screen, Field

screen = Screen("MY TITLE", panel_id="PNL001", instruction="Enter data",
                help_text="Press F1 for help", show_command_line=False)
screen.add_text(4, 2, "Name:")
screen.add_field(Field(row=4, col=10, length=20, label="Name"))
result = screen.show()
# result was a dict of field values, or None
if result:
    print(result["Name"])
```

### After
```python
from ux3270.panel import Screen, Field, Colors

screen = Screen()  # No constructor parameters
# Add title, panel_id, instruction as text with positions and colors
screen.add_text(0, 0, "PNL001", Colors.PROTECTED)
screen.add_text(0, 35, "MY TITLE", Colors.INTENSIFIED)
screen.add_text(1, 0, "Enter data", Colors.PROTECTED)
screen.add_text(4, 2, "Name:", Colors.PROTECTED)
screen.add_field(Field(row=4, col=10, length=20, label="Name"))
result = screen.show()
# result is now {"aid": "ENTER", "fields": {...}, "current_field": "Name"}
if result and result["aid"] != "F3":
    print(result["fields"]["Name"])
```

### Key differences:
- `Screen()` takes no parameters
- Use `add_text(row, col, text, color)` for all static content including title, panel_id, instructions
- `show()` returns `{"aid": key, "fields": dict, "current_field": label}` instead of just fields
- Check `result["aid"]` to determine which key was pressed (ENTER, F3, F1, etc.)
- Access field values via `result["fields"]`

## Colors

Always specify colors when adding text:
- `Colors.PROTECTED` - Standard protected text (turquoise)
- `Colors.INTENSIFIED` - Highlighted text (white/bold) - use for titles
- `Colors.DIM` - Dimmed text - use for separators
- `Colors.DEFAULT` - Default input color (green)
- `Colors.INPUT` - Input field color

## Form Changes

Form still works as a high-level API, but some parameters changed:

### Before
```python
form = Form("TITLE", panel_id="PNL001", instruction="...",
            help_text="...", show_command_line=True)
```

### After
```python
form = Form("TITLE", panel_id="PNL001", instruction="...", help_text="...")
# show_command_line parameter removed
```

Form handles F1 (help) and F4 (prompt) internally now.

## WorkWithList Changes

### Return value on F3

**Before:** `show()` returned `[]` on F3 (cancel)

**After:** `show()` returns `None` on F3 (cancel), `[]` when Enter pressed with no actions

```python
result = wwl.show()
if result is None:
    return  # User cancelled with F3
if not result:
    # Enter pressed but no actions selected
    pass
for action in result:
    # Process actions
    pass
```

### Type annotation
```python
def show(self) -> Optional[List[Dict[str, Any]]]:
```

## SelectionList Changes

SelectionList now uses Screen internally instead of doing its own rendering. The API is unchanged, but it's now consistent with other dialogs.

## Dialog Layer Rules

Dialogs should **never** print directly to the terminal. All terminal operations go through Screen:

- Don't use `print("\033[...")` escape sequences
- Don't use `sys.stdout.write()`
- Build a Screen, call `screen.show()`, process the result

The Screen handles:
- Clearing the screen
- Rendering text and fields
- Cursor positioning
- Input handling
- Returning control on AID keys

## AID Keys

Screen returns these AID (Attention Identifier) keys in `result["aid"]`:
- `ENTER` - Enter key
- `F1` through `F10` - Function keys
- `F3` - Typically used for Exit/Cancel
- `PGUP`, `PGDN` - Page up/down

## Example: Converting a Custom Dialog

### Before
```python
class MyDialog:
    def show(self):
        screen = Screen("MY DIALOG", panel_id="DLG001")
        screen.add_field(Field(row=3, col=10, length=20, label="Input"))
        result = screen.show()
        if result is None:
            return None
        return result["Input"]
```

### After
```python
class MyDialog:
    def show(self):
        screen = Screen()
        screen.add_text(0, 0, "DLG001", Colors.PROTECTED)
        screen.add_text(0, 35, "MY DIALOG", Colors.INTENSIFIED)
        screen.add_text(3, 2, "Input:", Colors.PROTECTED)
        screen.add_field(Field(row=3, col=10, length=20, label="Input"))

        result = screen.show()
        if result is None or result["aid"] == "F3":
            return None
        return result["fields"]["Input"]
```

## Checklist

- [ ] Update `Screen()` calls to remove constructor parameters
- [ ] Add title/panel_id/instruction using `add_text()` with colors
- [ ] Update `show()` result handling to use `result["aid"]` and `result["fields"]`
- [ ] Check for `result is None` or `result["aid"] == "F3"` for cancellation
- [ ] Remove any direct `print()` calls with escape sequences from dialog code
- [ ] Update WorkWithList result checking (`None` = cancelled, `[]` = no actions)
