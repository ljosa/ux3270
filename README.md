# ux3270

IBM 3270-like terminal application library for Python.

## Overview

This project provides a Python library for creating terminal applications that use an IBM 3270-like interaction model. The application creates a form or screen, hands off control to the user to interact with it, and continues after the user submits the form.

## Components

### 1. ux3270 - Core Terminal Library

The core library provides low-level components for building IBM 3270-style terminal applications:

- **Screen**: Manages a terminal screen with fields and text
- **Field**: Represents input fields with various types (text, password, numeric, readonly)
- **FieldType**: Enumeration of field types

Example:
```python
from ux3270 import Screen, Field, FieldType

screen = Screen("LOGIN")
screen.add_field(Field(row=2, col=15, length=20, label="Username", required=True))
screen.add_field(Field(row=4, col=15, length=20, label="Password", 
                       field_type=FieldType.PASSWORD, required=True))

result = screen.show()  # Hands control to user, returns when submitted
print(f"Logged in as: {result['Username']}")
```

### 2. ux3270_ui - High-Level UI Library

Provides common UI patterns and IBM 3270-style visual elements:

- **Menu**: Single-key selection menus with IBM 3270 styling
- **Form**: High-level form builder with automatic layout
- **Table**: Tabular data display with column headers

Example:
```python
from ux3270_ui import Menu, Form, Table

# Create a menu
menu = Menu("MAIN MENU")
menu.add_item("1", "Option 1", lambda: print("Selected 1"))
menu.add_item("2", "Option 2", lambda: print("Selected 2"))
menu.run()

# Create a form
form = Form("DATA ENTRY")
form.add_field("Name", length=30, required=True)
form.add_field("Email", length=40)
result = form.show()

# Display a table
table = Table("RESULTS", ["ID", "Name", "Status"])
table.add_row("001", "Item 1", "Active")
table.add_row("002", "Item 2", "Inactive")
table.show()
```

### 3. Inventory Management System

A complete inventory management application demonstrating the libraries:

- SQLite database backend
- Full CRUD operations (Create, Read, Update, Delete)
- Item search functionality
- Quantity adjustment
- IBM 3270-style user interface

## Installation

Install from source:

```bash
pip install -e .
```

## Running the Inventory App

After installation, run the inventory management system:

```bash
inventory-app
```

Or run directly with Python:

```bash
cd inventory_app
python main.py
```

## Features

- **IBM 3270-like Interaction Model**: Forms are displayed, control is handed to the user, and the application continues after submission
- **Field Validation**: Required fields, type validation (numeric, text, password)
- **Keyboard Navigation**: Tab/Shift+Tab to move between fields, Enter to submit
- **Visual Styling**: IBM 3270-inspired borders, formatting, and layout
- **Database Integration**: SQLite backend for data persistence

## Requirements

- Python 3.8 or higher
- Unix-like system (Linux, macOS) with terminal support

## License

MIT License

## IBM 3270 Background

The IBM 3270 was a family of block-oriented computer terminals introduced by IBM in 1971. Unlike character-oriented terminals, 3270 terminals:

1. Display complete screens/forms at once
2. Allow users to fill in multiple fields
3. Submit the entire form when complete
4. Support protected vs unprotected fields
5. Use function keys for specific actions

This library recreates this interaction pattern for modern terminal applications.