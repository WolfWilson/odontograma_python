#!/usr/bin/env python
# coding: utf-8

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def apply_style(app):
    """
    Estilo 'Fusion' + paleta de grises claros,
    con hojas de estilo que aumentan el tamaño de los íconos
    y la altura de los botones.
    """
    # 1) Fusion
    app.setStyle("Fusion")

    # 2) Paleta base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))  # gris muy claro
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Button, QColor(220, 220, 220))  # gris claro
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    # 3) StyleSheet
    app.setStyleSheet("""
        QLabel {
            font-weight: bold; /* Pone en negrita todas las etiquetas */
        }

        /* Botones (QPushButton, QToolButton) con fondo gris claro y borde redondo */
        QPushButton, QToolButton {
            background-color: #f5f5f5;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 5px 10px;
            margin: 3px;
            font-weight: normal;

            /* Control de altura */
            min-height: 24px;
        }

        /* Al pasar el mouse */
        QPushButton:hover, QToolButton:hover {
            background-color: #e8e8e8;
        }

        /* Al presionar */
        QPushButton:pressed, QToolButton:pressed {
            background-color: #dcdcdc;
        }

        /* Botón tipo "checked" */
        QPushButton:checked, QToolButton:checked {
            background-color: #66B2FF;
            color: white;
            font-weight: bold;
        }

        /* Solo para QToolButton: agrandar el icono */
        QToolButton {
            icon-size: 64px 64px; /* Ajusta aquí el tamaño del ícono */
        }
    """)
