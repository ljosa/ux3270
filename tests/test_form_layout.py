"""Tests for Form dynamic field layout and dot leaders."""

from ux3270.dialog import Form


def _build(form, width=80):
    """Build a screen from a form and return it."""
    return form._build_screen(24, width)


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
    """Extract the leader portion for the Nth field."""
    row, label = form._field_label_rows[field_index]
    text = _get_label_text(screen, row, form.label_col)
    assert text is not None, f"No text at row {row}"
    assert text.startswith(label)
    return text[len(label):]


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
            row, label = form._field_label_rows[i]
            text = _get_label_text(screen, row, form.label_col)
            assert form.label_col + len(text) == field_col

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
