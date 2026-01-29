#!/usr/bin/env python3
"""Display a work-with list for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import WorkWithList

wwl = WorkWithList("WORK WITH INVENTORY", panel_id="INV010",
                   instruction="Type option, press Enter.")
wwl.add_column("ID")
wwl.add_column("Description")
wwl.add_column("Qty", align="right")
wwl.add_column("Status")

wwl.add_action("2", "Change")
wwl.add_action("4", "Delete")
wwl.add_action("5", "Display")

wwl.add_row(ID="ITM001", Description="Widget Assembly Kit", Qty="150", Status="Active")
wwl.add_row(ID="ITM002", Description="Precision Gears Set", Qty="75", Status="Active")
wwl.add_row(ID="ITM003", Description="Industrial Bearing", Qty="200", Status="Active")
wwl.add_row(ID="ITM004", Description="Control Module", Qty="25", Status="Low Stock")
wwl.add_row(ID="ITM005", Description="Power Supply Unit", Qty="0", Status="Out of Stock")

wwl.show()
