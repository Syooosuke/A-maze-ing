"""Tests of the terminal rendering and of the interactive session."""

from __future__ import annotations

from amazeing.display.canvas import Canvas, Token
from amazeing.display.render import legend, render
from amazeing.display.session import Session
from amazeing.display.themes import THEMES
from mazegen import MazeGenerator


def maze() -> MazeGenerator:
    """Return a small generated maze."""
    return MazeGenerator(21, 15, (0, 0), (20, 14), seed=4).generate()


def test_canvas_size() -> None:
    """The canvas holds one spot per wall and per cell."""
    canvas = Canvas(maze())
    assert canvas.rows == 31
    assert canvas.cols == 43


def test_render_without_colour_is_plain_ascii() -> None:
    """The plain rendering carries no escape sequence."""
    picture = render(maze(), colour=False)
    assert "\x1b" not in picture
    assert set(picture) <= set("# EX%.\n")


def test_render_shows_entry_exit_and_pattern() -> None:
    """Entry, exit and the "42" are all visible."""
    picture = render(maze(), colour=False, show_path=True)
    assert "EE" in picture
    assert "XX" in picture
    assert "%%" in picture
    assert ".." in picture


def test_hiding_the_path() -> None:
    """The path is only drawn when asked for."""
    assert ".." not in render(maze(), colour=False, show_path=False)


def test_render_with_colour_uses_ansi() -> None:
    """The coloured rendering uses 256-colour escape sequences."""
    picture = render(maze(), theme=THEMES[1], colour=True)
    assert f"\x1b[38;5;{THEMES[1].wall}m" in picture


def test_pattern_has_its_own_colour() -> None:
    """The "42" is painted with the pattern colour of the theme."""
    picture = render(maze(), colour=True)
    assert f"\x1b[38;5;{THEMES[0].pattern}m" in picture


def test_legend_lists_every_token() -> None:
    """The legend explains all the colours in use."""
    text = legend(THEMES[0], colour=False)
    for label in ("entry", "exit", "42", "path", "wall"):
        assert label in text


def test_canvas_tokens() -> None:
    """A corridor cell is void, a pattern cell is a pattern token."""
    generator = maze()
    canvas = Canvas(generator)
    canvas.paint_pattern()
    pattern_x, pattern_y = sorted(generator.pattern_cells)[0]
    assert canvas.cells[2 * pattern_y + 1][2 * pattern_x + 1] is Token.PATTERN
    entry_x, entry_y = generator.entry
    assert canvas.cells[2 * entry_y + 1][2 * entry_x + 1] is Token.VOID


def test_session_cycles_options() -> None:
    """The session exposes the interactive toggles."""
    session = Session(maze(), colour=False)
    assert session.theme is THEMES[0]
    session.theme_index = (session.theme_index + 1) % len(THEMES)
    assert session.theme is THEMES[1]
    first = session.generator.grid
    session.regenerate()
    assert session.generator.grid is not first
    assert "seed" in session.status()
    assert session.screen()


def test_blocks_need_a_unicode_terminal() -> None:
    """Colour mode draws "██", which an ASCII terminal cannot show."""
    from amazeing.display.render import can_draw_blocks

    assert can_draw_blocks("utf-8")
    assert not can_draw_blocks("ascii")
    assert not can_draw_blocks(None)
    assert not can_draw_blocks("no-such-encoding")


def test_quit_is_the_last_menu_item() -> None:
    """Adding a menu item must not leave quit on an old number."""
    from amazeing.display.menu import MENU, QUIT_WORDS

    assert MENU[-1].startswith(f"{QUIT_WORDS[0]}. ")


def test_entry_and_exit_are_letters_in_colour_mode() -> None:
    """Entry and exit stay readable without telling colours apart."""
    picture = render(maze(), colour=True)
    assert "EE" in picture and "XX" in picture
