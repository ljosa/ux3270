#!/usr/bin/env python3
"""Inventory Management System using IBM 3270-like UI."""

import sys
from typing import Optional
from ux3270 import FieldType
from ux3270_ui import Menu, Form, Table
from database import InventoryDB


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
        
        try:
            # Check if SKU already exists
            existing = self.db.get_item_by_sku(result["SKU"])
            if existing:
                print(f"\n\033[31mError: SKU '{result['SKU']}' already exists!\033[0m")
                input("Press Enter to continue...")
                return
                
            item_id = self.db.add_item(
                sku=result["SKU"],
                name=result["Name"],
                description=result.get("Description", ""),
                quantity=int(result.get("Quantity", "0")),
                unit_price=float(result.get("Unit Price", "0.0")),
                location=result.get("Location", "")
            )
            print(f"\n\033[32mItem added successfully! ID: {item_id}\033[0m")
        except Exception as e:
            print(f"\n\033[31mError adding item: {e}\033[0m")
            
        input("Press Enter to continue...")
        
    def view_items(self):
        """View all items in inventory."""
        items = self.db.list_items()
        
        if not items:
            print("\nNo items in inventory.")
            input("Press Enter to continue...")
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
        search_term = result["Search Term"]
        
        items = self.db.search_items(search_term)
        
        if not items:
            print(f"\nNo items found matching '{search_term}'")
            input("Press Enter to continue...")
            return
            
        table = Table(f"SEARCH RESULTS: '{search_term}'", 
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
            print(f"\n\033[31mItem not found: {item_id_or_sku}\033[0m")
            input("Press Enter to continue...")
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
        
        try:
            self.db.update_item(
                item["id"],
                sku=result["SKU"],
                name=result["Name"],
                description=result.get("Description", ""),
                quantity=int(result.get("Quantity", "0")),
                unit_price=float(result.get("Unit Price", "0.0")),
                location=result.get("Location", "")
            )
            print("\n\033[32mItem updated successfully!\033[0m")
        except Exception as e:
            print(f"\n\033[31mError updating item: {e}\033[0m")
            
        input("Press Enter to continue...")
        
    def delete_item(self):
        """Delete an item from inventory."""
        form = Form("DELETE ITEM")
        form.add_field("Item ID or SKU", length=20, required=True)
        result = form.show()
        
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
            print(f"\n\033[31mItem not found: {item_id_or_sku}\033[0m")
            input("Press Enter to continue...")
            return
            
        # Confirm deletion
        confirm_form = Form("CONFIRM DELETION")
        confirm_form.add_text(f"Delete item: {item['sku']} - {item['name']}?")
        confirm_form.add_field("Confirm (YES/NO)", length=3, required=True)
        
        confirm = confirm_form.show()
        
        if confirm["Confirm (YES/NO)"].upper() == "YES":
            if self.db.delete_item(item["id"]):
                print("\n\033[32mItem deleted successfully!\033[0m")
            else:
                print("\n\033[31mError deleting item\033[0m")
        else:
            print("\nDeletion cancelled.")
            
        input("Press Enter to continue...")
        
    def adjust_quantity(self):
        """Adjust the quantity of an item."""
        form = Form("ADJUST QUANTITY")
        form.add_field("Item ID or SKU", length=20, required=True)
        result = form.show()
        
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
            print(f"\n\033[31mItem not found: {item_id_or_sku}\033[0m")
            input("Press Enter to continue...")
            return
            
        # Show adjustment form
        adj_form = Form("ADJUST QUANTITY")
        adj_form.add_field("Item", length=40, field_type=FieldType.READONLY, 
                          default=f"{item['sku']} - {item['name']}")
        adj_form.add_field("Current Quantity", length=10, field_type=FieldType.READONLY,
                          default=str(item['quantity']))
        adj_form.add_field("New Quantity", length=10, field_type=FieldType.NUMERIC, 
                          required=True, default=str(item['quantity']))
        
        result = adj_form.show()
        
        try:
            new_qty = int(result["New Quantity"])
            self.db.update_item(item["id"], quantity=new_qty)
            print(f"\n\033[32mQuantity updated: {item['quantity']} → {new_qty}\033[0m")
        except Exception as e:
            print(f"\n\033[31mError adjusting quantity: {e}\033[0m")
            
        input("Press Enter to continue...")


def main():
    """Main entry point."""
    app = InventoryApp()
    app.run()


if __name__ == "__main__":
    main()
