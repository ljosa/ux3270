"""Tests for Form dynamic field layout and dot leaders."""

from ux3270.dialog import Form


def _build(form, width=80, height=24, page=0, page_size=None):
    """Build a screen from a form and return it."""
    if page_size is None:
        page_size = form._page_size(height)
    return form._build_screen(page, page_size, height, width)


def _field_cols(screen):
    """Return list of field col values."""
    return [f.col for f in screen.fields]


def _get_label_text(screen, row, col):
    """Find the rendered text at a given row and col."""
    for r, c, text, _color in screen._text:
        if r == row and c == col:
            return text
    return None


def _get_leader(form, screen, field_index):
    """Extract the leader portion for the Nth field.

    Finds the field's label text on the screen by scanning for rows that
    start with the label, since pagination remaps row positions.
    """
    _, label = form._field_label_rows[field_index]
    # Find rendered row containing this label
    for r, c, text, _color in screen._text:
        if c == form.label_col and text.startswith(label):
            return text[len(label):]
    assert False, f"No label text found for field {field_index} ({label!r})"


class TestFieldColComputation:
    def test_short_labels_use_default(self):
        """Labels that fit within default field_col keep it at 20."""
        form = Form("T")
        form.add_field("Name", length=10)
        form.add_field("Age", length=3)
        screen = _build(form)
        assert all(c == 20 for c in _field_cols(screen))

    def test_long_label_shifts_field_col(self):
        """A long label pushes all fields to the right."""
        form = Form("T")
        form.add_field("X", length=10)
        form.add_field("Very Long Label Here", length=10)
        screen = _build(form)
        expected = form.label_col + len("Very Long Label Here") + form.MIN_LABEL_FIELD_GAP
        assert all(c == expected for c in _field_cols(screen))

    def test_no_fields(self):
        """Form with no fields still builds without error."""
        form = Form("T")
        screen = _build(form)
        assert screen.fields == []

    def test_field_col_floor(self):
        """field_col acts as a minimum even with very short labels."""
        form = Form("T")
        form.add_field("A", length=5)
        screen = _build(form)
        assert _field_cols(screen) == [20]

    def test_field_col_clamped_to_terminal_width(self):
        """Long labels don't push field_col past the terminal width."""
        form = Form("T")
        form.add_field("A" * 70, length=20)
        # On an 80-column terminal, field_col should be clamped to
        # width - MIN_FIELD_WIDTH = 70, not label_col + 70 + 4 = 76
        screen = _build(form, width=80)
        assert _field_cols(screen) == [80 - form.MIN_FIELD_WIDTH]

    def test_field_col_clamp_applies_to_all_fields(self):
        """When clamped, all fields share the clamped column."""
        form = Form("T")
        form.add_field("A" * 70, length=20)
        form.add_field("B", length=5)
        screen = _build(form, width=80)
        cols = _field_cols(screen)
        assert cols[0] == cols[1]
        assert cols[0] == 80 - form.MIN_FIELD_WIDTH


