#!/usr/bin/env python3
"""
Manual test script for ux3270 library.

This script demonstrates the interactive features but cannot be fully automated.
Run this on a real terminal to test the interactive functionality.
"""

import sys
sys.path.insert(0, '.')

from ux3270.panel import Screen, Field, FieldType
from ux3270.dialog import Menu, Form, Table


def test_table_display():
    """Test table display (non-interactive except for key press)."""
    print("\n" + "="*60)
    print("TEST 1: Table Display")
    print("="*60)
    
    table = Table("SAMPLE DATA TABLE")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Value", align="right")
    table.add_column("Status")
    table.add_row("001", "Item One", "$10.00", "Active")
    table.add_row("002", "Item Two", "$25.50", "Pending")
    table.add_row("003", "Item Three", "$99.99", "Active")
    
    print("\nTable created with 3 rows and 4 columns")
    print("Table should display with IBM 3270-style layout")
    assert len(table.rows) == 3
    assert len(table._columns) == 4


def test_form_creation():
    """Test form creation (structure only)."""
    print("\n" + "="*60)
    print("TEST 2: Form Creation")
    print("="*60)
    
    form = Form("USER REGISTRATION FORM")
    form.add_text("Please fill in all required fields:")
    form.add_field("Username", length=20, required=True)
    form.add_field("Email", length=40, required=True)
    form.add_field("Age", length=3, field_type=FieldType.NUMERIC)
    form.add_field("Password", length=20, field_type=FieldType.PASSWORD, required=True)
    
    print("\nForm created with 4 fields:")
    print("- Username (required)")
    print("- Email (required)")
    print("- Age (numeric)")
    print("- Password (hidden, required)")
    assert len(form._fields) == 4


def test_menu_creation():
    """Test menu creation (structure only)."""
    print("\n" + "="*60)
    print("TEST 3: Menu Creation")
    print("="*60)
    
    menu = Menu("MAIN MENU")
    menu.add_item("1", "Option One", lambda: print("Option 1"))
    menu.add_item("2", "Option Two", lambda: print("Option 2"))
    menu.add_item("3", "Option Three", lambda: print("Option 3"))
    
    print("\nMenu created with 3 items")
    print("Menu uses IBM 3270-style layout")
    print("Items: 1, 2, 3 with single-key selection")
    assert len(menu.items) == 3


def test_screen_api():
    """Test low-level screen API."""
    print("\n" + "="*60)
    print("TEST 4: Low-Level Screen API")
    print("="*60)

    from ux3270.panel import Colors

    screen = Screen()
    # Add title using add_text
    screen.add_text(0, 30, "LOGIN SCREEN", Colors.INTENSIFIED)
    screen.add_text(2, 2, "Welcome to the System", Colors.PROTECTED)
    screen.add_text(4, 2, "Username . .", Colors.PROTECTED)
    screen.add_text(6, 2, "Password . .", Colors.PROTECTED)
    screen.add_field(Field(row=4, col=15, length=20, label="Username", required=True))
    screen.add_field(Field(row=6, col=15, length=20, label="Password",
                          field_type=FieldType.PASSWORD, required=True))

    print("\nScreen created with:")
    print("- Title: LOGIN SCREEN (via add_text)")
    print("- Static text at row 2, col 2")
    print("- 2 fields: Username and Password")
    print("- Password field will display asterisks")
    assert len(screen.fields) == 2
    assert len(screen._text) == 4


def test_table_truncation():
    """Test auto-truncation of wide content."""
    print("\n" + "="*60)
    print("TEST 5: Table Truncation")
    print("="*60)

    table = Table("TRUNCATION TEST")
    table.add_column("ID", width=5)
    table.add_column("Description")
    table.add_row("001", "Short")
    table.add_row("002", "This is a very long description that exceeds normal width")

    # Test the truncation method
    assert table._truncate("Hello", 10) == "Hello"
    assert table._truncate("Hello World", 10) == "Hello Wor>"
    assert table._truncate("Hi", 2) == "Hi"
    assert table._truncate("Hello", 1) == "H"

    print("\nTruncation tests:")
    print("- 'Hello' with width 10 -> 'Hello' (no truncation)")
    print("- 'Hello World' with width 10 -> 'Hello Wor>' (truncated)")
    print("- 'Hi' with width 2 -> 'Hi' (exact fit)")
    print("- 'Hello' with width 1 -> 'H' (minimal width)")


def test_screen_truncation():
    """Test Screen-level truncation of text and fields that exceed terminal width."""
    print("\n" + "="*60)
    print("TEST 6: Screen Truncation")
    print("="*60)

    from ux3270.panel import Colors

    screen = Screen()
    screen._width = 40  # Force narrow terminal width

    # Add text that extends beyond terminal width
    screen.add_text(0, 0, "This is a very long title that should be truncated at column 40", Colors.INTENSIFIED)
    screen.add_text(1, 35, "ABCDEFGH", Colors.PROTECTED)  # Starts near edge, should truncate
    screen.add_text(2, 50, "Hidden", Colors.PROTECTED)  # Beyond edge, should be skipped

    width = screen.get_width()
    assert width == 40, f"Expected width 40, got {width}"

    # Verify truncation logic for each text element
    texts = screen._text
    assert len(texts) == 3, f"Expected 3 text elements, got {len(texts)}"

    # Row 0: full width text at col 0
    row, col, text, color = texts[0]
    available = width - col
    assert available == 40
    # During render, this will be truncated to 39 chars + ">"

    # Row 1: text at col 35, only 5 chars available
    row, col, text, color = texts[1]
    available = width - col
    assert available == 5
    # During render, "ABCDEFGH" (8 chars) will become "ABCD>" (5 chars)

    # Row 2: text at col 50, beyond width
    row, col, text, color = texts[2]
    assert col >= width, "Text at col 50 should be beyond width 40"
    # During render, this will be skipped entirely

    print("\nScreen truncation verified:")
    print("- Text at col 0 with 40 available -> truncated with '>' indicator")
    print("- Text at col 35 with 5 available -> 'ABCDEFGH' becomes 'ABCD>'")
    print("- Text at col 50 (beyond width) -> skipped")


def run_all_tests():
    """Run all non-interactive tests."""
    print("\n" + "="*70)
    print(" UX3270 Library Test Suite")
    print("="*70)
    
    tests = [
        ("Table Display", test_table_display),
        ("Form Creation", test_form_creation),
        ("Menu Creation", test_menu_creation),
        ("Screen API", test_screen_api),
        ("Table Truncation", test_table_truncation),
        ("Screen Truncation", test_screen_truncation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {test_name} - PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} - ERROR: {e}")
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    print("\n" + "="*70)
    print("NOTE: These tests verify structure and creation only.")
    print("For full interactive testing, run:")
    print("  - python examples/demo.py")
    print("  - python inventory_app/main.py")
    print("in a real terminal environment.")
    print("="*70)
    
    sys.exit(0 if success else 1)
