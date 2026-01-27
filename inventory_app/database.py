"""Database module for the inventory management system."""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime


class InventoryDB:
    """Manages SQLite database for inventory items."""
    
    def __init__(self, db_path: str = "inventory.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                unit_price REAL NOT NULL DEFAULT 0.0,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        
    def add_item(
        self,
        sku: str,
        name: str,
        description: str = "",
        quantity: int = 0,
        unit_price: float = 0.0,
        location: str = ""
    ) -> int:
        """
        Add a new item to inventory.
        
        Args:
            sku: Stock Keeping Unit (unique identifier)
            name: Item name
            description: Item description
            quantity: Initial quantity
            unit_price: Price per unit
            location: Storage location
            
        Returns:
            ID of created item
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO items (sku, name, description, quantity, unit_price, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sku, name, description, quantity, unit_price, location))
        self.conn.commit()
        return cursor.lastrowid
        
    def update_item(
        self,
        item_id: int,
        sku: str = None,
        name: str = None,
        description: str = None,
        quantity: int = None,
        unit_price: float = None,
        location: str = None
    ) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: ID of item to update
            sku: New SKU (optional)
            name: New name (optional)
            description: New description (optional)
            quantity: New quantity (optional)
            unit_price: New price (optional)
            location: New location (optional)
            
        Returns:
            True if item was updated
        """
        updates = []
        params = []
        
        if sku is not None:
            updates.append("sku = ?")
            params.append(sku)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        if unit_price is not None:
            updates.append("unit_price = ?")
            params.append(unit_price)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
            
        if not updates:
            return False
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(item_id)
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE items
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        self.conn.commit()
        return cursor.rowcount > 0
        
    def delete_item(self, item_id: int) -> bool:
        """
        Delete an item from inventory.
        
        Args:
            item_id: ID of item to delete
            
        Returns:
            True if item was deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.conn.commit()
        return cursor.rowcount > 0
        
    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of item to retrieve
            
        Returns:
            Item data as dictionary, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by SKU.
        
        Args:
            sku: SKU to search for
            
        Returns:
            Item data as dictionary, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items WHERE sku = ?", (sku,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def list_items(self) -> List[Dict[str, Any]]:
        """
        Get all items in inventory.
        
        Returns:
            List of items as dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items ORDER BY sku")
        return [dict(row) for row in cursor.fetchall()]
        
    def search_items(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search items by SKU, name, or description.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching items
        """
        cursor = self.conn.cursor()
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM items
            WHERE sku LIKE ? OR name LIKE ? OR description LIKE ?
            ORDER BY sku
        """, (search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
        
    def close(self):
        """Close database connection."""
        self.conn.close()