class TestDotLeaders:
    def test_leader_starts_with_space(self):
        form = Form("T")
        form.add_field("Name", length=5)
        screen = _build(form)
        leader = _get_leader(form, screen, 0)
        assert leader[0] == " "

    def test_leader_ends_with_space(self):
        """Leader always ends with a space (never a dot next to the field)."""
        form = Form("T")
        form.add_field("Name", length=5)
        screen = _build(form)
        leader = _get_leader(form, screen, 0)
        assert leader[-1] == " "

    def test_leader_contains_dots(self):
        form = Form("T")
        form.add_field("Name", length=5)
        screen = _build(form)
        leader = _get_leader(form, screen, 0)
        assert "." in leader

    def test_leader_length_fills_to_field_col(self):
        """Label text + leader fills exactly to field_col."""
        form = Form("T")
        form.add_field("Name", length=5)
        screen = _build(form)
        text = _get_label_text(screen, form.BODY_START_ROW, form.label_col)
        field_col = screen.fields[0].col
        assert len(text) == field_col - form.label_col

    def test_dots_align_across_labels(self):
        """Dots are at the same column positions regardless of label length."""
        form = Form("T")
        form.add_field("Employer Name", length=30)
        form.add_field("Employer TIN", length=10)
        screen = _build(form)

        text1 = _get_label_text(screen, form.BODY_START_ROW, form.label_col)
        text2 = _get_label_text(screen, form.BODY_START_ROW + 2, form.label_col)

        assert len(text1) == len(text2)

        dot_cols_1 = {i for i, ch in enumerate(text1) if ch == "."}
        dot_cols_2 = {i for i, ch in enumerate(text2) if ch == "."}
        assert dot_cols_1 == dot_cols_2
        assert len(dot_cols_1) > 0

    def test_dots_align_with_large_length_difference(self):
        """Dots align even when labels differ greatly in length."""
        form = Form("T")
        form.add_field("A", length=5)
        form.add_field("Much Longer Label", length=5)
        screen = _build(form)

        text_a = _get_label_text(screen, form.BODY_START_ROW, form.label_col)
        text_long = _get_label_text(screen, form.BODY_START_ROW + 2, form.label_col)

        dot_cols_a = {i for i, ch in enumerate(text_a) if ch == "."}
        dot_cols_long = {i for i, ch in enumerate(text_long) if ch == "."}
        # Longer label's dots should be a subset of shorter label's dots
        assert dot_cols_long <= dot_cols_a
        assert len(dot_cols_a) > len(dot_cols_long)

    def test_short_label_gets_more_dots(self):
        """A shorter label gets more dots to fill its larger gap."""
        form = Form("T")
        form.add_field("Age", length=3)
        form.add_field("Employer Name", length=30)
        screen = _build(form)

        leader_age = _get_leader(form, screen, 0)
        leader_name = _get_leader(form, screen, 1)
        assert leader_age.count(".") > leader_name.count(".")

    def test_all_labels_fill_to_same_field_col(self):
        """All labels + leaders end at the same column (field_col)."""
        form = Form("T")
        form.add_field("A", length=5)
        form.add_field("Much Longer", length=5)
        screen = _build(form)

        field_col = screen.fields[0].col
        for i in range(len(form._field_label_rows)):
            leader = _get_leader(form, screen, i)
            _, label = form._field_label_rows[i]
            assert form.label_col + len(label) + len(leader) == field_col

    def test_even_gap_ends_with_space(self):
        # gap = 20 - 2 - 4 = 14 (even)
        form = Form("T")
        form.add_field("Name", length=5)
        screen = _build(form)
        leader = _get_leader(form, screen, 0)
        assert leader[-1] == " "

    def test_odd_gap_ends_with_space(self):
        # gap = 20 - 2 - 3 = 15 (odd)
        form = Form("T")
        form.add_field("Age", length=3)
        screen = _build(form)
        leader = _get_leader(form, screen, 0)
        assert leader[-1] == " "


class TestStaticTextSeparation:
    def test_add_text_not_in_field_labels(self):
        """add_text items go to _static_text, not _field_label_rows."""
        form = Form("T")
        form.add_text("Some instructions")
        form.add_field("Name", length=10)
        assert len(form._field_label_rows) == 1
        assert len(form._static_text) == 1

    def test_add_text_rendered_separately(self):
        """Static text and field labels are both rendered."""
        form = Form("T")
        form.add_text("Instructions here")
        form.add_field("Name", length=10)
        screen = _build(form)
        rendered = [t for _, _, t, _ in screen._text]
        assert any("Instructions here" in s for s in rendered)
        assert any("Name" in s for s in rendered)


class TestFieldLabelRows:
    def test_stores_correct_tuples(self):
        form = Form("T")
        form.add_field("First", length=10)
        form.add_field("Second", length=10)
        assert form._field_label_rows == [
            (form.BODY_START_ROW, "First"),
            (form.BODY_START_ROW + 2, "Second"),
        ]


class TestWrapLines:
    def test_simple_text(self):
        assert Form._wrap_lines("hello world", 80) == ["hello world"]

    def test_wraps_long_line(self):
        result = Form._wrap_lines("word " * 20, 20)
        assert all(len(line) <= 20 for line in result)
        assert len(result) > 1

    def test_preserves_blank_lines(self):
        assert Form._wrap_lines("a\n\nb", 80) == ["a", "", "b"]

    def test_empty_string(self):
        assert Form._wrap_lines("", 80) == [""]

    def test_whitespace_only_paragraph(self):
        """textwrap.wrap returns [] for whitespace-only; _wrap_lines yields ''."""
        assert Form._wrap_lines("   ", 80) == [""]

    def test_multiple_paragraphs(self):
        result = Form._wrap_lines("first\nsecond\nthird", 80)
        assert result == ["first", "second", "third"]


