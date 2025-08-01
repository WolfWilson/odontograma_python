from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore    import Qt
import sys

app = QApplication(sys.argv)

w = QMainWindow()
w.setAttribute(Qt.WA_StyledBackground, True)          # <— línea clave
w.setStyleSheet("""
    QMainWindow {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 red, stop:1 yellow);   /* colores chillones */
    }
""")
w.resize(400, 300)
w.show()
sys.exit(app.exec_())
