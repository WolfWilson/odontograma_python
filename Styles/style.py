#!/usr/bin/env python
# coding: utf-8
"""
Styles/style.py  – Hoja QSS *escalable* para la aplicación Odontograma.

NEW 2025-08-01
• Detecta la resolución disponible y ajusta tamaños de fuente / paddings
  usando un factor `scale`, compartido con la vista principal.
• La API `apply_style(app, scale=1.0)` permite que MainWindow pase su
  propio factor; si no se proporciona, se calcula dentro del módulo.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui     import QGuiApplication


# --- PALETA DEL HEADER (IMITANDO LA IMAGEN CON DEGRADADO) ---
HEADER_GRADIENT_START = "#457aaf"
HEADER_GRADIENT_END   = "#bdd6ee"
HEADER_FOREGROUND     = "#212121"
HEADER_BORDER         = "#4a78a5"

# --- PALETA PRINCIPAL (TEMA CELESTE-GRIS) ---
LIGHT_BACKGROUND   = "#f0f8ff"
LIGHT_SURFACE      = "#e6eaf0"
LIGHT_FOREGROUND   = "#212121"
LIGHT_BORDER       = "#d0d5db"
LIGHT_ACCENT       = "#4682b4"
LIGHT_ACCENT_HOVER = "#0d3252"

# --- Resoluciones / escalado coherente con views.py --------
_LOW_RESOLUTION  = (1366, 768)
_LOWRES_SCALE    = 0.80
_HIRES_SCALE     = 1.00


def _auto_scale() -> float:
    screen = QGuiApplication.primaryScreen()
    if screen:
        sz = screen.availableGeometry().size()
        if sz.width() <= _LOW_RESOLUTION[0] or sz.height() <= _LOW_RESOLUTION[1]:
            return _LOWRES_SCALE
    return _HIRES_SCALE


def apply_style(app: QApplication | None, *, scale: float | None = None) -> None:
    """
    Aplica una hoja de estilos QSS global.
    Parámetros
    ----------
    app     : QApplication   (puede ser None si ya existe)
    scale   : float | None   factor externo; si None se autodetecta.
    """
    if app is None:
        app = QApplication.instance() # type: ignore[arg-type]
        if app is None:
            raise RuntimeError("No hay QApplication en ejecución")

    scale = scale or _auto_scale()

    # Font-sizes base según factor
    BASE_FONT   = max(8, int(11 * scale))
    SMALL_FONT  = max(7, int(9  * scale))
    TINY_FONT   = max(6, int(8  * scale))

    # Paddings
    PAD         = int(5 * scale)
    PAD_BTN     = int(8 * scale)
    TAB_PAD     = int(10 * scale)

    STYLESHEET = f"""
        /* -------- ESTILO GENERAL -------- */
        QWidget {{
            font-family: "Segoe UI", "Calibri", "Arial", sans-serif;
            font-size: {BASE_FONT}pt;
            color: {LIGHT_FOREGROUND};
            background-color: {LIGHT_BACKGROUND};
        }}

        QMainWindow, QTabWidget::pane {{
            background-color: {LIGHT_BACKGROUND};
            border: none;
        }}

        /* -------- HEADER (gradiente) -------- */
        QFrame#headerFrame {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                              stop:0 {HEADER_GRADIENT_START}, stop:1 {HEADER_GRADIENT_END});
            border-radius: 8px;
            padding: {PAD_BTN}px;
            border: 2px solid {HEADER_BORDER};
        }}
        QFrame#headerFrame QLabel {{
            background-color: transparent;
            color: {HEADER_FOREGROUND};
            font-weight: bold;
            font-size: {SMALL_FONT}pt;
        }}

        /* -------- PESTAÑAS -------- */
        QTabWidget::pane {{ border-top: 1px solid {LIGHT_BORDER}; }}
        QTabBar::tab:west {{
            background-color: transparent;
            color: {LIGHT_FOREGROUND};
            border: 1px solid transparent;
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
            padding: {TAB_PAD}px {int(6*scale)}px;
            min-width: {int(30*scale)}px;
            font-size: {SMALL_FONT}pt;
        }}
        QTabBar::tab:west:hover {{ background-color: {LIGHT_SURFACE}; color: {LIGHT_ACCENT_HOVER}; }}
        QTabBar::tab:west:selected {{
            background-color: {LIGHT_ACCENT}; color: white; font-weight: bold;
        }}

        /* -------- TABLA DE BOCAS -------- */
        QTableWidget {{
            background-color: white;
            border: 1px solid {LIGHT_BORDER};
            gridline-color: {LIGHT_BORDER};
            border-radius: 5px;
            font-size: {SMALL_FONT}pt;
        }}
        QTableWidget::item {{ padding: {PAD}px; border-bottom: 1px solid {LIGHT_SURFACE}; }}
        QTableWidget::item:selected {{ background-color: {LIGHT_ACCENT}; color: white; }}
        QHeaderView::section {{
            background-color: {LIGHT_SURFACE};
            padding: {int(4*scale)}px;
            font-size: {SMALL_FONT}pt;
            border: none;
            border-bottom: 1px solid {LIGHT_BORDER};
        }}

        /* -------- BOTONES -------- */
        QToolButton, QPushButton {{
            background-color: {LIGHT_SURFACE};
            border: 1px solid {LIGHT_BORDER};
            border-radius: 4px;
            padding: {PAD}px;
            min-width: {int(40*scale)}px;
            font-size: {TINY_FONT}pt;
        }}
        QToolButton:hover, QPushButton:hover {{ background-color: {LIGHT_BORDER}; border-color: {LIGHT_ACCENT}; }}
        QToolButton:pressed, QPushButton:pressed {{ background-color: {LIGHT_ACCENT_HOVER}; color: white; }}
        QToolButton#btnDescargar {{ background: transparent; border: none; padding: 0px; }}

        /* -------- RADIOBUTTONS -------- */
        QRadioButton {{ spacing: {int(8*scale)}px; background-color: transparent; }}
        QRadioButton::indicator {{
            width: {int(16*scale)}px; height: {int(16*scale)}px;
            border-radius: 9px; border: 2px solid {LIGHT_BORDER}; background-color: white;
        }}
        QRadioButton::indicator:hover    {{ border: 2px solid {LIGHT_ACCENT}; }}
        QRadioButton::indicator:checked  {{ background-color: {LIGHT_ACCENT}; border: 2px solid {LIGHT_ACCENT}; }}

        /* -------- QMessageBox -------- */
        QMessageBox QPushButton {{
            background-color: {LIGHT_ACCENT}; color: white;
            padding: {PAD_BTN}px {int(16*scale)}px; min-width: {int(80*scale)}px;
        }}
        QMessageBox QPushButton:hover {{ background-color: {LIGHT_ACCENT_HOVER}; }}

        /* -------- SCROLLBARS -------- */
        QScrollBar:vertical {{
            background: {LIGHT_SURFACE}; width: {int(12*scale)}px; margin: 0px; border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {LIGHT_BORDER}; min-height: {int(20*scale)}px; border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {LIGHT_ACCENT}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}
    """

    app.setStyleSheet(STYLESHEET)
