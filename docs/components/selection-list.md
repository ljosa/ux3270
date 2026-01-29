# Selection List

![Selection List Screenshot](../images/selection.png)

Selection lists allow users to pick one item from a list. Type 'S' next to an item and press Enter to select it. This is commonly used for F4=Prompt functionality.

## Basic Usage

```python
from ux3270.dialog import SelectionList

sel = SelectionList("SELECT DEPARTMENT", panel_id="SEL01")
sel.add_column("Code")
sel.add_column("Name")

sel.add_row(Code="ENG", Name="Engineering")
sel.add_row(Code="SAL", Name="Sales")
sel.add_row(Code="MKT", Name="Marketing")

selected = sel.show()
if selected:
    print(f"Selected: {selected['Code']}")
```

## Using with Form Prompts

Selection lists work well as F4 prompts in forms:

```python
from ux3270.dialog import Form, SelectionList

def select_department():
    sel = SelectionList("SELECT DEPARTMENT")
    sel.add_column("Code")
    sel.add_column("Name")
    for dept in db.get_departments():
        sel.add_row(**dept)
    selected = sel.show()
    return selected["Code"] if selected else None

form = Form("EMPLOYEE FORM")
form.add_field("Name", length=30)
form.add_field("Department", length=10, prompt=select_department)
```

## F6=Add Callback

Allow adding new items from the selection list:

```python
def add_department():
    form = Form("ADD DEPARTMENT")
    form.add_field("Code", length=5, required=True)
    form.add_field("Name", length=30, required=True)
    result = form.show()
    if result:
        db.insert_department(result)
        return result  # Return as selected item
    return None

sel.set_add_callback(add_department)
```

## Bulk Loading

Load multiple rows at once:

```python
departments = [
    {"Code": "ENG", "Name": "Engineering"},
    {"Code": "SAL", "Name": "Sales"},
]
sel.add_rows(departments)
```

## API Reference

::: ux3270.dialog.SelectionList
    options:
      members:
        - __init__
        - add_column
        - add_row
        - add_rows
        - set_add_callback
        - show
