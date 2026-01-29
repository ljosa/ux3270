# Message Panel

![Message Panel Screenshot](../images/message.png)

Message panels display information to the user and wait for acknowledgment. Use them for confirmations, errors, and status messages.

## Basic Usage

```python
from ux3270.dialog import show_message

# Simple message
show_message("Operation completed successfully")

# With type
show_message("Record saved", msg_type="success")
show_message("Invalid input", msg_type="error")
show_message("Are you sure?", msg_type="warning")
```

## Message Types

| Type | Color | Usage |
|------|-------|-------|
| `info` | Turquoise | General information (default) |
| `success` | Green | Successful operations |
| `error` | Red | Error messages |
| `warning` | Yellow | Warnings |

## With Title and Panel ID

```python
show_message(
    "The record has been deleted",
    msg_type="success",
    title="DELETE COMPLETE",
    panel_id="MSG01"
)
```

## Using MessagePanel Class

For more control, use the class directly:

```python
from ux3270.dialog import MessagePanel

panel = MessagePanel(
    message="Are you sure you want to delete this record?",
    msg_type="warning",
    title="CONFIRM DELETE"
)
panel.show()
```

## API Reference

::: ux3270.dialog.show_message

::: ux3270.dialog.MessagePanel
    options:
      members:
        - __init__
        - show
