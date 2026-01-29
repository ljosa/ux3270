# Form

![Form Screenshot](../images/form.png)

Forms display input fields and collect user data. They follow IBM CUA conventions with panel IDs, titles, and function key hints.

## Basic Usage

```python
from ux3270.dialog import Form
from ux3270.panel import FieldType

form = Form("DATA ENTRY", panel_id="FORM01", instruction="Enter data below")
form.add_field("Name", length=30, required=True)
form.add_field("Email", length=40)
form.add_field("Age", length=3, field_type=FieldType.NUMERIC)

result = form.show()
if result:
    print(f"Name: {result['Name']}")
```

## Field Types

| Type | Description |
|------|-------------|
| `FieldType.TEXT` | Standard text input (default) |
| `FieldType.NUMERIC` | Numbers only |
| `FieldType.PASSWORD` | Hidden input (shows asterisks) |
| `FieldType.READONLY` | Display only, not editable |

## Help Text

Forms support F1 help at both panel and field level:

```python
form = Form("HELP DEMO", help_text="This is panel-level help")
form.add_field("Username", help_text="Enter your login ID")
form.add_field("Department", help_text="Your department code")
```

Press F1 to display help. If the cursor is on a field with help text, that field's help is shown.

## F4 Prompt

Fields can have a prompt callback for selection lists:

```python
from ux3270.dialog import Form, SelectionList

def select_department():
    sel = SelectionList("SELECT DEPARTMENT")
    sel.add_column("Code")
    sel.add_column("Name")
    sel.add_row(Code="ENG", Name="Engineering")
    sel.add_row(Code="SAL", Name="Sales")
    selected = sel.show()
    return selected["Code"] if selected else None

form = Form("ASSIGNMENT")
form.add_field("Department", length=10, prompt=select_department)
result = form.show()
```

Press F4 when on a field with a prompt to show the selection list.

## Validation

```python
def validate_email(value):
    return "@" in value

form.add_field("Email", validator=validate_email)
```

## API Reference

::: ux3270.dialog.Form
    options:
      members:
        - __init__
        - add_field
        - add_text
        - show
