#!/usr/bin/env python3
"""Inventory Management System using IBM 3270-like UI."""

import argparse
import random

from ux3270.panel import FieldType, Colors
from ux3270.dialog import Menu, Form, Table
from .database import InventoryDB


# Sample data for demo purposes
SAMPLE_DATA = [
    # Electronics
    ("ELEC-001", "Wireless Mouse", "Ergonomic wireless mouse, 2.4GHz", 45, 29.99, "Warehouse A-1"),
    ("ELEC-002", "USB-C Hub", "7-port USB-C hub with HDMI", 32, 49.99, "Warehouse A-1"),
    ("ELEC-003", "Mechanical Keyboard", "RGB mechanical keyboard, blue switches", 18, 89.99, "Warehouse A-2"),
    ("ELEC-004", "Webcam HD", "1080p HD webcam with microphone", 67, 59.99, "Warehouse A-2"),
    ("ELEC-005", "Monitor Stand", "Adjustable monitor stand, dual arm", 23, 79.99, "Warehouse A-3"),
    ("ELEC-006", "Power Strip", "6-outlet surge protector", 120, 19.99, "Warehouse B-1"),
    ("ELEC-007", "HDMI Cable 6ft", "High-speed HDMI 2.1 cable", 200, 12.99, "Warehouse B-1"),
    ("ELEC-008", "Laptop Stand", "Aluminum laptop stand, foldable", 55, 34.99, "Warehouse A-3"),
    # Office Supplies
    ("OFFC-001", "Stapler", "Heavy-duty desktop stapler", 89, 15.99, "Warehouse C-1"),
    ("OFFC-002", "Paper Clips Box", "Box of 1000 paper clips", 150, 4.99, "Warehouse C-1"),
    ("OFFC-003", "Sticky Notes", "3x3 inch sticky notes, 12 pack", 200, 8.99, "Warehouse C-1"),
    ("OFFC-004", "Ballpoint Pens", "Blue ballpoint pens, 24 pack", 175, 11.99, "Warehouse C-2"),
    ("OFFC-005", "Notebook A4", "Spiral notebook, 100 pages", 300, 3.99, "Warehouse C-2"),
    ("OFFC-006", "File Folders", "Manila file folders, 50 pack", 80, 14.99, "Warehouse C-3"),
    ("OFFC-007", "Desk Organizer", "Mesh desk organizer, 5 compartments", 42, 24.99, "Warehouse C-3"),
    ("OFFC-008", "Whiteboard Markers", "Dry erase markers, 8 colors", 95, 9.99, "Warehouse C-2"),
    # Furniture
    ("FURN-001", "Office Chair", "Ergonomic office chair, lumbar support", 15, 249.99, "Warehouse D-1"),
    ("FURN-002", "Standing Desk", "Electric standing desk, 60 inch", 8, 449.99, "Warehouse D-1"),
    ("FURN-003", "Bookshelf", "5-tier bookshelf, walnut finish", 12, 129.99, "Warehouse D-2"),
    ("FURN-004", "Filing Cabinet", "3-drawer filing cabinet, lockable", 20, 179.99, "Warehouse D-2"),
    ("FURN-005", "Desk Lamp", "LED desk lamp, adjustable brightness", 65, 39.99, "Warehouse D-3"),
    # Breakroom
    ("BRKR-001", "Coffee Maker", "12-cup programmable coffee maker", 10, 79.99, "Warehouse E-1"),
    ("BRKR-002", "Paper Cups", "Disposable cups, 500 count", 40, 24.99, "Warehouse E-1"),
    ("BRKR-003", "Water Cooler", "Bottom-loading water cooler", 5, 199.99, "Warehouse E-2"),
    ("BRKR-004", "Microwave", "Countertop microwave, 1100W", 8, 89.99, "Warehouse E-2"),
    ("BRKR-005", "Mini Fridge", "Compact refrigerator, 3.2 cu ft", 6, 149.99, "Warehouse E-2"),
    # Safety
    ("SAFE-001", "First Aid Kit", "100-piece first aid kit", 25, 29.99, "Warehouse F-1"),
    ("SAFE-002", "Fire Extinguisher", "ABC fire extinguisher, 5 lb", 30, 49.99, "Warehouse F-1"),
    ("SAFE-003", "Safety Glasses", "Clear safety glasses, 12 pack", 60, 34.99, "Warehouse F-2"),
    ("SAFE-004", "Hard Hat", "OSHA-compliant hard hat, white", 40, 19.99, "Warehouse F-2"),
    ("SAFE-005", "Safety Vest", "High-visibility safety vest", 75, 12.99, "Warehouse F-2"),
]


