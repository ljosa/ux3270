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
    
    table = Table("SAMPLE DATA TABLE", ["ID", "Name", "Value", "Status"])
    table.add_row("001", "Item One", "$10.00", "Active")
    table.add_row("002", "Item Two", "$25.50", "Pending")
    table.add_row("003", "Item Three", "$99.99", "Active")
    
    print("\nTable created with 3 rows and 4 columns")
    print("Table should display with IBM 3270-style borders")
    return True


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
    return True


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
    print("Menu should have IBM 3270-style box borders")
    print("Items: 1, 2, 3 with single-key selection")
    return True


def test_screen_api():
    """Test low-level screen API."""
    print("\n" + "="*60)
    print("TEST 4: Low-Level Screen API")
    print("="*60)
    
    screen = Screen("LOGIN SCREEN")
    screen.add_text(2, 2, "Welcome to the System")
    screen.add_field(Field(row=4, col=15, length=20, label="Username", required=True))
    screen.add_field(Field(row=6, col=15, length=20, label="Password", 
                          field_type=FieldType.PASSWORD, required=True))
    
    print("\nScreen created with:")
    print("- Title: LOGIN SCREEN")
    print("- Static text at row 2, col 2")
    print("- 2 fields: Username and Password")
    print("- Password field will display asterisks")
    return True


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
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} - PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} - FAILED")
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
