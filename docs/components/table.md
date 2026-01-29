# Table

![Table Screenshot](../images/table.png)

Tables display read-only tabular data with pagination. Use F7/F8 to page through large datasets.

## Basic Usage

```python
from ux3270.dialog import Table

table = Table("INVENTORY LIST", panel_id="INV01")
table.add_column("ID")
table.add_column("Name")
table.add_column("Qty", align="right")
table.add_column("Status")

table.add_row("001", "Widget A", "100", "Active")
table.add_row("002", "Widget B", "50", "Active")
table.add_row("003", "Gadget C", "0", "Out of Stock")

table.show()
```

## Column Alignment

```python
table.add_column("Amount", align="right")  # Right-align numbers
table.add_column("Name", align="left")     # Left-align text (default)
```

## Column Width

By default, columns auto-size to fit content. You can specify a fixed width:

```python
table.add_column("Description", width=30)
```

## Header Fields

Add input fields above the table for filtering or positioning:

```python
table.add_header_field("Position to", length=20)
result = table.show()
position = result["Position to"] if result else ""
```

## Pagination

Tables automatically paginate based on terminal height:

- **F7** or **Page Up** - Previous page
- **F8** or **Page Down** - Next page

The row count message shows current position: `ROW 1 TO 10 OF 50`

## Auto-Truncation

If content is too wide for the terminal, long columns are automatically truncated with a `>` indicator:

```
ID    Name              Description
---   ---------------   ---------------------------
001   Widget A          This is a very long descrip>
002   Widget B          Short desc
```

## API Reference

::: ux3270.dialog.Table
    options:
      members:
        - __init__
        - add_column
        - add_row
        - add_header_field
        - get_header_values
        - show
