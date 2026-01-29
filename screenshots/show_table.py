#!/usr/bin/env python3
"""Display a table for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import Table

table = Table("INVENTORY REPORT", panel_id="RPT001",
              instruction="Press F7/F8 to page, F3 to exit")
table.add_column("ID")
table.add_column("Description")
table.add_column("Qty", align="right")
table.add_column("Price", align="right")
table.add_column("Status")

table.add_row("ITM001", "Widget Assembly Kit", "150", "$24.99", "Active")
table.add_row("ITM002", "Precision Gears Set", "75", "$89.50", "Active")
table.add_row("ITM003", "Industrial Bearing", "200", "$12.75", "Active")
table.add_row("ITM004", "Control Module", "25", "$199.00", "Low Stock")
table.add_row("ITM005", "Power Supply Unit", "0", "$149.99", "Out of Stock")
table.add_row("ITM006", "Sensor Array", "180", "$67.25", "Active")

table.show()
