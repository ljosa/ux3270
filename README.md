# ux3270

IBM 3270-like terminal UI library for Python.

## Overview

Create terminal applications with an IBM 3270-style interaction model: display a form, let the user fill it in, continue when they submit.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from ux3270 import Screen, Field, FieldType
from ux3270_ui import Menu, Form, Table

# Create a form
form = Form("DATA ENTRY")
form.add_field("Name", length=30, required=True)
form.add_field("Email", length=40)
result = form.show()
if result:  # None if user cancelled with F3
    print(f"Hello, {result['Name']}!")

# Create a menu
menu = Menu("MAIN MENU")
menu.add_item("1", "Option 1", lambda: print("Selected 1"))
menu.add_item("2", "Option 2", lambda: print("Selected 2"))
menu.run()  # Runs until user exits with F3 or X

# Display a table (with pagination)
table = Table("RESULTS", ["ID", "Name", "Status"])
table.add_row("001", "Item 1", "Active")
table.add_row("002", "Item 2", "Inactive")
table.show()  # F7/F8 to page up/down
```

## Demo App

The inventory management system demonstrates the library:

```bash
# Load sample data and run
inventory-app --demo

# Or just run (empty database)
inventory-app

# Other options
inventory-app --help
```

## Keyboard Controls

| Context | Key | Action |
|---------|-----|--------|
| Forms | Tab | Next field |
| Forms | Shift+Tab | Previous field |
| Forms | Enter | Submit |
| Forms | F3 | Cancel |
| Menus | 1-9, A-Z | Select item |
| Menus | F3, X | Exit |
| Tables | F7 | Page up |
| Tables | F8 | Page down |
| Tables | F3, Enter | Return |

## IBM 3270 Colors

The library uses IBM 3270 color conventions:
- **Green**: Input fields
- **Turquoise**: Labels (protected fields)
- **White**: Titles, headers (intensified)
- **Red**: Error messages
- **Yellow**: Warnings

## Requirements

- Python 3.8+
- Unix-like system (Linux, macOS)
- Terminal with ANSI support

## License

MIT
