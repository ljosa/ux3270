#!/usr/bin/env python3
"""Display tabular entry for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import TabularEntry
from ux3270.panel import FieldType

te = TabularEntry("ADJUST INVENTORY", panel_id="ADJ001",
                  instruction="Enter new quantities and press Enter to submit")
te.add_column("ID", width=8)
te.add_column("Description", width=22)
te.add_column("Current", width=8)
te.add_column("New Qty", width=8, editable=True, field_type=FieldType.NUMERIC)

te.add_row(ID="ITM001", Description="Widget Assembly Kit", Current="150")
te.add_row(ID="ITM002", Description="Precision Gears Set", Current="75")
te.add_row(ID="ITM003", Description="Industrial Bearing", Current="200")
te.add_row(ID="ITM004", Description="Control Module", Current="25")

te.show()
