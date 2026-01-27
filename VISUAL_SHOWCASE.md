# Visual Showcase - ux3270 IBM 3270-like Terminal Library

This document shows what the ux3270 library UI looks like in action.

## 1. Main Menu

The inventory management system starts with an IBM 3270-style menu:

```
╔════════════════════════════════════════════════╗
║ INVENTORY MANAGEMENT SYSTEM               ║
╚════════════════════════════════════════════════╝

  1 - Add New Item
  2 - View All Items
  3 - Search Items
  4 - Update Item
  5 - Delete Item
  6 - Adjust Quantity

Press a key to select an option, or X to exit
```

**Features**:
- IBM 3270-style box borders (╔═╗║╚╝)
- Single-key selection (press 1-6)
- Clean, professional appearance

## 2. Data Entry Form

When adding a new item, users see a form with labeled fields:

```
═══ ADD NEW ITEM ═══

  SKU: WIDGET001______________

  Name: Super Widget Pro_____________________________

  Description: High-quality widget for professional use________________

  Quantity: 100_______

  Unit Price: 29.99_______

  Location: Warehouse A - Shelf 3_______


Tab: Next field | Shift+Tab: Previous | Enter: Submit | Ctrl+C: Cancel
```

**Features**:
- Clear field labels aligned on the left
- Underscores show remaining field length
- Helpful keyboard shortcuts at bottom
- Tab navigation between fields
- Real-time input validation

## 3. Table Display

Viewing inventory shows data in a formatted table:

```
╔═══════════════════════╗
║ INVENTORY LIST      ║
╚═══════════════════════╝

  ID  │ SKU         │ Name                    │ Qty │ Price   │ Location
  ────┼─────────────┼──────────────────────────┼─────┼─────────┼────────────────────
  1   │ WIDGET001   │ Super Widget Pro         │ 100 │ $29.99  │ Warehouse A - She
  2   │ GADGET042   │ Premium Gadget           │ 50  │ $49.99  │ Warehouse B - She
  3   │ TOOL123     │ Professional Tool Set    │ 25  │ $199.99 │ Warehouse A - She
  4   │ PART567     │ Replacement Part Kit     │ 200 │ $9.99   │ Warehouse C - Bin
  5   │ DEVICE999   │ Electronic Device        │ 10  │ $299.99 │ Secure Storage

Total: 5 rows

Press any key to continue...
```

**Features**:
- Column headers in bold
- Clean table borders with Unicode characters (│ ─ ┼)
- Automatic column width calculation
- Row count summary
- Professional data presentation

## 4. Update Form (Pre-filled)

When updating an item, the form shows current values:

```
═══ UPDATE ITEM ═══

  SKU: WIDGET001______________

  Name: Super Widget Pro_____________________________

  Description: High-quality widget for professional use________________

  Quantity: 150_______

  Unit Price: 29.99_______

  Location: Warehouse A - Shelf 3_______


Tab: Next field | Shift+Tab: Previous | Enter: Submit | Ctrl+C: Cancel
```

**Features**:
- Pre-filled with current values
- Edit any field
- Same navigation as new entry
- Validation on submit

## 5. Confirmation Dialog

For destructive actions like delete:

```
═══ CONFIRM DELETION ═══

  Delete item: WIDGET001 - Super Widget Pro?

  Confirm (YES/NO): ___
```

**Features**:
- Clear confirmation message
- Simple YES/NO input
- Prevents accidental deletions

## 6. Search Results

Search functionality displays matching items:

```
╔═══════════════════════════════╗
║ SEARCH RESULTS: 'widget'    ║
╚═══════════════════════════════╝

  ID  │ SKU         │ Name                    │ Qty │ Price   │ Location
  ────┼─────────────┼──────────────────────────┼─────┼─────────┼────────────────────
  1   │ WIDGET001   │ Super Widget Pro         │ 100 │ $29.99  │ Warehouse A - She
  3   │ WIDGET042   │ Basic Widget             │ 500 │ $5.99   │ Warehouse C - Bin

Total: 2 rows
```

**Features**:
- Shows search term in title
- Same table format as full list
- Easy to read results

## Interactive Features (Not Shown)

The screenshots above show static displays, but the actual library provides:

### Field Editing
- **Character-by-character input**: Type naturally, see characters appear
- **Backspace support**: Delete characters with backspace
- **Field length limits**: Prevents typing beyond field length
- **Type validation**: Numeric fields only accept digits
- **Cursor positioning**: See cursor at current position

### Password Fields
```
  Password: ************______
```
- Characters are masked with asterisks
- Actual value is stored securely
- Length shown, content hidden

### Tab Navigation
- **Tab**: Move to next editable field
- **Shift+Tab**: Move to previous editable field
- **Auto-skip**: Read-only fields are skipped
- **Wrap-around**: Tab from last field returns to first

### Field Validation
```
Field 'Email' is required

Tab: Next field | Shift+Tab: Previous | Enter: Submit | Ctrl+C: Cancel
```
- Error messages appear in red at bottom
- Form cannot be submitted with invalid data
- Custom validators supported

### Read-Only Fields
```
  Item ID: 001          (greyed out, cannot edit)
```
- Displayed in dimmed color
- Show information without allowing edits
- Useful for IDs, timestamps, calculated values

## IBM 3270 Authenticity

The design closely follows IBM 3270 terminal conventions:

1. **Block-Oriented Display**: Entire screens are created before display
2. **Field-Based Entry**: Users fill in fields, not lines
3. **Protected Fields**: Some fields cannot be edited
4. **Form Submission**: Complete form before submitting
5. **Status Messages**: Error and help text at bottom
6. **Box Drawing**: Classic terminal graphics (╔═╗ ║ ╚╝)
7. **Single-Key Selection**: Menus use individual keys, not arrows

## Color and Styling

The library uses ANSI escape codes for:
- **Bold text**: Titles, labels, menu numbers, table headers
- **Dim text**: Help text, read-only fields
- **Red text**: Error messages
- **Normal text**: User input, data values

All styling is done with standard ANSI sequences that work on any modern terminal.

## Try It Yourself!

1. Install: `pip install -e .`
2. Run demo: `python examples/demo.py`
3. Run inventory app: `inventory-app`

Experience the full interactive IBM 3270-style interface!
