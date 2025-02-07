# Modules/style.py
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

def apply_style(app):
    """
    Aplica un estilo sencillo y sobrio en tonos grises claros a la aplicación.
    """
    palette = QPalette()

    # Fondo de ventana (Window)
    palette.setColor(QPalette.Window, QColor(245, 245, 245))  # gris muy claro
    palette.setColor(QPalette.WindowText, Qt.black)

    # Fondo de widgets tipo texto, editores
    palette.setColor(QPalette.Base, QColor(255, 255, 255))    # blanco
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.Text, Qt.black)

    # Tooltips
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)

    # Botones
    palette.setColor(QPalette.Button, QColor(220, 220, 220))  # gris claro
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)

    # Links o realces
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.white)

    # Asignamos la paleta al QApplication
    app.setPalette(palette)

    # Si lo deseas, también puedes cambiar el estilo base:
    # app.setStyle("Fusion")
