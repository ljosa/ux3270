# Menu

![Menu Screenshot](../images/menu.png)

Menus display a list of options with single-key selection. Press a key to immediately execute the associated action.

## Basic Usage

```python
from ux3270.dialog import Menu

def handle_reports():
    print("Running reports...")

def handle_settings():
    print("Opening settings...")

menu = Menu("MAIN MENU", panel_id="MENU01")
menu.add_item("1", "Reports", handle_reports)
menu.add_item("2", "Settings", handle_settings)
menu.add_item("3", "Help", lambda: print("Help"))
menu.run()  # Loops until user exits
```

## Single Show vs Run Loop

- `menu.show()` - Display once, return selected key or None
- `menu.run()` - Loop until user presses F3 or X to exit

```python
# Single display
key = menu.show()
if key == "1":
    print("User selected option 1")

# Or loop
menu.run()  # Automatically loops
```

## Exit Keys

- **F3** - Exit the menu
- **X** - Also exits the menu

## API Reference

::: ux3270.dialog.Menu
    options:
      members:
        - __init__
        - add_item
        - show
        - run
