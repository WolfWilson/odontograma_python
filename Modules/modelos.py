#Modules/models.py
# coding: utf-8

from PyQt5.QtWidgets import QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QPen, QFont, QPolygonF, QPixmap
from PyQt5.QtCore import Qt, QPointF
import os

from Modules.utils import resource_path
print("El módulo modelos.py se está ejecutando")

class ToothFacePolygon(QGraphicsPolygonItem):
    """
    Clase que representa una cara (polígono) del diente.
    Maneja el clic y aplica cambios de estado si hace falta.
    """
    def __init__(self, points, parent_tooth, face_name):
        super().__init__()
        poly = QPolygonF()
        for (px, py) in points:
            poly.append(QPointF(px, py))
        self.setPolygon(poly)
        self.tooth = parent_tooth
        self.face_name = face_name
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 2))
        self.is_selected = False

    def mousePressEvent(self, event):
        """
        Dependiendo del estado actual del odontograma (self.tooth.odontogram_view.current_state_name),
        se cambia color, se marca puente, etc.
        """
        if self.tooth.odontogram_view.locked:
            return

        current_state = self.tooth.odontogram_view.current_state_name
        if current_state == "Obturacion":
            if not self.is_selected:
                self.setBrush(QBrush(Qt.blue))
                self.is_selected = True
            else:
                self.setBrush(QBrush(Qt.white))
                self.is_selected = False

        elif current_state == "Puente":
            self.tooth.has_bridge = not self.tooth.has_bridge
            self.tooth.odontogram_view.update_bridges()
        else:
            self.tooth.apply_state(current_state)

        super().mousePressEvent(event)


