# Utils/loading_img.py
# coding: utf-8
"""
Splash animado y translúcido, reutilizable.
"""

from __future__ import annotations

from PyQt5.QtCore    import Qt, QSize, QPoint
from PyQt5.QtGui     import QMovie
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from Modules.utils import resource_path


class LoadingSplash(QWidget):
    """Ventana splash con GIF animado y (opcional) texto."""

    def __init__(
        self,
        app: QApplication,
        *,
        gif_rel_path: str,
        message: str | None = None,
        max_gif_size: QSize | None = QSize(160, 160),
    ) -> None:

        super().__init__(None)  # ← solo parent (None)

        # ► FLAGS sin marco + siempre encima
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint # type: ignore[attr-defined]
        ) # type: ignore[attr-defined]

        # ► Fondo transparente
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # ══════════════  LAYOUT  ══════════════
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ► GIF animado
        self._movie = QMovie(resource_path(gif_rel_path))
        if isinstance(max_gif_size, QSize) and not max_gif_size.isEmpty():
            self._movie.setScaledSize(max_gif_size)

        lbl_gif = QLabel()
        lbl_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_gif.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        lbl_gif.setMovie(self._movie)
        box.addWidget(lbl_gif)

        # ► Texto opcional
        if message:
            lbl_txt = QLabel(message)
            lbl_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_txt.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            lbl_txt.setStyleSheet("color:white; font-size:14pt;")
            box.addWidget(lbl_txt)

        self._movie.start()                              # ¡animación en marcha!

        # ► Centrar splash
        self.adjustSize()
        screen = app.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            self.move(center - QPoint(self.width() // 2, self.height() // 2))

    # ─────────────────────────────────────────────────────────
    def finish(self, _widget: QWidget | None = None) -> None:
        """Detiene la animación y cierra el splash."""
        self._movie.stop()
        self.close()
