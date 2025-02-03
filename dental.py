from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsPolygonItem, QGraphicsTextItem, QMainWindow
)
from PyQt5.QtGui import QBrush, QPen, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF

class ToothFacePolygon(QGraphicsPolygonItem):
    """Clase para representar una cara poligonal (clicable) de un diente."""
    def __init__(self, points, color=Qt.white):
        super().__init__()
        # Construimos el polígono a partir de la lista de (x, y)
        polygon = QPolygonF()
        for (px, py) in points:
            polygon.append(QPointF(px, py))

        self.setPolygon(polygon)
        self.default_color = color
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.black, 2))  # Grosor de línea
        self.is_selected = False

    def mousePressEvent(self, event):
        """Al hacer clic se alterna el color de la cara."""
        if not self.is_selected:
            self.setBrush(QBrush(Qt.yellow))
            self.is_selected = True
        else:
            self.setBrush(QBrush(self.default_color))
            self.is_selected = False
        super().mousePressEvent(event)


class ToothItem:
    """
    Un diente compuesto por 5 caras poligonales:
      - top (arriba)
      - right (derecha)
      - bottom (abajo)
      - left (izquierda)
      - center (central)
    Todas forman el “cuadrado con cuadrado interno” y diagonales a las esquinas.
    """
    def __init__(self, x, y, size, scene):
        self.scene = scene
        self.size = size
        self.create_faces(x, y, size)

    def create_faces(self, x, y, size):
        """
        Genera 5 polígonos:
          - 4 trapezoides (top, right, bottom, left)
          - 1 cuadrado central
        cuyas aristas diagonales forman la “X” interna.
        """
        face_size = size / 3

        # Esquinas exteriores del diente
        topLeft      = (x,         y)
        topRight     = (x + size,  y)
        bottomRight  = (x + size,  y + size)
        bottomLeft   = (x,         y + size)

        # Esquinas del cuadrado interno
        cTopLeft     = (x + face_size,         y + face_size)
        cTopRight    = (x + size - face_size,  y + face_size)
        cBottomRight = (x + size - face_size,  y + size - face_size)
        cBottomLeft  = (x + face_size,         y + size - face_size)

        # Cara superior
        top_face_points = [ topLeft, topRight, cTopRight, cTopLeft ]
        self.top = ToothFacePolygon(top_face_points)
        self.scene.addItem(self.top)

        # Cara derecha
        right_face_points = [ topRight, bottomRight, cBottomRight, cTopRight ]
        self.right = ToothFacePolygon(right_face_points)
        self.scene.addItem(self.right)

        # Cara inferior
        bottom_face_points = [ bottomRight, bottomLeft, cBottomLeft, cBottomRight ]
        self.bottom = ToothFacePolygon(bottom_face_points)
        self.scene.addItem(self.bottom)

        # Cara izquierda
        left_face_points = [ bottomLeft, topLeft, cTopLeft, cBottomLeft ]
        self.left = ToothFacePolygon(left_face_points)
        self.scene.addItem(self.left)

        # Cara central
        center_face_points = [ cTopLeft, cTopRight, cBottomRight, cBottomLeft ]
        self.center = ToothFacePolygon(center_face_points)
        self.scene.addItem(self.center)


class OdontogramView(QGraphicsView):
    """Vista que muestra todas las filas de dientes según el FDI indicado."""
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.create_teeth()

    def create_teeth(self):
        size = 40
        margin = 10
        
        # Declaramos un margen izquierdo para las filas "largas"
        x_start_long = 50
        # Y calculamos uno diferente para las filas "cortas"
        x_start_short = 50 + ((16 - 10) * (size + margin) / 2)

        row1 = ["18","17","16","15","14","13","12","11",
                "21","22","23","24","25","26","27","28"]  # 16 dientes
        row2 = ["55","54","53","52","51","61","62","63","64","65"]  # 10 dientes
        row3 = ["85","84","83","82","81","71","72","73","74","75"]  # 10 dientes
        row4 = ["48","47","46","45","44","43","42","41",
                "31","32","33","34","35","36","37","38"]  # 16 dientes

        y_positions = [50, 140, 250, 340]

        # Recorremos las filas
        for index, row in enumerate([row1, row2, row3, row4]):
            y = y_positions[index]
            
            # Decidimos si la fila es "larga" (16 dientes) o "corta" (10)
            if len(row) == 16:
                x_start = x_start_long
            else:
                x_start = x_start_short

            for i, tooth_num in enumerate(row):
                x = x_start + i * (size + margin)
                # Crear el diente poligonal
                ToothItem(x, y, size, self.scene)
                # Numeración centrada debajo
                text = QGraphicsTextItem(str(tooth_num))
                text.setFont(QFont("Arial", 10))
                text.setDefaultTextColor(Qt.black)
                text.setPos(x + size/2 - text.boundingRect().width()/2, y + size + 3)
                self.scene.addItem(text)



class MainWindow(QMainWindow):
    """Ventana principal para el odontograma."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odontograma Poligonal (FDI Completo)")
        self.setGeometry(100, 100, 1200, 600)

        self.odontogram_view = OdontogramView()
        self.setCentralWidget(self.odontogram_view)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
