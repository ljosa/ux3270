"""Menu UI component for IBM 3270-style applications."""

from typing import List, Callable, Optional

from ux3270.panel import Screen, Colors


class MenuItem:
    """Represents a menu item."""

    def __init__(self, key: str, label: str, action: Callable):
        """
        Initialize a menu item.

        Args:
            key: Single character key to select this item
            label: Display label for the menu item
            action: Function to call when item is selected
        """
        self.key = key
        self.label = label
        self.action = action


class Menu:
    """
    IBM 3270-style menu screen.

    Displays a list of options with single-key selection.
    Follows IBM CUA (Common User Access) conventions:
    - Panel ID at top-left, title centered
    - Instruction line below title
    - Menu items in body area
    - Function keys at bottom

    The dialog builds a Screen definition and hands control to Screen
    for all rendering and input handling.
    """

    # CUA layout constants
    TITLE_ROW = 0
    INSTRUCTION_ROW = 1
    ITEMS_START_ROW = 3

    def __init__(self, title: str = "MAIN MENU", panel_id: str = "",
                 instruction: str = "Select an option"):
        """
        Initialize a menu.

        Args:
            title: Menu title (displayed in uppercase per IBM convention)
            panel_id: Optional panel identifier (shown at top-left per CUA)
            instruction: Instruction text (shown on row 2 per CUA)
        """
        self.title = title.upper()
        self.panel_id = panel_id.upper() if panel_id else ""
        self.instruction = instruction
        self.items: List[MenuItem] = []

    def add_item(self, key: str, label: str, action: Callable) -> "Menu":
        """
        Add a menu item.

        Args:
            key: Single character key to select this item
            label: Display label
            action: Function to call when selected

        Returns:
            Self for method chaining
        """
        self.items.append(MenuItem(key, label, action))
        return self

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        try:
            import os
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80

    def _build_screen(self, height: int, width: int) -> Screen:
        """Build a Screen with the menu display."""
        screen = Screen()
        screen.set_any_key_mode(True)  # Return on single key press

        # Row 0: Panel ID and Title
        if self.panel_id:
            screen.add_text(self.TITLE_ROW, 0, self.panel_id, Colors.PROTECTED)
        if self.title:
            title_col = max(0, (width - len(self.title)) // 2)
            screen.add_text(self.TITLE_ROW, title_col, self.title, Colors.INTENSIFIED)

        # Row 1: Instruction line
        if self.instruction:
            screen.add_text(self.INSTRUCTION_ROW, 0, self.instruction, Colors.PROTECTED)

        # Menu items starting at row 3
        for i, item in enumerate(self.items):
            # Format: "1 - Label"
            item_text = f"{item.key} - {item.label}"
            screen.add_text(self.ITEMS_START_ROW + i, 2, item.key, Colors.INTENSIFIED)
            screen.add_text(self.ITEMS_START_ROW + i, 4, f"- {item.label}", Colors.PROTECTED)

        # Separator (height-2)
        screen.add_text(height - 2, 0, "-" * width, Colors.DIM)

        # Function keys (height-1)
        screen.add_text(height - 1, 0, "F3=Exit", Colors.PROTECTED)

        return screen

    def show(self) -> Optional[str]:
        """
        Display the menu and wait for user selection.

        Returns:
            Selected key, or None if user exits (F3 or X)
        """
        height, width = self._get_terminal_size()
        screen = self._build_screen(height, width)
        result = screen.show()

        if result is None:
            return None

        # F3 or X = Exit
        if result["aid"] == "F3":
            return None

        # Check if a key was pressed
        if result["aid"] == "KEY":
            key = result.get("key", "")

            # X also exits
            if key.upper() == "X":
                return None

            # Find matching menu item
            for item in self.items:
                if item.key.upper() == key.upper():
                    item.action()
                    return key

        return None

    def run(self):
        """Run the menu in a loop until user exits."""
        try:
            while True:
                result = self.show()
                if result is None:
                    break
        except KeyboardInterrupt:
            pass
