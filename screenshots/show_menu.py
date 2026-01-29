#!/usr/bin/env python3
"""Display a menu for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import Menu

menu = Menu("MAIN MENU", panel_id="MENU01", instruction="Select an option")
menu.add_item("1", "Work with Inventory", lambda: None)
menu.add_item("2", "Reports", lambda: None)
menu.add_item("3", "System Configuration", lambda: None)
menu.add_item("4", "User Management", lambda: None)
menu.show()
