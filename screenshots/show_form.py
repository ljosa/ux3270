#!/usr/bin/env python3
"""Display a form for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import Form
from ux3270.panel import FieldType

form = Form("ADD INVENTORY ITEM", panel_id="INV001",
            instruction="Enter item details and press Enter")
form.add_field("Item ID", length=10, required=True)
form.add_field("Description", length=30, required=True)
form.add_field("Quantity", length=8, field_type=FieldType.NUMERIC)
form.add_field("Unit Price", length=12, field_type=FieldType.NUMERIC)
form.add_field("Location", length=15)
form.show()
