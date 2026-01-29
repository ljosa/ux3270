# ux3270

IBM 3270-style terminal UI library for Python.

## Overview

Create terminal applications with an IBM 3270-style interaction model: display a form, let the user fill it in, continue when they submit.

The library provides high-level dialog components (Form, Menu, Table, etc.) that follow IBM CUA (Common User Access) conventions, built on a low-level Screen API that handles terminal rendering and input.

## Features

- **Forms** with field validation, help text, and F4 prompt lookups
- **Menus** with single-key selection
- **Tables** with pagination and column alignment
- **Work-with Lists** with action codes per row (AS/400-style)
- **Selection Lists** for F4 prompt functionality
- **Tabular Entry** for multi-row data entry
- **Message Panels** for user feedback

![Menu Screenshot](images/menu.png)

## Quick Example

```python
from ux3270.dialog import Form, Menu, show_message

# Create a form
form = Form("DATA ENTRY", help_text="Enter your information")
form.add_field("Name", length=30, required=True)
form.add_field("Email", length=40)
result = form.show()

if result:
    show_message(f"Hello, {result['Name']}!", msg_type="success")
```

## Installation

```bash
uv add git+https://github.com/ljosa/ux3270.git
```

## IBM 3270 Colors

The library uses authentic IBM 3270 color conventions:

| Color | Usage |
|-------|-------|
| Green | Input fields |
| Turquoise | Labels (protected fields) |
| White | Titles, headers (intensified) |
| Red | Error messages |
| Yellow | Warnings |

## Terminal Width

Tables and lists automatically adapt to terminal width:

- Uses actual terminal width (not hardcoded 80 columns)
- Short columns are preserved at natural width
- Long columns are truncated to fit available space
- Truncated content shows `>` indicator (e.g., "Very long tex>")
