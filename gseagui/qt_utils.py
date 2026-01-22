from __future__ import annotations

from PyQt5.QtWidgets import QApplication


def fit_window_to_available_screen(
    window,
    desired_width: int,
    desired_height: int,
    *,
    max_ratio: float = 0.95,
) -> None:
    """Resize + center a top-level window so it never exceeds the available screen area.

    This is especially useful on HiDPI displays where hard-coded sizes can end up
    larger than the physical screen.
    """

    screen = None
    try:
        screen = window.screen()
    except Exception:
        screen = None

    if screen is None:
        screen = QApplication.primaryScreen()

    if screen is None:
        window.resize(desired_width, desired_height)
        return

    avail = screen.availableGeometry()
    max_width = max(200, int(avail.width() * max_ratio))
    max_height = max(200, int(avail.height() * max_ratio))

    target_width = min(int(desired_width), max_width)
    target_height = min(int(desired_height), max_height)

    try:
        window.setMinimumSize(
            min(window.minimumWidth(), target_width),
            min(window.minimumHeight(), target_height),
        )
    except Exception:
        pass

    window.resize(target_width, target_height)

    x = avail.x() + max(0, (avail.width() - target_width) // 2)
    y = avail.y() + max(0, (avail.height() - target_height) // 2)
    window.move(x, y)