class ToothItem:
    """
    Clase que representa la pieza dental completa (con sus caras y overlays).
    Maneja la creación de polígonos, overlays y la aplicación de estados específicos.
    """
    def __init__(self, x, y, size, scene, odontogram_view, tooth_num):
        self.scene = scene
        self.odontogram_view = odontogram_view
        self.size = size
        self.tooth_num = tooth_num

        # Polígonos
        self.top = None
        self.right = None
        self.bottom = None
        self.left = None
        self.center = None

        # Overlays
        self.cross_lines = []
        self.corona_circle = None
        self.implante_text = None
        self.sellador_circle = None
        self.ausente_fisio_circle = None
        self.protesis_text = None
        self.supernumerario_circle = None
        self.supernumerario_text = None

        # Flag para puente
        self.has_bridge = False

        # 1) Imagen de fondo
        self.load_tooth_image(x, y, tooth_num)
        # 2) Crear polígonos
        self.create_faces(x, y, size)
        # 3) Crear overlays
        self.create_overlays(x, y, size)

    def load_tooth_image(self, x, y, tooth_num_str):
        """
        Carga la imagen del diente (si existe) y la agrega a la escena como QGraphicsPixmapItem.
        """
        image_file = f"Source/diente_{tooth_num_str}.png"
        image_path = resource_path(image_file)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pix_item = QGraphicsPixmapItem(pixmap)
                w_img = pixmap.width()
                h_img = pixmap.height()
                if w_img != self.size or h_img != self.size:
                    scale_factor = self.size / w_img
                    pix_item.setScale(scale_factor)
                pix_item.setPos(x, y)
                pix_item.setZValue(-1)
                self.scene.addItem(pix_item)

    def create_faces(self, x, y, size):
        """
        Crea los QGraphicsPolygonItem que representan cada cara (top, right, bottom, left, center).
        """
        fs = size / 3
        tl = (x,       y)
        tr = (x+size,  y)
        br = (x+size,  y+size)
        bl = (x,       y+size)
        ctl= (x+fs,       y+fs)
        ctr= (x+size-fs,  y+fs)
        cbr= (x+size-fs,  y+size-fs)
        cbl= (x+fs,       y+size-fs)

        self.top    = ToothFacePolygon([tl, tr, ctr, ctl], self, "top")
        self.right  = ToothFacePolygon([tr, br, cbr, ctr], self, "right")
        self.bottom = ToothFacePolygon([br, bl, cbl, cbr], self, "bottom")
        self.left   = ToothFacePolygon([bl, tl, ctl, cbl], self, "left")
        self.center = ToothFacePolygon([ctl, ctr, cbr, cbl], self, "center")

        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            self.scene.addItem(f)

    def create_overlays(self, x, y, size):
        """
        Crea los elementos superpuestos (líneas en X, círculos, textos, etc.) para mostrar estados especiales.
        """
        pen_b = QPen(Qt.blue, 3)

        # X para PD Ausente
        line1 = self.scene.addLine(x, y, x+size, y+size, pen_b)
        line2 = self.scene.addLine(x+size, y, x, y+size, pen_b)
        line1.setVisible(False)
        line2.setVisible(False)
        self.cross_lines = [line1, line2]

        # Corona
        r = size * 1.1
        cx = x + size / 2 - r / 2
        cy = y + size / 2 - r / 2
        self.corona_circle = self.scene.addEllipse(cx, cy, r, r, pen_b, QBrush(Qt.transparent))
        self.corona_circle.setVisible(False)

        # Implante texto
        self.implante_text = QGraphicsTextItem("IMP")
        self.implante_text.setFont(QFont("Arial", 10, QFont.Bold))
        self.implante_text.setDefaultTextColor(Qt.blue)
        self.implante_text.setPos(x + 5, y + 5)
        self.implante_text.setVisible(False)
        self.implante_text.setZValue(1)

        # Sellador
        srad = size * 0.2
        sx = x + size / 2 - srad / 2
        sy = y + size / 2 - srad / 2
        pen_y = QPen(Qt.yellow, 2)
        brush_y = QBrush(Qt.yellow)
        self.sellador_circle = self.scene.addEllipse(sx, sy, srad, srad, pen_y, brush_y)
        self.sellador_circle.setVisible(False)

        # Ausente fisiológico
        dotted = QPen(Qt.blue, 2, Qt.DotLine)
        afr = size
        ax = x + size / 2 - afr / 2
        ay = y + size / 2 - afr / 2
        self.ausente_fisio_circle = self.scene.addEllipse(ax, ay, afr, afr, dotted, QBrush(Qt.transparent))
        self.ausente_fisio_circle.setVisible(False)

        # Prótesis
        self.protesis_text = QGraphicsTextItem("")
        self.protesis_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.protesis_text.setDefaultTextColor(Qt.red)
        self.protesis_text.setVisible(False)
        self.protesis_text.setZValue(1)
        self.scene.addItem(self.protesis_text)

        # Supernumerario
        sup_r = size * 0.4
        sx2 = x + size / 2 - sup_r / 2
        sy2 = y + size / 2 - sup_r / 2
        pen_b2 = QPen(Qt.blue, 2)
        self.supernumerario_circle = self.scene.addEllipse(sx2, sy2, sup_r, sup_r, pen_b2, QBrush(Qt.transparent))
        self.supernumerario_circle.setVisible(False)

        # Texto S
        s_text = QGraphicsTextItem("S")
        s_text.setFont(QFont("Arial", 12, QFont.Bold))
        s_text.setDefaultTextColor(Qt.blue)
        s_text.setPos(
            sx2 + sup_r / 2 - s_text.boundingRect().width() / 2,
            sy2 + sup_r / 2 - s_text.boundingRect().height() / 2
        )
        s_text.setVisible(False)
        s_text.setZValue(1)
        self.supernumerario_text = s_text
        self.scene.addItem(s_text)

        for ov in [line1, line2, self.corona_circle, self.implante_text,
                   self.sellador_circle, self.ausente_fisio_circle,
                   self.supernumerario_circle, s_text]:
            self.scene.addItem(ov)

    # -----------------------
    # Métodos de estado
    # -----------------------
    def apply_state(self, state_name):
        """
        Aplica un estado global al diente (Agenesia, PD Ausente, Corona, etc.)
        """
        if state_name == "Ninguno":
            self.reset_tooth()
        elif state_name == "Agenesia":
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
        elif state_name in [
            "Prótesis Removible SUPERIOR",
            "Prótesis Removible INFERIOR",
            "Prótesis Completa SUPERIOR",
            "Prótesis Completa INFERIOR",
        ]:
            self.set_protesis_text(self._short_protesis_label(state_name))
        elif state_name == "Supernumerario":
            self.set_supernumerario(True)
        elif state_name == "Obturacion":
            # Pinta todas las caras de azul
            for f in [self.top, self.right, self.bottom, self.left, self.center]:
                f.setBrush(QBrush(Qt.blue))
        elif state_name == "Puente":
            self.has_bridge = True
            self.odontogram_view.update_bridges()

    def _short_protesis_label(self, full_label):
        if full_label == "Prótesis Removible SUPERIOR": return "PRS"
        if full_label == "Prótesis Removible INFERIOR": return "PRI"
        if full_label == "Prótesis Completa SUPERIOR":  return "PCS"
        if full_label == "Prótesis Completa INFERIOR":  return "PCI"
        return ""

    def apply_obturation_faces(self, faces_str):
        """
        Aplica la obturación solo a las caras indicadas (p.ej. 'MO', 'DB', etc.)
        """
        face_map = {
            "M": self.left, "D": self.right,
            "V": self.top,  "B": self.top,
            "L": self.bottom, "P": self.bottom,
            "I": self.center, "O": self.center,
            "G": None
        }
        for c in faces_str.upper():
            poly = face_map.get(c)
            if poly:
                poly.setBrush(QBrush(Qt.blue))

    def set_agenesia(self, enabled):
        col = Qt.darkGray if enabled else Qt.white
        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            f.setBrush(QBrush(col))

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
        self.protesis_text.setPlainText(label)
        top_rect = self.top.mapToScene(self.top.boundingRect()).boundingRect()
        tw = self.protesis_text.boundingRect().width()
        th = self.protesis_text.boundingRect().height()
        cx = top_rect.center().x() - tw/2
        cy = top_rect.top() - 5 - th
        self.protesis_text.setPos(cx, cy)
        self.protesis_text.setVisible(True)

    def set_supernumerario(self, enabled):
        if enabled:
            self.supernumerario_circle.setVisible(True)
            self.supernumerario_text.setVisible(True)

    def reset_tooth(self):
        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            f.setBrush(QBrush(Qt.white))
            f.setPen(QPen(Qt.black, 2))
            f.is_selected = False
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
        self.has_bridge = False
