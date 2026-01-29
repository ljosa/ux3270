# Panel Layer API

The panel layer provides low-level terminal emulation. Most applications use the dialog layer, but the panel layer is available for custom components.

## Import

```python
from ux3270.panel import Screen, Field, FieldType, Colors
```

## Screen

The Screen class is a low-level terminal emulator. It accepts a screen definition (text and fields) and handles all rendering and input.

```python
from ux3270.panel import Screen, Field, Colors

screen = Screen()

# Add static text
screen.add_text(0, 0, "PANEL01", Colors.PROTECTED)
screen.add_text(0, 35, "MY SCREEN", Colors.INTENSIFIED)
screen.add_text(2, 2, "Enter data:", Colors.PROTECTED)

# Add input field
screen.add_field(Field(row=4, col=2, length=20, label="Name"))

# Show and get result
result = screen.show()
# result = {"aid": "ENTER", "fields": {"Name": "value"}, "current_field": "Name"}
```

### Screen Methods

::: ux3270.panel.Screen
    options:
      members:
        - add_text
        - add_field
        - set_any_key_mode
        - show
        - get_field_values

## Field

Represents an input field on a screen.

```python
from ux3270.panel import Field, FieldType

field = Field(
    row=4,
    col=10,
    length=20,
    label="Username",
    field_type=FieldType.TEXT,
    default="",
    required=False,
    validator=None,
    prompt=None
)
```

::: ux3270.panel.Field

## FieldType

Enumeration of field types.

| Value | Description |
|-------|-------------|
| `FieldType.TEXT` | Standard text input |
| `FieldType.NUMERIC` | Numbers only |
| `FieldType.PASSWORD` | Hidden input (asterisks) |
| `FieldType.READONLY` | Display only |

## Colors

Constants for IBM 3270 colors.

| Constant | Color | Usage |
|----------|-------|-------|
| `Colors.DEFAULT` | Green | Input fields |
| `Colors.INPUT` | Green | Input fields |
| `Colors.PROTECTED` | Turquoise | Labels, static text |
| `Colors.INTENSIFIED` | White | Titles, headers |
| `Colors.DIM` | Gray | Separators |
| `Colors.ERROR` | Red | Error messages |
| `Colors.WARNING` | Yellow | Warnings |
| `Colors.SUCCESS` | Green | Success messages |

## AID Keys

The `result["aid"]` value indicates which key was pressed:

| AID | Key |
|-----|-----|
| `ENTER` | Enter key |
| `F1` - `F10` | Function keys |
| `PGUP` | Page Up |
| `PGDN` | Page Down |
| `KEY` | Any key (in any-key mode) |
