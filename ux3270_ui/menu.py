"""Menu UI component for IBM 3270-style applications."""

import sys
import tty
import termios
from typing import List, Callable, Optional


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
    """
    
    def __init__(self, title: str = "MAIN MENU"):
        """
        Initialize a menu.
        
        Args:
            title: Menu title
        """
        self.title = title
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
        
    def clear(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)
        
    def render(self):
        """Render the menu."""
        self.clear()
        
        # Display title with IBM 3270-style border
        print("╔" + "═" * (len(self.title) + 2) + "╗")
        print(f"║ \033[1m{self.title}\033[0m ║")
        print("╚" + "═" * (len(self.title) + 2) + "╝")
        print()
        
        # Display menu items
        for item in self.items:
            print(f"  \033[1m{item.key}\033[0m - {item.label}")
            
        print()
        print("\033[2mPress a key to select an option, or X to exit\033[0m")
        
    def show(self) -> Optional[str]:
        """
        Display the menu and wait for user selection.
        
        Returns:
            Selected key, or None if user exits
        """
        self.render()
        
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Set raw mode for single character input
            tty.setraw(fd)
            
            while True:
                ch = sys.stdin.read(1).upper()
                
                if ch == 'X' or ch == '\x03':  # X or Ctrl+C
                    return None
                    
                # Find matching menu item
                for item in self.items:
                    if item.key.upper() == ch:
                        self.clear()
                        item.action()
                        return ch
                        
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    def run(self):
        """Run the menu in a loop until user exits."""
        try:
            while True:
                result = self.show()
                if result is None:
                    self.clear()
                    print("Goodbye!")
                    break
        except KeyboardInterrupt:
            self.clear()
            print("\nGoodbye!")
