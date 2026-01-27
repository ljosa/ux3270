#!/usr/bin/env python3
"""Simple example demonstrating ux3270 and ux3270_ui libraries."""

from ux3270 import Screen, Field, FieldType
from ux3270_ui import Menu, Form, Table


def example_low_level():
    """Example using low-level ux3270 API."""
    print("\n=== Low-Level API Example ===\n")
    
    screen = Screen("USER REGISTRATION")
    screen.add_text(2, 2, "Please enter your information:")
    screen.add_field(Field(row=4, col=20, length=30, label="Full Name", required=True))
    screen.add_field(Field(row=6, col=20, length=30, label="Email", required=True))
    screen.add_field(Field(row=8, col=20, length=10, label="Age", field_type=FieldType.NUMERIC))
    screen.add_field(Field(row=10, col=20, length=20, label="Password", 
                          field_type=FieldType.PASSWORD, required=True))
    
    result = screen.show()
    
    print(f"\nRegistration complete!")
    print(f"Name: {result['Full Name']}")
    print(f"Email: {result['Email']}")
    print(f"Age: {result['Age']}")
    input("\nPress Enter to continue...")


def example_high_level_form():
    """Example using high-level Form API."""
    print("\n=== High-Level Form Example ===\n")
    
    form = Form("CUSTOMER SURVEY")
    form.add_text("Thank you for taking our survey!")
    form.add_field("Name", length=30, required=True)
    form.add_field("Company", length=40)
    form.add_field("Rating (1-10)", length=2, field_type=FieldType.NUMERIC, required=True)
    form.add_field("Comments", length=60)
    
    result = form.show()
    
    print(f"\nSurvey submitted!")
    print(f"Thank you, {result['Name']}!")
    input("\nPress Enter to continue...")


def example_table():
    """Example using Table display."""
    print("\n=== Table Display Example ===\n")
    
    table = Table("EMPLOYEE LIST", ["ID", "Name", "Department", "Status"])
    table.add_row("001", "Alice Johnson", "Engineering", "Active")
    table.add_row("002", "Bob Smith", "Marketing", "Active")
    table.add_row("003", "Carol Davis", "Sales", "On Leave")
    table.add_row("004", "David Wilson", "Engineering", "Active")
    table.add_row("005", "Eve Martinez", "HR", "Active")
    
    table.show()


def example_menu():
    """Example using Menu."""
    print("\n=== Menu Example ===\n")
    
    menu = Menu("DEMO APPLICATION")
    menu.add_item("1", "Low-Level Screen API", example_low_level)
    menu.add_item("2", "High-Level Form API", example_high_level_form)
    menu.add_item("3", "Table Display", example_table)
    
    menu.run()


if __name__ == "__main__":
    print("Welcome to ux3270 Demo!")
    print("This demonstrates the IBM 3270-like terminal library.\n")
    
    try:
        example_menu()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled. Goodbye!")
