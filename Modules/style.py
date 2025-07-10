#!/usr/bin/env python
# coding: utf-8
"""
Estilos globales de la aplicación.

apply_style(app):
    · Tema Fusion + paleta clara personalizada
    · StyleSheet global con:
        - Botones genéricos
        - Encabezado #headerFrame moderno
        - Fondo con imagen degradada (src/background.jpg) si existe
"""
from __future__ import annotations

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

from Modules.utils import resource_path


# ──────────────────────────────────────────────────────────────
def apply_style(app) -> None:  # noqa: ANN001 – tipo QtApp depende del main
    # 1) Tema Fusion
    app.setStyle("Fusion")

    # 2) Paleta base (gris claro, buen contraste modo claro/oscuro)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.WindowText, QColor("black"))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.Text, QColor("black"))
    palette.setColor(QPalette.ToolTipBase, QColor("black"))
    palette.setColor(QPalette.ToolTipText, QColor("white"))
    palette.setColor(QPalette.Button, QColor(220, 220, 220))
    palette.setColor(QPalette.ButtonText, QColor("black"))
    palette.setColor(QPalette.BrightText, QColor("red"))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(palette)

    # 3) StyleSheet global --------------------------------------------------
    bg_path = resource_path("src/background.jpg")
    bg_rule = ""
    if os.path.exists(bg_path):
        bg_path = bg_path.replace("\\", "/")
        bg_rule = f"""
            QMainWindow, QWidget {{
                background-image: url("{bg_path}");
                background-repeat: no-repeat;
                background-position: center;
            }}
        """

    app.setStyleSheet(f"""
        /* === Fondo global === */
        {bg_rule}

        /* === Etiquetas por defecto === */
        QLabel {{
            font-weight: bold;
        }}

        /* === Botones y toolbuttons === */
        QPushButton, QToolButton {{
            background-color: #f5f5f5;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 5px 10px;
            margin: 3px;
            min-height: 24px;
        }}
        QPushButton:hover, QToolButton:hover {{
            background-color: #e8e8e8;
        }}
        QPushButton:pressed, QToolButton:pressed {{
            background-color: #dcdcdc;
        }}
        QPushButton:checked, QToolButton:checked {{
            background-color: #66B2FF;
            color: white;
            font-weight: bold;
        }}
        /* Iconos grandes sólo en QToolButton */
        QToolButton {{ icon-size: 64px 64px; }}

        /* === Vistas y tablas translúcidas === */
        QGraphicsView,
        QPushButton, QToolButton,
        QComboBox, QSpinBox, QDoubleSpinBox,
        QPlainTextEdit, QTextEdit, QTableWidget {{
            background-color: rgba(255, 255, 255, 0.8);
        }}

        /* === Pestañas Verticales (QTabWidget) === */

        /* Define el borde izquierdo del panel, contra el que se "fusionan" las pestañas */
        QTabWidget::pane:west {{
            border-left: 2px solid #bbb;
            background-color: rgba(255, 255, 255, 0.8);
        }}

        /* Define la barra de pestañas cuando está a la izquierda */
        QTabBar:west {{
            border: none;
            background-color: rgba(255, 255, 255, 0.8);
        }}

        /* Estilo para cada pestaña individual */
        QTabBar::tab:west {{
            background: #e0e0e0;
            border: 1px solid #bbb;
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            padding: 5px 8px;
            margin-bottom: 3px;
            font-weight: bold;
            font-size: 9pt;
            min-height: 160px;
        }}

        /* Pestaña NO seleccionada cuando el mouse pasa por encima */
        QTabBar::tab:west:!selected:hover {{
            background: #d3d3d3; /* Un gris un poco más oscuro para que se note */
            border-color: #999;
        }}

        /* Pestaña seleccionada */
        QTabBar::tab:west:selected {{
            background: rgba(255, 255, 255, 0.8);
            border-right-color: transparent;
        }}

        /* === Encabezado personalizado === */
        QFrame#headerFrame {{
            background-color: #7CC8FF;
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 6px;
            padding: 12px;
        }}
        QFrame#headerFrame QLabel {{
            color: white;
            font-size: 14px;      /* texto más grande */
            background: transparent;  /* ← elimina cualquier rectángulo de fondo */     
        }}
    """)