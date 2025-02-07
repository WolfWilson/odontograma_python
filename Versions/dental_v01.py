import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow,
    QGraphicsPolygonItem, QGraphicsTextItem, QComboBox, QVBoxLayout, QWidget
)
from PyQt5.QtGui import QBrush, QPen, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF

# --------------------------------------------------------------------
#  Diccionario de ESTADOS (incluye los anteriores + nuevos)
# --------------------------------------------------------------------
ESTADOS = {
    "Ninguno": 0,
    "Obturacion": 1,
    "Agenesia": 2,
    "PD Ausente": 3,
    "Corona": 4,
    "Implante": 5,
    "Puente": 6,
    "Selladores": 7,
    "Ausente Fisiológico": 8,
    "Prótesis Removible SUPERIOR": 9,
    "Prótesis Removible INFERIOR": 10,
    "Prótesis Completa SUPERIOR": 11,
    "Prótesis Completa INFERIOR": 12,
    "Supernumerario": 13
}

def get_tooth_definition(fdi_number: str) -> dict:
    """
    Dada la numeración FDI (por ejemplo, "11", "22", "75", "85"),
    devuelve un diccionario con la información de:
      - dentition  : "Permanente" o "Temporal"
      - arch       : "Superior" o "Inferior"
      - side       : "Derecha" o "Izquierda"
      - type       : "Incisivo", "Canino", "Premolar", "Molar"
      - faces      : lista con las caras [M, D, V, P/L, I/O, G]
      - description: texto libre (ej: "Incisivo central superior derecho")
    """
    # Parseamos el primer dígito (cuadrante) y el segundo dígito (posición)
    if len(fdi_number) != 2:
        # Caso extremo: si alguien puso "1" o "85 " con espacio...
        # se puede limpiar o manejar error. Asumimos un fallback.
        return {}

    quadrant = int(fdi_number[0])  # 1..8
    position = int(fdi_number[1])  # 1..8 (1..5 si es temporal)

    # Determinar dentición (permanente vs temporal) según cuadrante
    if 1 <= quadrant <= 4:
        dentition = "Permanente"
    else:
        dentition = "Temporal"

    # Determinar arcada (superior vs inferior) y lado (derecha vs izquierda)
    # 1 o 5 => Superior derecho
    # 2 o 6 => Superior izquierdo
    # 3 o 7 => Inferior izquierdo
    # 4 o 8 => Inferior derecho
    if quadrant in [1, 5]:
        arch = "Superior"
        side = "Derecha"
    elif quadrant in [2, 6]:
        arch = "Superior"
        side = "Izquierda"
    elif quadrant in [3, 7]:
        arch = "Inferior"
        side = "Izquierda"
    else:  # quadrant in [4, 8]
        arch = "Inferior"
        side = "Derecha"

    # Determinar tipo de diente según el "número de posición":
    # 1,2 => Incisivos, 3 => Canino, 4,5 => Premolares (solo en permanente),
    # 6,7,8 => Molares (en temporal, 4 y 5 actúan como "molares" primarios)
    if dentition == "Permanente":
        if position in [1, 2]:
            tooth_type = "Incisivo"
        elif position == 3:
            tooth_type = "Canino"
        elif position in [4, 5]:
            tooth_type = "Premolar"
        else:
            tooth_type = "Molar"
    else:
        # Dentición temporal => no hay premolares, la posición 4 y 5 son "molares temporales"
        if position in [1, 2]:
            tooth_type = "Incisivo"
        elif position == 3:
            tooth_type = "Canino"
        else:
            tooth_type = "Molar"  # 4 y 5 en temporal son molares

    # Asignamos caras según sea anterior (incisivo/canino) o posterior (premolar/molar)
    if tooth_type in ["Incisivo", "Canino"]:
        # M, D, V(labial), P/L, I, G
        if arch == "Superior":
            faces = ["M", "D", "V(labial)", "P", "I", "G"]
        else:
            faces = ["M", "D", "V(labial)", "L", "I", "G"]
    else:
        # Premolares / Molares: M, D, V(bucal), P/L, O, G
        if arch == "Superior":
            faces = ["M", "D", "V(bucal)", "P", "O", "G"]
        else:
            faces = ["M", "D", "V(bucal)", "L", "O", "G"]

    # Construimos una descripción breve
    description = f"{tooth_type} {arch} {side} ({dentition})"

    return {
        "dentition": dentition,
        "arch": arch,
        "side": side,
        "type": tooth_type,
        "faces": faces,
        "description": description
    }

