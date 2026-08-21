"""Optional graphical rendering of the maze with the MiniLibX library.

The ``mlx`` package (shipped with the subject as ``mlx-2.2.tgz``) is a thin
ctypes wrapper around the C MiniLibX.  It is **not** a dependency of this
project: when it is missing, or when no display is available, the program
falls back to the terminal renderer with a clear message.

The whole maze is drawn into a single MiniLibX image, which is then blitted
in one call -- drawing pixel per pixel through ``mlx_pixel_put`` would be
far too slow for a maze of a few hundred cells.
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, List, Optional

from amazeing.render import Canvas, Theme, Token
from amazeing.ui import Session
from mazegen import MazeError

# X11 keysyms of the keys driving the viewer.
KEY_REGENERATE = 0x31  # '1'
KEY_PATH = 0x32        # '2'
KEY_COLOURS = 0x33     # '3'
KEY_PATTERN = 0x34     # '4'
KEY_SAVE = 0x35        # '5'
KEY_QUIT = 0x36        # '6'
KEY_Q = 0x71           # 'q'
KEY_ESCAPE = 0xFF1B    # Escape

# X11 DestroyNotify, used to catch a click on the window close button.
_DESTROY_NOTIFY = 17
_STRUCTURE_NOTIFY_MASK = 1 << 17

_FOOTER_HEIGHT = 26
_MIN_SCALE = 2
_MAX_SCALE = 16
_DEFAULT_SCALE = 8

_HELP = "1: regen   2: path   3: colours   4: 42   5: save   6/Esc: quit"

# The six levels of the xterm 6x6x6 colour cube.
_CUBE_LEVELS = (0, 95, 135, 175, 215, 255)
# The sixteen basic xterm colours.
_BASE_COLOURS = (
    0x000000, 0x800000, 0x008000, 0x808000,
    0x000080, 0x800080, 0x008080, 0xC0C0C0,
    0x808080, 0xFF0000, 0x00FF00, 0xFFFF00,
    0x0000FF, 0xFF00FF, 0x00FFFF, 0xFFFFFF,
)

_BACKGROUND = 0x101014


class MlxUnavailable(Exception):
    """Raised when the MiniLibX cannot be used on this machine."""


def ansi256_to_rgb(index: int) -> int:
    """Convert an xterm 256-colour index into a ``0xRRGGBB`` value.

    The terminal renderer and the graphical one share the same
    :class:`~amazeing.render.Theme` objects, so the colours have to be
    translated from the palette used by the ANSI escape sequences.

    Args:
        index: A colour index between 0 and 255.

    Returns:
        The matching 24 bit RGB colour.
    """
    if index < 16:
        return _BASE_COLOURS[index]
    if index < 232:
        offset = index - 16
        red = _CUBE_LEVELS[offset // 36]
        green = _CUBE_LEVELS[(offset // 6) % 6]
        blue = _CUBE_LEVELS[offset % 6]
        return (red << 16) | (green << 8) | blue
    grey = 8 + 10 * (index - 232)
    return (grey << 16) | (grey << 8) | grey


def load_mlx() -> Any:
    """Import the MiniLibX wrapper.

    Returns:
        The ``mlx.Mlx`` class.

    Raises:
        MlxUnavailable: If the package or its shared library is missing.
    """
    try:
        from mlx import Mlx
    except ImportError as error:
        raise MlxUnavailable(
            "the 'mlx' package is not installed "
            f"(pip install mlx-2.2-py3-none-any.whl): {error}"
        ) from None
    except OSError as error:
        raise MlxUnavailable(
            f"the MiniLibX shared library cannot be loaded: {error}"
        ) from None
    return Mlx


class MlxViewer:
    """Display a maze in a MiniLibX window and handle the key events."""

    def __init__(
        self,
        session: Session,
        mlx_factory: Optional[Callable[[], Any]] = None,
        scale: Optional[int] = None,
    ) -> None:
        """Prepare a viewer for ``session``.

        Args:
            session: The session holding the maze and the display options.
            mlx_factory: Callable returning a MiniLibX instance; the real
                ``mlx.Mlx`` class is used by default.  Injecting a double
                here is what makes the viewer testable without a display.
            scale: Size in pixels of a half-cell; computed from the screen
                size when omitted.
        """
        self.session = session
        self._factory: Callable[[], Any] = (
            mlx_factory if mlx_factory is not None else load_mlx()
        )
        self._wanted_scale = scale
        self.mlx: Any = None
        self.mlx_ptr: Any = None
        self.win_ptr: Any = None
        self.img_ptr: Any = None
        self.scale = _DEFAULT_SCALE
        self.running = False
        self._buffer: Any = None
        self._bytes_per_pixel = 4
        self._size_line = 0

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------
    @property
    def canvas_cols(self) -> int:
        """Number of half-cells of the canvas, horizontally."""
        return 2 * self.session.generator.width + 1

    @property
    def canvas_rows(self) -> int:
        """Number of half-cells of the canvas, vertically."""
        return 2 * self.session.generator.height + 1

    @property
    def image_width(self) -> int:
        """Width of the maze image, in pixels."""
        return self.canvas_cols * self.scale

    @property
    def image_height(self) -> int:
        """Height of the maze image, in pixels."""
        return self.canvas_rows * self.scale

    def _pick_scale(self) -> int:
        """Choose the biggest half-cell size fitting on the screen."""
        if self._wanted_scale is not None:
            return max(1, self._wanted_scale)
        try:
            _, screen_w, screen_h = self.mlx.mlx_get_screen_size(self.mlx_ptr)
        except Exception:  # noqa: BLE001 - any backend may refuse this
            return _DEFAULT_SCALE
        if not screen_w or not screen_h:
            return _DEFAULT_SCALE
        usable_h = int(screen_h) - _FOOTER_HEIGHT - 80
        scale = min(
            (int(screen_w) - 40) // self.canvas_cols,
            usable_h // self.canvas_rows,
        )
        return max(_MIN_SCALE, min(_MAX_SCALE, scale))

    # ------------------------------------------------------------------
    # Colours
    # ------------------------------------------------------------------
    def _palette(self) -> Dict[Token, int]:
        """Map every canvas token to a 24 bit RGB colour."""
        theme: Theme = self.session.theme
        pattern = (
            theme.pattern if self.session.pattern_colour else theme.wall
        )
        return {
            Token.VOID: _BACKGROUND,
            Token.WALL: ansi256_to_rgb(theme.wall),
            Token.PATTERN: ansi256_to_rgb(pattern),
            Token.PATH: ansi256_to_rgb(theme.path),
            Token.ENTRY: ansi256_to_rgb(theme.entry),
            Token.EXIT: ansi256_to_rgb(theme.exit),
        }

    def _pixel_bytes(self, colour: int) -> bytes:
        """Encode a colour the way the MiniLibX image expects it."""
        return colour.to_bytes(4, sys.byteorder)[: self._bytes_per_pixel]

    # ------------------------------------------------------------------
    # Window life cycle
    # ------------------------------------------------------------------
    def open(self) -> None:
        """Create the window and the image.

        Raises:
            MlxUnavailable: If the display or the image cannot be created.
        """
        self.mlx = self._factory()
        self.mlx_ptr = self.mlx.mlx_init()
        if not self.mlx_ptr:
            raise MlxUnavailable(
                "mlx_init() failed: no display available "
                "(is DISPLAY set?)"
            )
        self.scale = self._pick_scale()
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr,
            self.image_width,
            self.image_height + _FOOTER_HEIGHT,
            "A-Maze-ing",
        )
        if not self.win_ptr:
            raise MlxUnavailable("mlx_new_window() failed")
        self._new_image()

    def _new_image(self) -> None:
        """Allocate the image the maze is drawn into.

        Raises:
            MlxUnavailable: If the image cannot be created.
        """
        self.img_ptr = self.mlx.mlx_new_image(
            self.mlx_ptr, self.image_width, self.image_height
        )
        if not self.img_ptr:
            raise MlxUnavailable("mlx_new_image() failed")
        buffer, bits_per_pixel, size_line, _ = self.mlx.mlx_get_data_addr(
            self.img_ptr
        )
        self._buffer = buffer
        self._bytes_per_pixel = max(1, int(bits_per_pixel) // 8)
        self._size_line = int(size_line)

    def close(self) -> None:
        """Destroy the image and the window, and leave the main loop."""
        if self.mlx is None:
            return
        try:
            if self.img_ptr:
                self.mlx.mlx_destroy_image(self.mlx_ptr, self.img_ptr)
                self.img_ptr = None
            if self.win_ptr:
                self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
                self.win_ptr = None
            self.mlx.mlx_loop_exit(self.mlx_ptr)
        except Exception as error:  # noqa: BLE001 - never die while closing
            print(f"Warning: MiniLibX cleanup failed: {error}",
                  file=sys.stderr)
        self.running = False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def build_rows(self) -> List[bytes]:
        """Render the maze into one packed pixel row per canvas row.

        Returns:
            ``canvas_rows`` byte strings, each holding ``image_width``
            pixels ready to be copied into the MiniLibX image.
        """
        canvas = Canvas(self.session.generator)
        canvas.paint_pattern()
        if self.session.show_path:
            canvas.paint_path(self.session.generator.solution)
        canvas.paint_endpoints()
        palette = self._palette()
        cache = {
            token: self._pixel_bytes(colour) * self.scale
            for token, colour in palette.items()
        }
        return [
            b"".join(cache[token] for token in row) for row in canvas.cells
        ]

    def draw(self) -> None:
        """Redraw the maze and push it to the window."""
        rows = self.build_rows()
        stride = self._size_line or self.image_width * self._bytes_per_pixel
        for canvas_y, packed in enumerate(rows):
            top = canvas_y * self.scale
            for repeat in range(self.scale):
                start = (top + repeat) * stride
                self._buffer[start:start + len(packed)] = packed
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._draw_footer()

    def _draw_footer(self) -> None:
        """Write the help line and the maze statistics under the maze."""
        white = 0xFFFFFF
        grey = 0x9AA0A6
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr, 8, self.image_height + 10,
            white, _HELP,
        )
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr, 8, self.image_height + 22,
            grey, self.session.status(),
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_key(self, keycode: int, param: Any = None) -> None:
        """Handle a key press.

        Args:
            keycode: The X11 keysym reported by the MiniLibX.
            param: The user pointer given to ``mlx_key_hook``, unused.

        Note:
            This runs as a C callback: an exception escaping here would be
            swallowed by ctypes, so everything is caught and reported.
        """
        try:
            self._dispatch(keycode)
        except Exception as error:  # noqa: BLE001 - keep the window alive
            print(f"Error: {error}", file=sys.stderr)

    def _dispatch(self, keycode: int) -> None:
        """Apply the action bound to ``keycode``, then redraw."""
        session = self.session
        if keycode in (KEY_QUIT, KEY_Q, KEY_ESCAPE):
            self.close()
            return
        if keycode == KEY_REGENERATE:
            try:
                session.regenerate()
            except MazeError as error:
                print(f"Error: {error}", file=sys.stderr)
                return
        elif keycode == KEY_PATH:
            session.toggle_path()
        elif keycode == KEY_COLOURS:
            session.next_theme()
        elif keycode == KEY_PATTERN:
            session.toggle_pattern_colour()
        elif keycode == KEY_SAVE:
            session.save()
            return
        else:
            return
        self.draw()

    def on_close(self, param: Any = None) -> None:
        """Handle a click on the window close button."""
        self.close()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Open the window, draw the maze and loop until the user quits.

        Raises:
            MlxUnavailable: If the window cannot be opened.
        """
        self.open()
        print(f"MiniLibX window -- {_HELP}")
        self.draw()
        self.mlx.mlx_key_hook(self.win_ptr, self.on_key, None)
        self.mlx.mlx_hook(
            self.win_ptr,
            _DESTROY_NOTIFY,
            _STRUCTURE_NOTIFY_MASK,
            self.on_close,
            None,
        )
        self.running = True
        try:
            self.mlx.mlx_loop(self.mlx_ptr)
        except KeyboardInterrupt:
            self.close()
        finally:
            self.running = False


def show_in_window(
    session: Session,
    mlx_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Display ``session`` in a MiniLibX window.

    Args:
        session: The session holding the maze and the display options.
        mlx_factory: Callable returning a MiniLibX instance, for tests.

    Raises:
        MlxUnavailable: If the MiniLibX cannot be used.
    """
    MlxViewer(session, mlx_factory=mlx_factory).run()