def _get_fkeys_text(screen):
    """Return the function keys text from the last row of the screen."""
    # Function keys are on the last row (height - 1)
    for r, c, text, _color in screen._text:
        if c == 0 and ("F3=" in text or "F7=" in text or "F8=" in text):
            return text
    return ""


def _visible_labels(screen, label_col=2):
    """Return the list of field labels visible on the screen."""
    labels = []
    for f in screen.fields:
        labels.append(f.label)
    return labels



class TestPagination:
    def test_all_fields_fit_no_pagination(self):
        """Form with 2 fields on a 24-line terminal — no F7/F8 in function keys."""
        form = Form("T")
        form.add_field("Name", length=10)
        form.add_field("Age", length=3)
        screen = _build(form, height=24)
        fkeys = _get_fkeys_text(screen)
        assert "F7=" not in fkeys
        assert "F8=" not in fkeys

    def test_fields_overflow_shows_pagination_keys(self):
        """Form with 20 fields on a 24-line terminal — F8=Down in function keys."""
        form = Form("T")
        for i in range(20):
            form.add_field(f"Field {i}", length=10)
        # page_size = (24 - 5) // 2 = 9
        screen = _build(form, height=24, page=0)
        fkeys = _get_fkeys_text(screen)
        assert "F8=Down" in fkeys
        assert "F7=" not in fkeys  # First page: no Up

    def test_page_shows_correct_fields(self):
        """Build page 0 and page 1, verify correct field labels on each."""
        form = Form("T")
        for i in range(20):
            form.add_field(f"Field {i}", length=10)
        page_size = form._page_size(24)  # 9

        screen0 = _build(form, height=24, page=0, page_size=page_size)
        labels0 = _visible_labels(screen0)
        assert labels0 == [f"Field {i}" for i in range(page_size)]

        screen1 = _build(form, height=24, page=1, page_size=page_size)
        labels1 = _visible_labels(screen1)
        assert labels1 == [f"Field {i}" for i in range(page_size, 2 * page_size)]

    def test_page_size_calculation(self):
        """Verify page_size computation from terminal height."""
        form = Form("T")
        # Chrome = 5 lines; each item = 2 rows
        chrome = form.BODY_START_ROW + form._FOOTER_LINES
        assert form._page_size(24) == (24 - chrome) // 2  # 9
        assert form._page_size(10) == (10 - chrome) // 2  # 2
        assert form._page_size(6) == 1  # minimum

    def test_field_col_consistent_across_pages(self):
        """field_col is the same on page 0 and page 1."""
        form = Form("T")
        # Add a long-labeled field first and short ones after
        form.add_field("Very Long Label Here", length=10)
        for i in range(19):
            form.add_field(f"F{i}", length=10)
        page_size = form._page_size(24)

        screen0 = _build(form, height=24, page=0, page_size=page_size)
        screen1 = _build(form, height=24, page=1, page_size=page_size)

        cols0 = set(_field_cols(screen0))
        cols1 = set(_field_cols(screen1))
        assert len(cols0) == 1
        assert cols0 == cols1

    def test_static_text_paginates_with_fields(self):
        """A form with interleaved add_text and add_field paginates correctly."""
        form = Form("T")
        form.add_text("Section 1")
        form.add_field("Name", length=10)
        form.add_text("Section 2")
        form.add_field("Age", length=3)
        # 4 items total; force page_size=2 so they span 2 pages
        screen0 = _build(form, height=24, page=0, page_size=2)
        screen1 = _build(form, height=24, page=1, page_size=2)

        # Page 0: "Section 1" text + "Name" field
        rendered0 = [t for _, _, t, _ in screen0._text]
        assert any("Section 1" in s for s in rendered0)
        assert any("Name" in s for s in rendered0)
        assert not any("Section 2" in s for s in rendered0)

        # Page 1: "Section 2" text + "Age" field
        rendered1 = [t for _, _, t, _ in screen1._text]
        assert any("Section 2" in s for s in rendered1)
        assert any("Age" in s for s in rendered1)
        assert not any("Section 1" in s for s in rendered1)

    def test_last_page_shows_f7_no_f8(self):
        """Last page shows F7=Up but not F8=Down."""
        form = Form("T")
        for i in range(20):
            form.add_field(f"Field {i}", length=10)
        page_size = form._page_size(24)
        last_page = (len(form._items) - 1) // page_size

        screen = _build(form, height=24, page=last_page, page_size=page_size)
        fkeys = _get_fkeys_text(screen)
        assert "F7=Up" in fkeys
        assert "F8=" not in fkeys