class ToothFacePolygon(QGraphicsPolygonItem):
    """
    Cara poligonal de un diente.
    """
    def __init__(self, points, parent_tooth, face_name):
        super().__init__()
        polygon = QPolygonF()
        for (px, py) in points:
            polygon.append(QPointF(px, py))

        self.setPolygon(polygon)
        self.tooth = parent_tooth  # Referencia al diente
        self.face_name = face_name
        self.default_color = Qt.white
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.black, 2))
        self.is_selected = False

    def mousePressEvent(self, event):
        """
        Al hacer clic, aplicamos el estado activo del odontograma.
        - Obturación: pinta esta cara en azul.
        - Puente: especial (selecciona pilares en la vista).
        - El resto de estados se aplican al diente completo.
        """
        current_state = self.tooth.odontogram_view.current_state_name
        view = self.tooth.odontogram_view
        
        if current_state == "Obturacion":
            # Pintar en azul solo esta cara (toggle)
            if not self.is_selected:
                self.setBrush(QBrush(Qt.blue))
                self.is_selected = True
            else:
                self.setBrush(QBrush(self.default_color))
                self.is_selected = False

        elif current_state == "Puente":
            # Delegar al método de la vista para manejar la selección de pilares
            view.handle_puente_click(self.tooth)

        else:
            # El resto se aplica al diente completo
            self.tooth.apply_state(current_state)

        super().mousePressEvent(event)


