#!/usr/bin/env python
# coding: utf-8
# Styles/style.py
"""
Módulo de estilo para la aplicación Odontograma.

Define una hoja de estilos (QSS) para dar un aspecto moderno y profesional
a todos los componentes de la interfaz de usuario.
"""
from PyQt5.QtWidgets import QApplication

# --- PALETA DEL HEADER (TEMA OSCURO) ---
# VALORES MODIFICADOS para un header más claro
HEADER_BACKGROUND = "#8c98b4"  # Un gris oscuro, pero más claro que el anterior
HEADER_FOREGROUND = "#b3c7eb"  # Nord Snow Storm (texto claro)
HEADER_BORDER = "#5e6c80"      # Borde sutilmente más claro que el nuevo fondo

# --- PALETA PRINCIPAL (TEMA CELESTE-GRIS CLARO) ---
LIGHT_BACKGROUND = "#f0f8ff"   # AliceBlue: Un blanco con un toque muy sutil de celeste
LIGHT_SURFACE = "#e6eaf0"      # Gris azulado claro para superficies
LIGHT_FOREGROUND = "#212121"   # Gris muy oscuro (casi negro) para texto
LIGHT_BORDER = "#d0d5db"       # Borde gris azulado
LIGHT_ACCENT = "#4682b4"       # SteelBlue: Un azul más sobrio para acentos
LIGHT_ACCENT_HOVER = "#3a6a94"  # Azul más oscuro para efecto hover


def apply_style(app: QApplication) -> None:
    """
    Aplica una hoja de estilos QSS global a la aplicación.
    """
    STYLESHEET = f"""
        /* ------------------- ESTILO GENERAL (TEMA CLARO) ------------------- */
        QWidget {{
            font-family: "Segoe UI", "Calibri", "Arial", sans-serif;
            font-size: 11pt;
            color: {LIGHT_FOREGROUND};
            background-color: {LIGHT_BACKGROUND};
        }}

        QMainWindow, QTabWidget::pane {{
            background-color: {LIGHT_BACKGROUND};
            border: none;
        }}

        /* ------------------- HEADER (EXCEPCIÓN CON TEMA OSCURO) ------------------- */
        QFrame#headerFrame {{
            background-color: {HEADER_BACKGROUND};
            border-radius: 8px;
            padding: 15px;
            border: 1px solid {HEADER_BORDER};
        }}

        QFrame#headerFrame QLabel {{
            background-color: transparent;
            color: {HEADER_FOREGROUND};
            font-weight: bold;
        }}

        /* ------------------- PESTAÑAS (TABS) ------------------- */
        QTabWidget::pane {{
            border-top: 1px solid {LIGHT_BORDER};
        }}

        QTabBar::tab:west {{
            background-color: transparent;
            color: {LIGHT_FOREGROUND};
            border: 1px solid transparent;
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
            padding: 10px 6px;
            min-width: 30px;
        }}

        QTabBar::tab:west:hover {{
            background-color: {LIGHT_SURFACE};
        }}

        QTabBar::tab:west:selected {{
            background-color: {LIGHT_ACCENT};
            color: white;
        }}

        /* ------------------- TABLA DE BOCAS ------------------- */
        QTableWidget {{
            background-color: white;
            border: 1px solid {LIGHT_BORDER};
            gridline-color: {LIGHT_BORDER};
            border-radius: 5px;
        }}

        QTableWidget::item {{
            padding: 5px;
            border-bottom: 1px solid {LIGHT_SURFACE};
        }}

        QTableWidget::item:selected {{
            background-color: {LIGHT_ACCENT};
            color: white;
        }}

        QHeaderView::section {{
            background-color: {LIGHT_SURFACE};
            padding: 6px;
            border: none;
            border-bottom: 1px solid {LIGHT_BORDER};
        }}

        /* ------------------- BOTONES ------------------- */
        QToolButton, QPushButton {{
            background-color: {LIGHT_SURFACE};
            border: 1px solid {LIGHT_BORDER};
            border-radius: 4px;
            padding: 5px;
            min-width: 40px;
        }}

        QToolButton:hover, QPushButton:hover {{
            background-color: {LIGHT_BORDER};
            border-color: {LIGHT_ACCENT};
        }}

        QToolButton:pressed, QPushButton:pressed {{
            background-color: {LIGHT_ACCENT_HOVER};
            color: white;
        }}

        /* Botón de descarga específico */
        QToolButton#btnDescargar {{
            background: transparent;
            border: none;
            padding: 0px;
        }}

        /* ------------------- RADIO BUTTONS (FILTROS) ------------------- */
        QRadioButton {{
            spacing: 8px;
        }}

        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 9px;
            border: 2px solid {LIGHT_BORDER};
            background-color: white;
        }}

        QRadioButton::indicator:hover {{
            border: 2px solid {LIGHT_ACCENT};
        }}

        QRadioButton::indicator:checked {{
            background-color: {LIGHT_ACCENT};
            border: 2px solid {LIGHT_ACCENT};
        }}

        /* ------------------- OTROS WIDGETS ------------------- */
        QMessageBox {{
            background-color: {LIGHT_BACKGROUND};
        }}

        QMessageBox QPushButton {{
            background-color: {LIGHT_ACCENT};
            color: white;
            padding: 8px 16px;
            min-width: 80px;
        }}

        QMessageBox QPushButton:hover {{
            background-color: {LIGHT_ACCENT_HOVER};
        }}

        /* SCROLLBARS */
        QScrollBar:vertical {{
            border: none;
            background: {LIGHT_SURFACE};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {LIGHT_BORDER};
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {LIGHT_ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            height: 0px;
            background: none;
        }}
    """
    app.setStyleSheet(STYLESHEET)