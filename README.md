# ux3270

IBM 3270-like terminal UI library for Python.

## Overview

Create terminal applications with an IBM 3270-style interaction model: display a form, let the user fill it in, continue when they submit.

## Screenshots

The inventory management demo app showcases the library's capabilities:

| Main Menu | Inventory List | Update Form |
|:---------:|:--------------:|:-----------:|
| ![Main Menu](docs/images/screenshot1.png) | ![Inventory List](docs/images/screenshot2.png) | ![Update Form](docs/images/screenshot3.png) |
| Menu with single-key selection | Table with F7/F8 pagination | Form with required fields and F4=Prompt |

## Installation

As a dependency in your project:

```bash
uv add git+https://github.com/ljosa/ux3270.git
```

For development of ux3270 itself:

```bash
git clone https://github.com/ljosa/ux3270.git
cd ux3270
uv venv && uv pip install -e .
```

## Quick Start

```python
from ux3270.dialog import Menu, Form, Table, TabularEntry, WorkWithList, SelectionList, show_message

# Create a form with help text
form = Form("DATA ENTRY", help_text="Enter your information")
form.add_field("Name", length=30, required=True,
               help_text="Your full name")
form.add_field("Email", length=40)
result = form.show()  # F1 for help, F3 to cancel
if result:
    print(f"Hello, {result['Name']}!")

# Form with F4=Prompt lookup
def select_dept():
    sel = SelectionList("SELECT DEPARTMENT", ["Code", "Name"])
    sel.add_row(Code="ENG", Name="Engineering")
    sel.add_row(Code="SAL", Name="Sales")
    selected = sel.show()
    return selected["Code"] if selected else None

form = Form("ASSIGNMENT")
form.add_field("Department", prompt=select_dept)  # F4 shows list
result = form.show()

# Work-with list (action codes per row)
wwl = WorkWithList("WORK WITH ITEMS", ["ID", "Name", "Status"])
wwl.add_action("2", "Change")
wwl.add_action("4", "Delete")
wwl.add_action("5", "Display")
wwl.set_add_callback(add_new_item)  # F6=Add
wwl.add_row(ID="001", Name="Item 1", Status="Active")
wwl.add_row(ID="002", Name="Item 2", Status="Inactive")
result = wwl.show()  # Returns [{"action": "2", "row": {...}}, ...]
for item in result or []:
    if item["action"] == "2":
        edit_item(item["row"]["ID"])

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

# Tabular entry (table with editable columns)
te = TabularEntry("PORTFOLIO UPDATE", panel_id="PORT01")
te.add_column("Ticker", width=8)
te.add_column("Name", width=20)
te.add_column("New Amount", width=12, editable=True, required=True)
te.add_column("Previous", width=12)
te.add_row(Ticker="AAPL", Name="Apple Inc", Previous="1,234.56")
te.add_row(Ticker="GOOGL", Name="Alphabet", Previous="5,678.90")
result = te.show()  # Tab between cells, Enter to submit

# Show a message
show_message("Operation completed", msg_type="success")
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
| All | F1 | Help |
| All | F3 | Cancel/Exit |
| Forms | Tab | Next field |
| Forms | Shift+Tab | Previous field |
| Forms | Enter | Submit |
| Forms | F4 | Prompt (show selection list) |
| Fields | Left/Right | Move cursor |
| Fields | Home/End | Start/end of field |
| Fields | Delete | Delete at cursor |
| Fields | Backspace | Delete before cursor |
| Fields | Insert | Toggle insert/overwrite mode |
| Fields | Ctrl+E | Erase to end of field |
| Menus | 1-9, A-Z | Select item |
| Tables/Lists | F7 | Page backward |
| Tables/Lists | F8 | Page forward |
| Tables | Enter | Return |
| Selection Lists | S | Select item |
| Work-with Lists | 1-9, A-Z | Enter action code |
| Work-with Lists | Enter | Process actions |
| Work-with Lists | F6 | Add new record |
| Tabular Entry | Tab | Next editable cell |
| Tabular Entry | Shift+Tab | Previous editable cell |
| Tabular Entry | Enter | Submit all values |

## Terminal Width

Tables and lists automatically adapt to terminal width:
- Uses actual terminal width (not hardcoded 80 columns)
- Short columns are preserved at natural width
- Long columns are truncated to fit available space
- Truncated content shows `>` indicator (e.g., "Very long tex>")

## IBM 3270 Colors

The library uses IBM 3270 color conventions:
- **Green**: Input fields
- **Turquoise**: Labels (protected fields)
- **White**: Titles, headers (intensified)
- **Red**: Error messages
- **Yellow**: Warnings

## Requirements

- Python 3.10+
- Unix-like system (Linux, macOS)
- Terminal with ANSI support

## License

MIT