class ToothItem:
    """
    Representa un diente con 5 caras poligonales y varios "overlays" para estados.
    Además, guarda en self.tooth_info la definición exacta:
      dentition, arch, side, type, faces, etc.
    """
    def __init__(self, x, y, size, scene, odontogram_view, tooth_num, row_index, col_index):
        self.scene = scene
        self.odontogram_view = odontogram_view
        self.size = size
        self.tooth_num = tooth_num
        self.row_index = row_index
        self.col_index = col_index

        # <-- NUEVO: info detallada de la pieza
        self.tooth_info = get_tooth_definition(self.tooth_num)
        # Ejemplo: self.tooth_info["faces"] => ["M","D","V(labial)","P","I","G"]

        # Referencias a las 5 caras gráficas (actualmente "top,right,bottom,left,center")
        self.top = None
        self.right = None
        self.bottom = None
        self.left = None
        self.center = None

        # Elementos gráficos extra (inicialmente ocultos)
        self.cross_lines = []         # PD Ausente
        self.corona_circle = None     # Corona
        self.implante_text = None     # "IMP"
        self.sellador_circle = None   # Círculo amarillo
        self.ausente_fisio_circle = None  # Círculo discontinuo
        self.protesis_text = None         # Texto en rojo: PRS / PRI / PCS / PCI
        self.supernumerario_circle = None # Círculo con "S"
        self.supernumerario_text = None   # "S" interna

        self.create_faces(x, y, size)
        self.create_overlays(x, y, size)

    def create_faces(self, x, y, size):
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
        self.top = ToothFacePolygon([topLeft, topRight, cTopRight, cTopLeft],
                                    self, "top")
        self.scene.addItem(self.top)

        # Cara derecha
        self.right = ToothFacePolygon([topRight, bottomRight, cBottomRight, cTopRight],
                                      self, "right")
        self.scene.addItem(self.right)

        # Cara inferior
        self.bottom = ToothFacePolygon([bottomRight, bottomLeft, cBottomLeft, cBottomRight],
                                       self, "bottom")
        self.scene.addItem(self.bottom)

        # Cara izquierda
        self.left = ToothFacePolygon([bottomLeft, topLeft, cTopLeft, cBottomLeft],
                                     self, "left")
        self.scene.addItem(self.left)

        # Cara central
        self.center = ToothFacePolygon([cTopLeft, cTopRight, cBottomRight, cBottomLeft],
                                       self, "center")
        self.scene.addItem(self.center)

    def create_overlays(self, x, y, size):
        """
        Crea (ocultos) los distintos elementos gráficos que se mostrarán
        según el estado.
        """
        pen_blue = QPen(Qt.blue, 3)

        # 1) PD Ausente - cruz
        line1 = self.scene.addLine(x, y, x + size, y + size, pen_blue)
        line2 = self.scene.addLine(x + size, y, x, y + size, pen_blue)
        line1.setVisible(False)
        line2.setVisible(False)
        self.cross_lines = [line1, line2]

        # 2) Corona - círculo grande (azul)
        radius = size * 1.1
        cx = x + size/2 - radius/2
        cy = y + size/2 - radius/2
        self.corona_circle = self.scene.addEllipse(
            cx, cy, radius, radius,
            pen_blue, QBrush(Qt.transparent)
        )
        self.corona_circle.setVisible(False)

        # 3) Implante - texto "IMP" en el centro (azul)
        self.implante_text = QGraphicsTextItem("IMP")
        self.implante_text.setFont(QFont("Arial", 10, QFont.Bold))
        self.implante_text.setDefaultTextColor(Qt.blue)
        self.center_text_item(self.implante_text, x, y, size)
        self.implante_text.setVisible(False)

        # 4) Sellador - círculo amarillo en el centro (más pequeño)
        sellador_radius = size * 0.2
        sx = x + size/2 - sellador_radius/2
        sy = y + size/2 - sellador_radius/2
        pen_yellow = QPen(Qt.yellow, 2)
        brush_yellow = QBrush(Qt.yellow)
        self.sellador_circle = self.scene.addEllipse(
            sx, sy, sellador_radius, sellador_radius,
            pen_yellow, brush_yellow
        )
        self.sellador_circle.setVisible(False)

        # 5) Ausente fisiológico - círculo discontinuo alrededor del diente
        dotted_pen = QPen(Qt.blue, 2, Qt.DotLine)
        af_radius = size * 1.0
        ax = x + size/2 - af_radius/2
        ay = y + size/2 - af_radius/2
        self.ausente_fisio_circle = self.scene.addEllipse(
            ax, ay, af_radius, af_radius,
            dotted_pen, QBrush(Qt.transparent)
        )
        self.ausente_fisio_circle.setVisible(False)

        # 6) Prótesis (Removible Sup/Inf, Completa Sup/Inf) -> texto en rojo
        self.protesis_text = QGraphicsTextItem("")  # Se asigna dinámicamente
        self.protesis_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.protesis_text.setDefaultTextColor(Qt.red)
        self.protesis_text.setPos(x, y)
        self.protesis_text.setVisible(False)

        # 7) Supernumerario -> círculo azul con 'S' azul en el centro
        sup_radius = size * 0.4
        sx2 = x + size/2 - sup_radius/2
        sy2 = y + size/2 - sup_radius/2
        pen_blue_s = QPen(Qt.blue, 2)
        brush_transp = QBrush(Qt.transparent)
        self.supernumerario_circle = self.scene.addEllipse(
            sx2, sy2, sup_radius, sup_radius,
            pen_blue_s, brush_transp
        )
        self.supernumerario_circle.setVisible(False)

        s_text = QGraphicsTextItem("S")
        s_text.setFont(QFont("Arial", 12, QFont.Bold))
        s_text.setDefaultTextColor(Qt.blue)
        s_tx = sx2 + sup_radius/2 - s_text.boundingRect().width()/2
        s_ty = sy2 + sup_radius/2 - s_text.boundingRect().height()/2
        s_text.setPos(s_tx, s_ty)
        s_text.setVisible(False)
        self.supernumerario_text = s_text

        # Agregar todo a la escena
        self.scene.addItem(self.corona_circle)
        self.scene.addItem(self.implante_text)
        self.scene.addItem(self.sellador_circle)
        self.scene.addItem(self.ausente_fisio_circle)
        self.scene.addItem(self.protesis_text)
        self.scene.addItem(self.supernumerario_circle)
        self.scene.addItem(s_text)

    def center_text_item(self, text_item, x, y, size):
        """
        Ubica un QGraphicsTextItem aproximadamente en el centro del diente (x,y,size).
        """
        cx = x + size/2
        cy = y + size/2
        text_item.setPos(
            cx - text_item.boundingRect().width()/2,
            cy - text_item.boundingRect().height()/2
        )

    # --------------------------------------------------------------------
    #  Métodos para aplicar estados a TODO el diente
    # --------------------------------------------------------------------
    def apply_state(self, state_name):
        if state_name == "Agenesia":
            self.set_agenesia(True)
        elif state_name == "PD Ausente":
            self.set_pd_ausente(True)
        elif state_name == "Corona":
            self.set_corona(True)
        elif state_name == "Implante":
            self.set_implante(True)
        elif state_name == "Selladores":
            self.set_sellador(True)
        elif state_name == "Ausente Fisiológico":
            self.set_ausente_fisio(True)
        elif state_name == "Ninguno":
            self.reset_tooth()
            return
        elif state_name == "Prótesis Removible SUPERIOR":
            self.set_protesis_text("PRS")
        elif state_name == "Prótesis Removible INFERIOR":
            self.set_protesis_text("PRI")
        elif state_name == "Prótesis Completa SUPERIOR":
            self.set_protesis_text("PCS")
        elif state_name == "Prótesis Completa INFERIOR":
            self.set_protesis_text("PCI")
        elif state_name == "Supernumerario":
            self.set_supernumerario(True)

    def set_agenesia(self, enabled):
        color = Qt.darkGray if enabled else Qt.white
        for face in [self.top, self.right, self.bottom, self.left, self.center]:
            face.setBrush(QBrush(color))

    def set_pd_ausente(self, enabled):
        for line in self.cross_lines:
            line.setVisible(enabled)

    def set_corona(self, enabled):
        if self.corona_circle:
            self.corona_circle.setVisible(enabled)

    def set_implante(self, enabled):
        if self.implante_text:
            self.implante_text.setVisible(enabled)

    def set_sellador(self, enabled):
        if self.sellador_circle:
            self.sellador_circle.setVisible(enabled)

    def set_ausente_fisio(self, enabled):
        if self.ausente_fisio_circle:
            self.ausente_fisio_circle.setVisible(enabled)

    def set_protesis_text(self, label):
        """
        Muestra el texto en rojo (PRS, PRI, PCS, PCI) **por encima** del diente.
        """
        self.reset_tooth()
        self.protesis_text.setPlainText(label)

        # Tomamos el boundingRect de la cara "top" en coordenadas de escena:
        top_scene_poly = self.top.mapToScene(self.top.boundingRect())
        top_scene_rect = top_scene_poly.boundingRect()

        text_width  = self.protesis_text.boundingRect().width()
        text_height = self.protesis_text.boundingRect().height()

        center_x = top_scene_rect.center().x() - (text_width / 2)
        # Lo colocamos un poco arriba (margen 5 px)
        text_y = top_scene_rect.top() - 5 - text_height

        self.protesis_text.setPos(center_x, text_y)
        self.protesis_text.setVisible(True)

    def set_supernumerario(self, enabled):
        self.reset_tooth()
        if enabled:
            self.supernumerario_circle.setVisible(True)
            self.supernumerario_text.setVisible(True)

    def reset_tooth(self):
        """
        Quita todos los estados: caras blancas, sin cruz, círculos, textos, etc.
        """
        for face in [self.top, self.right, self.bottom, self.left, self.center]:
            face.setBrush(QBrush(Qt.white))
            face.is_selected = False
        
        # Ocultar overlays
        for line in self.cross_lines:
            line.setVisible(False)
        if self.corona_circle:
            self.corona_circle.setVisible(False)
        if self.implante_text:
            self.implante_text.setVisible(False)
        if self.sellador_circle:
            self.sellador_circle.setVisible(False)
        if self.ausente_fisio_circle:
            self.ausente_fisio_circle.setVisible(False)
        if self.protesis_text:
            self.protesis_text.setVisible(False)
        if self.supernumerario_circle:
            self.supernumerario_circle.setVisible(False)
        if self.supernumerario_text:
            self.supernumerario_text.setVisible(False)


