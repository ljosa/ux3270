# Getting Started

## Installation

Install ux3270 as a dependency in your project:

```bash
uv add git+https://github.com/ljosa/ux3270.git
```

Or for development:

```bash
git clone https://github.com/ljosa/ux3270.git
cd ux3270
uv venv && uv pip install -e .
```

## Your First Form

```python
from ux3270.dialog import Form

# Create a simple form
form = Form("USER LOGIN", panel_id="LOGIN01")
form.add_field("Username", length=20, required=True)
form.add_field("Password", length=20, field_type=FieldType.PASSWORD, required=True)

# Show the form and get results
result = form.show()

if result is None:
    print("User cancelled")
else:
    print(f"Username: {result['Username']}")
```

## Your First Menu

```python
from ux3270.dialog import Menu

def option_one():
    print("You selected option 1")

def option_two():
    print("You selected option 2")

menu = Menu("MAIN MENU", panel_id="MENU01")
menu.add_item("1", "First Option", option_one)
menu.add_item("2", "Second Option", option_two)
menu.run()  # Loops until F3 or X
```

## Running the Demo

The library includes a demo application:

```bash
# Run the inventory demo with sample data
inventory-app --demo

# Or run the simple demo
python examples/demo.py
```

## Architecture

ux3270 has two layers:

1. **Dialog Layer** (`ux3270.dialog`) - High-level components like Form, Menu, Table
2. **Panel Layer** (`ux3270.panel`) - Low-level Screen API for terminal rendering

Most applications only need the dialog layer. The panel layer is available for custom components.
