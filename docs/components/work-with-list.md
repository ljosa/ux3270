# Work-with List

![Work-with List Screenshot](../images/worklist.png)

Work-with lists display data with an action input field per row. Users type action codes (2=Change, 4=Delete, etc.) and press Enter to process actions. This is the classic AS/400 interaction pattern.

## Basic Usage

```python
from ux3270.dialog import WorkWithList

wwl = WorkWithList("WORK WITH INVENTORY", panel_id="INV01")
wwl.add_column("ID")
wwl.add_column("Name")
wwl.add_column("Qty", align="right")

# Define available actions
wwl.add_action("2", "Change")
wwl.add_action("4", "Delete")
wwl.add_action("5", "Display")

# Add data rows
wwl.add_row(ID="001", Name="Widget A", Qty="100")
wwl.add_row(ID="002", Name="Widget B", Qty="50")

result = wwl.show()
```

## Processing Actions

The `show()` method returns a list of actions:

```python
result = wwl.show()

if result is None:
    print("Cancelled")
elif not result:
    print("No actions selected")
else:
    for item in result:
        action = item["action"]  # "2", "4", "5", etc.
        row = item["row"]        # The row data dict

        if action == "2":
            edit_item(row["ID"])
        elif action == "4":
            delete_item(row["ID"])
        elif action == "5":
            display_item(row["ID"])
```

## F6=Add Callback

Add a callback to handle F6=Add:

```python
def add_new_item():
    form = Form("ADD ITEM")
    form.add_field("Name", required=True)
    form.add_field("Qty", field_type=FieldType.NUMERIC)
    result = form.show()
    if result:
        # Save to database
        db.insert(result)

wwl.set_add_callback(add_new_item)
```

## Header Fields

Add filter fields above the list:

```python
wwl.add_header_field("Position to", length=20)
wwl.add_header_field("Status", length=10, default="Active")

result = wwl.show()
# Access header values
header_values = wwl.get_header_values()
```

## Typical Application Pattern

```python
while True:
    # Reload data
    wwl.rows.clear()
    for item in db.get_all():
        wwl.add_row(**item)

    result = wwl.show()

    if result is None:
        break  # User pressed F3

    for action in result:
        if action["action"] == "2":
            edit_item(action["row"]["ID"])
        elif action["action"] == "4":
            if confirm_delete():
                delete_item(action["row"]["ID"])
```

## API Reference

::: ux3270.dialog.WorkWithList
    options:
      members:
        - __init__
        - add_column
        - add_row
        - add_action
        - add_header_field
        - set_add_callback
        - get_header_values
        - show
