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

    # 3) Fondo global (mosaico o degradado)
    bg_path = resource_path("src/background.jpg")
    if os.path.exists(bg_path):
        # ----- usar la imagen en mosaico -----
        bg_path_css = bg_path.replace("\\", "/")
        bg_rule = f"""
            QMainWindow, QWidget {{
                background-image: url("{bg_path_css}");
                background-repeat: repeat;        /* se repite para cubrir */
                background-position: 0 0;         /* ancla esquina superior-izq. */
            }}
        """
    else:
        # ----- degradado celeste claro → celeste más intenso -----
        bg_rule = """
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #dff3ff,   /* celeste muy claro */
                                            stop:1 #b1e0ff);  /* celeste más intenso */
            }
        """

    # 4) StyleSheet global  (se mantiene exactamente igual, salvo bg_rule al inicio)
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
        /* === Pestañas Verticales (QTabWidget) === */

        /* Define el borde izquierdo del panel, contra el que se "fusionan" las pestañas */
        QTabWidget::pane:west {{
            border-left: 2px solid #bbb;
            background-color: rgba(255, 255, 255, 0.8);
        }}

        /* ════════════════════════════════════════════════════════════════
   PESTAÑAS VERTICALES (QTabWidget + QTabBar) – PyQt5 compatibles
   ════════════════════════════════════════════════════════════════ */

        /* Pane lateral (la zona gris clara que envuelve las pestañas) */
        QTabWidget::pane:west {{
        border-left: 2px solid #bbb;
        background-color: rgba(255,255,255,0.8);
        }}

        /* Barra de pestañas (contenedor) */
        QTabBar:west {{
        background: transparent;   /* evita tapar colores de las tabs */
        border: none;
        }}

        /* ─────────  Pestaña NO seleccionada  ───────── */
        QTabBar::tab:west {{
        background-color: #e0e0e0;
        color: black;
        border: 1px solid #7aa4d8;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 6px;
        padding: 6px 4px;          /* vertical | horizontal */
        /*  Ajuste de tamaño:  grosor = min-width  |  largo = min-height  */
        min-width: 36px;           /* grosor (más angosto)   */
        min-height: 120px;         /* largo vertical        */
        font-size: 9pt;
        font-weight: normal;
        }}

        

        /* ─────────  Hover (solo si NO está seleccionada)  ───────── */
        QTabBar::tab:west:!selected:hover {{
        background-color: #c9dbff;
        border: 1px solid #5c8fd6;
        color: black;
        }}

        /* ─────────  Pestaña seleccionada  ───────── */
        QTabBar::tab:west:selected {{
        background-color: #3399FF;   /* azul visible */
        color: white;
        border: 2px solid #0067c2;
        font-weight: bold;
        }}

        /*  ALTERNATIVA EXTRA:
        Si en algunos temas no toma “:west:selected”, Qt acepta la
        forma genérica sin el “west”. La dejamos por compatibilidad.  */
        QTabBar::tab:selected {{
        background-color: #3399FF;
        color: white;
        border: 2px solid #0067c2;
        }}

        
        /* ══ Botón DESCARGAR (icono) ══ */
        #btnDescargar {{
        background: transparent;          /* sin fondo ni borde               */
        border: none;
        padding: 0;                       /* el icono define el tamaño        */
        }}

        #btnDescargar:hover {{
        background: rgba(0, 0, 0, 0.10);  /* leve realce al pasar el mouse    */
        border-radius: 4px;
        }}

        #btnDescargar:pressed {{
        background: rgba(0, 0, 0, 0.18);  /* un poco más oscuro al presionar  */
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
            font-size: 12px;      /* texto más grande */
            background: transparent;  /* ← elimina cualquier rectángulo de fondo */     
        }}

        /* ═══════════  SCROLLBARS MODERNOS  ═══════════ */

/* ——— Pista (fondo) ——— */
QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;        /* deja ver el fondo/degradado */
    border: none;
    margin: 0px;
}}

/* ——— Handle (la parte que se mueve) ——— */
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: rgba(0, 0, 0, 80);   /* gris translúcido */
    min-height: 40px;                      /* alto mínimo */
    min-width: 40px;                       /* ancho mínimo para horiz. */
    border-radius: 8px;                    /* esquinas redondeadas */
}}

/* ——— Hover / presionado ——— */
QScrollBar::handle:hover,
QScrollBar::handle:pressed {{
    background-color: rgba(0, 0, 0, 130);  /* un poco más oscuro */
}}

/* ——— Flechas y espacios extremos ocultos ——— */
QScrollBar::sub-line,
QScrollBar::add-line,
QScrollBar::sub-page,
QScrollBar::add-page {{
    background: none;
    width: 0px;
    height: 0px;
}}

/* ——— Ejemplo para afectar solo barras de tablas ———
QTableWidget QScrollBar {{ … }}
———————————————————————————————————————————— */

/* Íconos más chicos solo en la pestaña “Prest Requeridas”
   (3.ª pestaña contando desde 0) */
QTabWidget::pane > QWidget:nth-child(3) QToolButton {{
    icon-size: 40px 40px;
}}


    """)


    