class InventoryApp:
    """Main inventory management application."""

    def __init__(self, db_path: str = "inventory.db"):
        """
        Initialize the application.

        Args:
            db_path: Path to SQLite database
        """
        self.db = InventoryDB(db_path)

    def run(self):
        """Run the main application loop."""
        menu = Menu("INVENTORY MANAGEMENT SYSTEM")
        menu.add_item("1", "Add New Item", self.add_item)
        menu.add_item("2", "View All Items", self.view_items)
        menu.add_item("3", "Search Items", self.search_items)
        menu.add_item("4", "Update Item", self.update_item)
        menu.add_item("5", "Delete Item", self.delete_item)
        menu.add_item("6", "Adjust Quantity", self.adjust_quantity)

        menu.run()
        self.db.close()

    def _get_terminal_size(self) -> tuple:
        """Get terminal dimensions."""
        import os
        try:
            size = os.get_terminal_size()
            return size.lines, size.columns
        except Exception:
            return 24, 80

    def _show_message(self, message: str, msg_type: str = "info"):
        """Display a message following CUA layout.

        CUA Layout:
        - Message on the message line (height-3)
        - Separator at height-2
        - Function keys at height-1

        Args:
            message: The message to display
            msg_type: One of "error", "success", "warning", "info"
        """
        height, width = self._get_terminal_size()

        # Clear screen
        print("\033[2J\033[H", end="", flush=True)

        # Message line (height-3)
        print(f"\033[{height - 2};1H", end="", flush=True)
        if msg_type == "error":
            print(Colors.error(message), end="", flush=True)
        elif msg_type == "success":
            print(Colors.success(message), end="", flush=True)
        elif msg_type == "warning":
            print(Colors.warning(message), end="", flush=True)
        else:
            print(Colors.info(message), end="", flush=True)

        # Separator (height-2)
        print(f"\033[{height - 1};1H", end="", flush=True)
        print(Colors.dim("─" * width), end="", flush=True)

        # Function key hint (height-1)
        print(f"\033[{height};1H", end="", flush=True)
        print(Colors.info("Enter=Continue"), end="", flush=True)

        input()

    def add_item(self):
        """Add a new item to inventory."""
        form = Form("ADD NEW ITEM")
        form.add_field("SKU", length=20, required=True)
        form.add_field("Name", length=40, required=True)
        form.add_field("Description", length=60)
        form.add_field("Quantity", length=10, field_type=FieldType.NUMERIC, default="0")
        form.add_field("Unit Price", length=10, default="0.00")
        form.add_field("Location", length=30)

        result = form.show()
        if result is None:
            return  # User cancelled with F3

        try:
            # Check if SKU already exists
            existing = self.db.get_item_by_sku(result["SKU"])
            if existing:
                self._show_message(f"ERROR: SKU '{result['SKU']}' already exists", "error")
                return

            item_id = self.db.add_item(
                sku=result["SKU"],
                name=result["Name"],
                description=result.get("Description", ""),
                quantity=int(result.get("Quantity", "0") or "0"),
                unit_price=float(result.get("Unit Price", "0.0") or "0.0"),
                location=result.get("Location", "")
            )
            self._show_message(f"ITEM ADDED - ID: {item_id}", "success")
        except Exception as e:
            self._show_message(f"ERROR: {e}", "error")

    def view_items(self):
        """View all items in inventory."""
        items = self.db.list_items()

        if not items:
            self._show_message("NO ITEMS IN INVENTORY", "warning")
            return

        table = Table("INVENTORY LIST", ["ID", "SKU", "Name", "Qty", "Price", "Location"])

        for item in items:
            table.add_row(
                item["id"],
                item["sku"],
                item["name"][:30],  # Truncate long names
                item["quantity"],
                f"${item['unit_price']:.2f}",
                item["location"][:20]  # Truncate long locations
            )

        table.show()

    def search_items(self):
        """Search for items."""
        form = Form("SEARCH ITEMS")
        form.add_field("Search Term", length=40, required=True)

        result = form.show()
        if result is None:
            return  # User cancelled with F3

        search_term = result["Search Term"]
        items = self.db.search_items(search_term)

        if not items:
            self._show_message(f"NO ITEMS FOUND FOR '{search_term.upper()}'", "warning")
            return

        table = Table(f"SEARCH RESULTS: {search_term.upper()}",
                     ["ID", "SKU", "Name", "Qty", "Price", "Location"])

        for item in items:
            table.add_row(
                item["id"],
                item["sku"],
                item["name"][:30],
                item["quantity"],
                f"${item['unit_price']:.2f}",
                item["location"][:20]
            )

        table.show()

    def update_item(self):
        """Update an existing item."""
        # First, get the item ID
        form = Form("UPDATE ITEM - SELECT")
        form.add_field("Item ID or SKU", length=20, required=True)
        result = form.show()
        if result is None:
            return  # User cancelled with F3

        # Find the item
        item_id_or_sku = result["Item ID or SKU"]
        item = None

        # Try as ID first
        try:
            item_id = int(item_id_or_sku)
            item = self.db.get_item(item_id)
        except ValueError:
            # Try as SKU
            item = self.db.get_item_by_sku(item_id_or_sku)

        if not item:
            self._show_message(f"ITEM NOT FOUND: {item_id_or_sku}", "error")
            return

        # Show update form with current values
        update_form = Form("UPDATE ITEM")
        update_form.add_field("SKU", length=20, default=item["sku"], required=True)
        update_form.add_field("Name", length=40, default=item["name"], required=True)
        update_form.add_field("Description", length=60, default=item["description"])
        update_form.add_field("Quantity", length=10, field_type=FieldType.NUMERIC,
                            default=str(item["quantity"]))
        update_form.add_field("Unit Price", length=10, default=str(item["unit_price"]))
        update_form.add_field("Location", length=30, default=item["location"])

        result = update_form.show()
        if result is None:
            return  # User cancelled with F3

        try:
            self.db.update_item(
                item["id"],
                sku=result["SKU"],
                name=result["Name"],
                description=result.get("Description", ""),
                quantity=int(result.get("Quantity", "0") or "0"),
                unit_price=float(result.get("Unit Price", "0.0") or "0.0"),
                location=result.get("Location", "")
            )
            self._show_message("ITEM UPDATED", "success")
        except Exception as e:
            self._show_message(f"ERROR: {e}", "error")

    def delete_item(self):
        """Delete an item from inventory."""
        form = Form("DELETE ITEM")
        form.add_field("Item ID or SKU", length=20, required=True)
        result = form.show()
        if result is None:
            return  # User cancelled with F3

        # Find the item
        item_id_or_sku = result["Item ID or SKU"]
        item = None

        # Try as ID first
        try:
            item_id = int(item_id_or_sku)
            item = self.db.get_item(item_id)
        except ValueError:
            # Try as SKU
            item = self.db.get_item_by_sku(item_id_or_sku)

        if not item:
            self._show_message(f"ITEM NOT FOUND: {item_id_or_sku}", "error")
            return

        # Confirm deletion (IBM convention: Y/N)
        confirm_form = Form("CONFIRM DELETE")
        confirm_form.add_text(f"Item: {item['sku']} - {item['name']}")
        confirm_form.add_field("Delete? (Y/N)", length=1, required=True)

        confirm = confirm_form.show()
        if confirm is None:
            return  # User cancelled with F3

        if confirm["Delete? (Y/N)"].upper() == "Y":
            if self.db.delete_item(item["id"]):
                self._show_message("ITEM DELETED", "success")
            else:
                self._show_message("DELETE FAILED", "error")
        else:
            self._show_message("DELETE CANCELLED", "info")

    def adjust_quantity(self):
        """Adjust the quantity of an item."""
        form = Form("ADJUST QUANTITY")
        form.add_field("Item ID or SKU", length=20, required=True)
        result = form.show()
        if result is None:
            return  # User cancelled with F3

        # Find the item
        item_id_or_sku = result["Item ID or SKU"]
        item = None

        # Try as ID first
        try:
            item_id = int(item_id_or_sku)
            item = self.db.get_item(item_id)
        except ValueError:
            # Try as SKU
            item = self.db.get_item_by_sku(item_id_or_sku)

        if not item:
            self._show_message(f"ITEM NOT FOUND: {item_id_or_sku}", "error")
            return

        # Show adjustment form
        adj_form = Form("ADJUST QUANTITY")
        adj_form.add_field("Item", length=40, field_type=FieldType.READONLY,
                          default=f"{item['sku']} - {item['name']}")
        adj_form.add_field("Current Qty", length=10, field_type=FieldType.READONLY,
                          default=str(item['quantity']))
        adj_form.add_field("New Qty", length=10, field_type=FieldType.NUMERIC,
                          required=True, default=str(item['quantity']))

        result = adj_form.show()
        if result is None:
            return  # User cancelled with F3

        try:
            new_qty = int(result["New Qty"])
            self.db.update_item(item["id"], quantity=new_qty)
            self._show_message(f"QUANTITY UPDATED: {item['quantity']} -> {new_qty}", "success")
        except Exception as e:
            self._show_message(f"ERROR: {e}", "error")


