#!/usr/bin/env python3
"""
Screenshot demonstration of ux3270 UI.
This script creates a visual representation of what the UI looks like.
"""

import sys
sys.path.insert(0, '.')

def print_demo_screen():
    """Print a static representation of the UI."""
    
    # Clear screen
    print("\033[2J\033[H", end="")
    
    # Demo 1: Menu
    print("\033[1;1H")
    print("╔════════════════════════════════════════════════╗")
    print("║ \033[1mINVENTORY MANAGEMENT SYSTEM\033[0m               ║")
    print("╚════════════════════════════════════════════════╝")
    print()
    print("  \033[1m1\033[0m - Add New Item")
    print("  \033[1m2\033[0m - View All Items")
    print("  \033[1m3\033[0m - Search Items")
    print("  \033[1m4\033[0m - Update Item")
    print("  \033[1m5\033[0m - Delete Item")
    print("  \033[1m6\033[0m - Adjust Quantity")
    print()
    print("\033[2mPress a key to select an option, or X to exit\033[0m")
    print()
    print()
    
    # Demo 2: Form
    print("─" * 60)
    print("\033[1m═══ ADD NEW ITEM ═══\033[0m")
    print()
    print("  SKU: WIDGET001______________")
    print()
    print("  Name: Super Widget Pro_____________________________")
    print()
    print("  Description: High-quality widget for professional use________________")
    print()
    print("  Quantity: 100_______")
    print()
    print("  Unit Price: 29.99_______")
    print()
    print("  Location: Warehouse A - Shelf 3_______")
    print()
    print()
    print("\033[2mTab: Next field | Shift+Tab: Previous | Enter: Submit | Ctrl+C: Cancel\033[0m")
    print()
    print()
    
    # Demo 3: Table
    print("─" * 60)
    print("╔═══════════════════════╗")
    print("║ \033[1mINVENTORY LIST\033[0m      ║")
    print("╚═══════════════════════╝")
    print()
    print("  \033[1mID\033[0m  │ \033[1mSKU\033[0m         │ \033[1mName\033[0m                    │ \033[1mQty\033[0m │ \033[1mPrice\033[0m   │ \033[1mLocation\033[0m")
    print("  ────┼─────────────┼──────────────────────────┼─────┼─────────┼────────────────────")
    print("  1   │ WIDGET001   │ Super Widget Pro         │ 100 │ $29.99  │ Warehouse A - She")
    print("  2   │ GADGET042   │ Premium Gadget           │ 50  │ $49.99  │ Warehouse B - She")
    print("  3   │ TOOL123     │ Professional Tool Set    │ 25  │ $199.99 │ Warehouse A - She")
    print("  4   │ PART567     │ Replacement Part Kit     │ 200 │ $9.99   │ Warehouse C - Bin")
    print("  5   │ DEVICE999   │ Electronic Device        │ 10  │ $299.99 │ Secure Storage")
    print()
    print("\033[2mTotal: 5 rows\033[0m")
    print()
    print("\033[2mPress any key to continue...\033[0m")
    print()


if __name__ == "__main__":
    print_demo_screen()
    print("\n\nThis is a static demonstration of the ux3270 UI.")
    print("In actual use, the interface is fully interactive with:")
    print("  • Tab navigation between fields")
    print("  • Character-by-character input")
    print("  • Real-time field validation")
    print("  • Password masking")
    print("  • Single-key menu selection")
    print("\nSee USAGE.md for detailed documentation.")