class OdontogramView(QGraphicsView):
    """
    Vista principal con la escena, administra el estado activo y la creación de dientes.
    """
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Estado actual (por defecto "Ninguno")
        self.current_state_name = "Ninguno"

        # Variables auxiliares para el "Puente"
        self.puente_pilar_inicial = None

        # Almacén de todos los dientes en filas
        self.dientes = []

        # Creamos las 4 filas (con sus respectivos números FDI)
        self.create_teeth()

    def create_teeth(self):
        size = 40
        margin = 10

        row1 = ["18","17","16","15","14","13","12","11",
                "21","22","23","24","25","26","27","28"]  # 16
        row2 = ["55","54","53","52","51","61","62","63","64","65"]  # 10
        row3 = ["85","84","83","82","81","71","72","73","74","75"]  # 10
        row4 = ["48","47","46","45","44","43","42","41",
                "31","32","33","34","35","36","37","38"]  # 16

        rows = [row1, row2, row3, row4]
        y_positions = [50, 140, 250, 340]

        for row_index, row in enumerate(rows):
            tooth_row = []
            y = y_positions[row_index]
            x_start = 50
            for col_index, tooth_num in enumerate(row):
                x = x_start + col_index*(size + margin)
                
                # Crear el diente
                tooth_item = ToothItem(
                    x, y, size, self.scene, self, tooth_num,
                    row_index, col_index
                )
                tooth_row.append(tooth_item)

                # Texto debajo del diente (el número)
                text = QGraphicsTextItem(tooth_num)
                text.setFont(QFont("Arial", 10))
                text.setDefaultTextColor(Qt.black)
                text.setPos(
                    x + size/2 - text.boundingRect().width()/2,
                    y + size + 3
                )
                self.scene.addItem(text)

            self.dientes.append(tooth_row)

    def set_current_state(self, state_name):
        """
        Actualiza el estado que se aplicará cuando se haga clic en un diente/cara.
        """
        self.current_state_name = state_name
        if state_name != "Puente":
            # Si cambiamos a otro estado y estábamos a medio "Puente",
            # cancelamos la selección de pilar_inicial
            self.puente_pilar_inicial = None

    # --------------------------------------------------------------------
    # Lógica para "Puente"
    # --------------------------------------------------------------------
    def handle_puente_click(self, clicked_tooth):
        """
        Si no hay pilar_inicial, lo guardamos.
        Si ya hay pilar_inicial, trazamos el puente.
        """
        if self.puente_pilar_inicial is None:
            self.puente_pilar_inicial = clicked_tooth
        else:
            pilar1 = self.puente_pilar_inicial
            pilar2 = clicked_tooth
            if pilar1.row_index == pilar2.row_index:
                # Dibujar la línea horizontal y verticales
                self.draw_bridge(pilar1, pilar2)
            else:
                print("No se puede dibujar puente entre filas distintas.")
            self.puente_pilar_inicial = None

    def draw_bridge(self, pilar1, pilar2):
        """
        Dibuja la línea horizontal uniendo pilar1 y pilar2,
        y líneas verticales en cada pilar.
        """
        if pilar1.col_index > pilar2.col_index:
            pilar1, pilar2 = pilar2, pilar1

        # Coordenadas de las caras left y right en la escena
        x_left = pilar1.left.mapToScene(pilar1.left.boundingRect().topLeft()).x()
        x_right = pilar2.right.mapToScene(pilar2.right.boundingRect().topRight()).x()

        # Y centrado en la fila
        y_row = pilar1.top.mapToScene(pilar1.top.boundingRect().topLeft()).y()
        d_size = pilar1.size
        y_center = y_row + d_size/2

        pen_bridge = QPen(Qt.blue, 3)

        # Línea horizontal
        self.scene.addLine(x_left, y_center, x_right, y_center, pen_bridge)

        # Líneas verticales en los dos pilares
        top_v = y_center - (d_size * 0.5)
        bot_v = y_center + (d_size * 0.5)
        self.scene.addLine(x_left, top_v, x_left, bot_v, pen_bridge)
        self.scene.addLine(x_right, top_v, x_right, bot_v, pen_bridge)

        print(f"Puente desde {pilar1.tooth_num} hasta {pilar2.tooth_num}")


class MainWindow(QMainWindow):
    """
    Ventana principal con la vista y el combo de estados.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odontograma - Prótesis sobre diente (texto por encima)")
        self.setGeometry(100, 100, 1400, 600)

        # Vista (QGraphicsView) con el odontograma
        self.odontogram_view = OdontogramView()

        # ComboBox para seleccionar el estado
        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)

        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.odontogram_view)
        layout.addWidget(self.state_selector)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)


# -------------------------------------------------------------
# Lanzador de la aplicación
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