def load_sample_data(db: InventoryDB) -> int:
    """Load sample data into the database.

    Args:
        db: Database instance

    Returns:
        Number of items loaded
    """
    count = 0
    for sku, name, desc, qty, price, loc in SAMPLE_DATA:
        # Skip if SKU already exists
        if db.get_item_by_sku(sku):
            continue
        # Add some randomness to quantities for realism
        qty_variance = random.randint(-5, 10)
        actual_qty = max(0, qty + qty_variance)
        db.add_item(sku, name, desc, actual_qty, price, loc)
        count += 1
    return count


def clear_database(db: InventoryDB) -> int:
    """Clear all items from the database.

    Args:
        db: Database instance

    Returns:
        Number of items deleted
    """
    return db.clear_all()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inventory Management System - IBM 3270-style UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  inventory-app                  Start the application
  inventory-app --demo           Load sample data and start
  inventory-app --load-sample    Load sample data (additive)
  inventory-app --clear          Clear all data from database
  inventory-app --clear --demo   Clear and reload sample data
        """
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Load sample data for demonstration"
    )
    parser.add_argument(
        "--load-sample",
        action="store_true",
        help="Load sample data (additive, skips existing SKUs)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data from the database"
    )
    parser.add_argument(
        "--db",
        default="inventory.db",
        help="Path to database file (default: inventory.db)"
    )

    args = parser.parse_args()

    # Handle --clear
    if args.clear:
        db = InventoryDB(args.db)
        count = clear_database(db)
        print(f"Cleared {count} items from database.")
        db.close()
        if not args.demo and not args.load_sample:
            return

    # Handle --demo or --load-sample
    if args.demo or args.load_sample:
        db = InventoryDB(args.db)
        count = load_sample_data(db)
        print(f"Loaded {count} sample items.")
        db.close()
        if not args.demo:
            return

    # Run the app
    app = InventoryApp(args.db)
    app.run()


if __name__ == "__main__":
    main()
