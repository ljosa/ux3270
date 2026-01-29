# Tabular Entry

![Tabular Entry Screenshot](../images/tabular.png)

Tabular entry displays a table where some columns are editable input fields. Use it for multi-row data entry scenarios like bulk updates.

## Basic Usage

```python
from ux3270.dialog import TabularEntry
from ux3270.panel import FieldType

te = TabularEntry("PORTFOLIO UPDATE", panel_id="PORT01")

# Static columns (display only)
te.add_column("Ticker", width=8)
te.add_column("Name", width=20)
te.add_column("Current", width=12)

# Editable column
te.add_column("New Amount", width=12, editable=True, required=True,
              field_type=FieldType.NUMERIC)

# Add rows
te.add_row(Ticker="AAPL", Name="Apple Inc", Current="1,234.56")
te.add_row(Ticker="GOOGL", Name="Alphabet", Current="5,678.90")

result = te.show()
if result:
    for row in result:
        print(f"{row['Ticker']}: {row['New Amount']}")
```

## Column Types

```python
# Static column (display only)
te.add_column("ID", width=10)

# Editable column
te.add_column("Quantity", width=8, editable=True)

# Required editable column (marked with *)
te.add_column("Amount", width=10, editable=True, required=True)

# Numeric input
te.add_column("Price", width=10, editable=True,
              field_type=FieldType.NUMERIC)
```

## Navigation

- **Tab** - Move to next editable cell
- **Shift+Tab** - Move to previous editable cell
- **F7/F8** - Page up/down for large datasets
- **Enter** - Submit all values

## Validation

Validation runs on Enter:

```python
def validate_quantity(value):
    return int(value) > 0

te.add_column("Qty", width=8, editable=True,
              validator=validate_quantity)
```

Error messages appear on the error line when validation fails.

## Return Value

Returns a list of dicts combining original data with edited values:

```python
result = te.show()
# result = [
#     {"Ticker": "AAPL", "Name": "Apple Inc", "Current": "1,234.56", "New Amount": "2000"},
#     {"Ticker": "GOOGL", "Name": "Alphabet", "Current": "5,678.90", "New Amount": "3000"},
# ]
```

Returns `None` if cancelled (F3).

## API Reference

::: ux3270.dialog.TabularEntry
    options:
      members:
        - __init__
        - add_column
        - add_row
        - show
