#!/usr/bin/env python3
"""Display a selection list for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import SelectionList

sel = SelectionList("SELECT DEPARTMENT", panel_id="SEL001",
                    instruction="Type S to select item, press Enter")
sel.add_column("Code")
sel.add_column("Name")
sel.add_column("Manager")

sel.add_row(Code="ENG", Name="Engineering", Manager="J. Smith")
sel.add_row(Code="SAL", Name="Sales", Manager="M. Johnson")
sel.add_row(Code="MKT", Name="Marketing", Manager="S. Williams")
sel.add_row(Code="FIN", Name="Finance", Manager="R. Brown")
sel.add_row(Code="OPS", Name="Operations", Manager="L. Davis")

sel.show()
