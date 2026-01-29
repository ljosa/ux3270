#!/usr/bin/env python3
"""Display a message panel for screenshot."""
import sys
sys.path.insert(0, '/app/src')

from ux3270.dialog import MessagePanel

panel = MessagePanel(
    message="Record ITM001 has been successfully updated.",
    msg_type="success",
    title="UPDATE COMPLETE",
    panel_id="MSG001"
)
panel.show()
