# ux3270 Usage Guide

## Quick Start

### Installation

```bash
pip install -e .
```

### Running the Inventory Management System

```bash
# Using the installed command
inventory-app

# Or run directly
cd inventory_app
python main.py
```

## Library Components

### 1. ux3270 - Core Library

The core library provides the fundamental building blocks for IBM 3270-style applications.

#### Basic Screen Example

```python
from ux3270 import Screen, Field, FieldType

# Create a screen
screen = Screen("LOGIN")

# Add fields
screen.add_field(Field(
    row=2,
    col=15,
    length=20,
    label="Username",
    required=True
))

screen.add_field(Field(
    row=4,
    col=15,
    length=20,
    label="Password",
    field_type=FieldType.PASSWORD,
    required=True
))

# Show the screen and get user input
result = screen.show()
print(f"Username: {result['Username']}")
print(f"Password: {result['Password']}")
```

#### Field Types

- `FieldType.TEXT` - Standard text input (default)
- `FieldType.PASSWORD` - Masked password input (displays asterisks)
- `FieldType.NUMERIC` - Only accepts numeric input
- `FieldType.READONLY` - Display-only, cannot be edited

#### Field Validation

```python
def validate_email(value):
    return '@' in value

field = Field(
    row=2,
    col=15,
    length=40,
    label="Email",
    required=True,
    validator=validate_email
)
```

### 2. ux3270_ui - High-Level UI Library

Provides convenient abstractions for common UI patterns.

#### Menu Example

```python
from ux3270_ui import Menu

def option1():
    print("Option 1 selected")

def option2():
    print("Option 2 selected")

menu = Menu("MAIN MENU")
menu.add_item("1", "First Option", option1)
menu.add_item("2", "Second Option", option2)
menu.run()  # Runs until user exits with 'X'
```

#### Form Example

```python
from ux3270_ui import Form
from ux3270 import FieldType

form = Form("CUSTOMER INFO")
form.add_text("Please enter customer details:")
form.add_field("Name", length=40, required=True)
form.add_field("Email", length=50)
form.add_field("Age", length=3, field_type=FieldType.NUMERIC)

result = form.show()
# result is a dictionary: {"Name": "...", "Email": "...", "Age": "..."}
```

#### Table Example

```python
from ux3270_ui import Table

table = Table("SALES REPORT", ["ID", "Product", "Quantity", "Total"])
table.add_row("001", "Widget A", "50", "$500.00")
table.add_row("002", "Widget B", "30", "$450.00")
table.add_row("003", "Widget C", "75", "$750.00")

table.show()  # Displays table and waits for keypress
```

## Inventory Management System

The inventory system demonstrates all library features in a complete application.

### Features

1. **Add New Item** - Create inventory items with SKU, name, description, quantity, price, and location
2. **View All Items** - Display all inventory in a table
3. **Search Items** - Search by SKU, name, or description
4. **Update Item** - Modify existing items
5. **Delete Item** - Remove items with confirmation
6. **Adjust Quantity** - Quickly update stock levels

### Database Schema

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    unit_price REAL NOT NULL DEFAULT 0.0,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Using the Database API

```python
from inventory_app.database import InventoryDB

# Create database connection
db = InventoryDB("inventory.db")

# Add an item
item_id = db.add_item(
    sku="WIDGET001",
    name="Super Widget",
    description="A premium widget",
    quantity=100,
    unit_price=29.99,
    location="Warehouse A, Shelf 3"
)

# Get an item
item = db.get_item(item_id)
print(f"Item: {item['name']}, Qty: {item['quantity']}")

# Search items
results = db.search_items("Widget")
for item in results:
    print(f"{item['sku']}: {item['name']}")

# Update quantity
db.update_item(item_id, quantity=150)

# Delete item
db.delete_item(item_id)

# Close connection
db.close()
```

## Keyboard Controls

### In Forms/Screens

- **Tab** - Move to next field
- **Shift+Tab** - Move to previous field
- **Enter** - Submit form
- **Backspace** - Delete character
- **Ctrl+C** - Cancel and exit

### In Menus

- **Number/Letter Key** - Select menu item
- **X** - Exit menu
- **Ctrl+C** - Exit application

### In Tables

- **Any Key** - Close table and continue

## Design Philosophy

The library follows the IBM 3270 terminal model:

1. **Block-Oriented**: Complete screens are created before display
2. **Form Submission**: User fills entire form before submission
3. **Field Protection**: Some fields can be read-only
4. **Structured Navigation**: Tab between fields in order
5. **Visual Clarity**: Clear borders, labels, and status messages

## Advanced Examples

### Multi-Step Workflow

```python
from ux3270_ui import Form, Menu
from ux3270 import FieldType

def customer_workflow():
    # Step 1: Get customer info
    form1 = Form("NEW CUSTOMER - STEP 1")
    form1.add_field("Name", length=40, required=True)
    form1.add_field("Email", length=50, required=True)
    customer = form1.show()
    
    # Step 2: Get address
    form2 = Form("NEW CUSTOMER - STEP 2")
    form2.add_field("Street", length=60, required=True)
    form2.add_field("City", length=30, required=True)
    form2.add_field("ZIP", length=10, required=True)
    address = form2.show()
    
    # Combine results
    return {**customer, **address}

# Use in a menu
menu = Menu("CRM SYSTEM")
menu.add_item("1", "Add Customer", customer_workflow)
menu.run()
```

### Custom Validation

```python
from ux3270_ui import Form

def validate_age(value):
    try:
        age = int(value)
        return 0 <= age <= 150
    except:
        return False

def validate_email(value):
    return '@' in value and '.' in value

form = Form("REGISTRATION")
form.add_field("Email", length=50, required=True, validator=validate_email)
form.add_field("Age", length=3, required=True, validator=validate_age)

result = form.show()
```

## Tips and Best Practices

1. **Field Length**: Set realistic field lengths based on expected content
2. **Required Fields**: Mark important fields as required for better UX
3. **Field Labels**: Use clear, concise labels
4. **Validation**: Add validators for fields with specific formats
5. **Read-Only Fields**: Use for display of computed values or IDs
6. **Error Messages**: The library automatically shows validation errors
7. **Menu Organization**: Group related functions logically
8. **Table Columns**: Keep column count reasonable for terminal width

## Troubleshooting

### Terminal Issues

If you see garbled output or the screen doesn't clear properly:
- Ensure you're running in a real terminal (not a file redirect)
- Your terminal must support ANSI escape sequences
- Try `reset` command if terminal state is corrupted

### Import Errors

If you get import errors:
- Make sure you've installed the package: `pip install -e .`
- Check that you're in the correct directory
- Verify Python version is 3.8 or higher

### Database Locked

If you get "database is locked" errors:
- Close any other connections to the database
- Check that the database file has proper permissions
- Only one InventoryDB instance should access a file at once
