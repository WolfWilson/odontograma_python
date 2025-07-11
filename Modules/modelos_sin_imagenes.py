# Modules/modelos_sin_imagenes_optimized.py
#!/usr/bin/env python
# coding: utf-8
"""
Odontograma sin imágenes – versión optimizada.
Se evita la duplicación de items en la escena y se simplifica la creación
 de polígonos y overlays. Pensado para usarse tal cual en el proyecto
( reemplaza al antiguo `modelos_sin_imagenes.py` ).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QFont, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from Modules.utils import ESTADOS_POR_NUM  # noqa: F401


# ──────────────────────────────────────────────────────────────
# Helpers y constantes
# ──────────────────────────────────────────────────────────────
BLUE_PEN = QPen(Qt.blue, 3)
YELLOW_PEN = QPen(Qt.yellow, 2)
DOT_BLUE_PEN = QPen(Qt.blue, 2, Qt.DotLine)
BRIDGE_PEN = QPen(Qt.blue, 4)
WHITE_BRUSH = QBrush(Qt.white)
BLUE_BRUSH = QBrush(Qt.blue)
YELLOW_BRUSH = QBrush(Qt.yellow)
TRANSPARENT_BRUSH = QBrush(Qt.transparent)

# Mapeo de etiquetas reducidas para prótesis
PROTESIS_SHORT = {
    "Prótesis Removible SUPERIOR": "PRS",
    "Prótesis Removible INFERIOR": "PRI",
    "Prótesis Completa SUPERIOR": "PCS",
    "Prótesis Completa INFERIOR": "PCI",
}


# ──────────────────────────────────────────────────────────────
# Cara individual del diente
# ──────────────────────────────────────────────────────────────
class ToothFacePolygon(QGraphicsPolygonItem):
    def __init__(self, pts: List[Tuple[float, float]], parent: "ToothItem") -> None:
        super().__init__(QPolygonF([QPointF(x, y) for x, y in pts]))
        self.tooth = parent
        self.setBrush(WHITE_BRUSH)
        self.setPen(QPen(Qt.black, 2))
        self._selected = False

    # ------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore[override]
        view = self.tooth.odontogram_view
        if view.locked:
            return

        state = view.current_state
        if state == "Obturacion":
            self._toggle_obturation()
        elif state == "Puente":
            self.tooth.has_bridge = not self.tooth.has_bridge
            view.update_bridges()
        else:
            self.tooth.apply_state(state)
        super().mousePressEvent(event)

    # ------------------------------------------------------
    def _toggle_obturation(self) -> None:
        self._selected = not self._selected
        self.setBrush(BLUE_BRUSH if self._selected else WHITE_BRUSH)


# ──────────────────────────────────────────────────────────────
# Pieza dental completa
# ──────────────────────────────────────────────────────────────
class ToothItem:
    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        scene: QGraphicsScene,
        view: "OdontogramView",
        num: str,
    ) -> None:
        self.scene = scene
        self.odontogram_view = view
        self.size = size
        self.num = num
        self.has_bridge = False

        self._create_faces(x, y, size)
        self._create_overlays(x, y, size)

    # ------------------------- caras ----------------------
    def _create_faces(self, x: int, y: int, s: int) -> None:
        fs = s / 3
        pts = {
            "top":    [(x, y), (x + s, y), (x + s - fs, y + fs), (x + fs, y + fs)],
            "right":  [(x + s, y), (x + s, y + s), (x + s - fs, y + s - fs), (x + s - fs, y + fs)],
            "bottom": [(x + s, y + s), (x, y + s), (x + fs, y + s - fs), (x + s - fs, y + s - fs)],
            "left":   [(x, y + s), (x, y), (x + fs, y + fs), (x + fs, y + s - fs)],
            "center": [(x + fs, y + fs), (x + s - fs, y + fs), (x + s - fs, y + s - fs), (x + fs, y + s - fs)],
        }
        self.faces: Dict[str, ToothFacePolygon] = {
            name: ToothFacePolygon(poly, self) for name, poly in pts.items()
        }
        for face in self.faces.values():
            self.scene.addItem(face)

    # ----------------------- overlays ----------------------
    def _create_overlays(self, x: int, y: int, s: int) -> None:
        self.cross_lines: List[QGraphicsLineItem] = [
            self.scene.addLine(x, y, x + s, y + s, BLUE_PEN),
            self.scene.addLine(x + s, y, x, y + s, BLUE_PEN),
        ]
        for ln in self.cross_lines:
            ln.setVisible(False)

        # Corona
        r = s * 1.1
        self.corona = self.scene.addEllipse(
            x + s / 2 - r / 2, y + s / 2 - r / 2, r, r, BLUE_PEN, TRANSPARENT_BRUSH
        )
        self.corona.setVisible(False)

        # Implante
        self.implante = self.scene.addText("IMP", QFont("Arial", 10, QFont.Bold))
        self.implante.setDefaultTextColor(Qt.blue)
        self.implante.setPos(x + 5, y + 5)
        self.implante.setVisible(False)

        # Sellador
        sr = s * 0.2
        self.sellador = self.scene.addEllipse(
            x + s / 2 - sr / 2, y + s / 2 - sr / 2, sr, sr, YELLOW_PEN, YELLOW_BRUSH
        )
        self.sellador.setVisible(False)

        # Ausente fisiológico
        self.ausente_fisio = self.scene.addEllipse(
            x + s / 2 - s / 2, y + s / 2 - s / 2, s, s, DOT_BLUE_PEN, TRANSPARENT_BRUSH
        )
        self.ausente_fisio.setVisible(False)

        # Prótesis
        self.protesis = self.scene.addText("", QFont("Arial", 12, QFont.Bold))
        self.protesis.setDefaultTextColor(Qt.red)
        self.protesis.setVisible(False)

        # Supernumerario
        sup_r = s * 0.4
        cx, cy = x + s / 2 - sup_r / 2, y + s / 2 - sup_r / 2
        self.super_num_circ = self.scene.addEllipse(
            cx, cy, sup_r, sup_r, BLUE_PEN, TRANSPARENT_BRUSH
        )
        self.super_num_circ.setVisible(False)
        self.super_num_text = self.scene.addText("S", QFont("Arial", 12, QFont.Bold))
        self.super_num_text.setDefaultTextColor(Qt.blue)
        self.super_num_text.setPos(
            cx + sup_r / 2 - self.super_num_text.boundingRect().width() / 2,
            cy + sup_r / 2 - self.super_num_text.boundingRect().height() / 2,
        )
        self.super_num_text.setVisible(False)

    # ------------------ métodos de estado -------------------
    def apply_state(self, name: str) -> None:
        handlers = {
            "Ninguno":              self.reset,
            "Agenesia":             lambda: self._shade_all(Qt.darkGray),
            "PD Ausente":           lambda: self._set_lines(True),
            "Corona":               lambda: self.corona.setVisible(True),
            "Implante":             lambda: self.implante.setVisible(True),
            "Selladores":           lambda: self.sellador.setVisible(True),
            "Ausente Fisiológico":  lambda: self.ausente_fisio.setVisible(True),
            "Supernumerario":       lambda: self._toggle_super(True),
            "Puente":               self._flag_bridge,
            "Extracción":           lambda: [self._set_lines(True)] + [f.setBrush(QBrush(Qt.red)) for f in self.faces.values()],
            "Caries":               lambda: self.faces["center"].setBrush(QBrush(Qt.darkYellow))
        }
        if name in handlers:
            handlers[name]()
        elif name in PROTESIS_SHORT:
            self._set_protesis_text(PROTESIS_SHORT[name])
        elif name == "Obturacion":
            for face in self.faces.values():
                face.setBrush(BLUE_BRUSH)

        elif name == "Extracción":
            self.set_pd_ausente(True)
            for f in [self.top, self.right, self.bottom, self.left, self.center]:
                f.setBrush(QBrush(Qt.red))

        elif name == "Caries":
            for f in [self.center]:
                f.setBrush(QBrush(Qt.darkYellow))


    # ------------------------------------------------------
    def apply_obturation_faces(self, faces: str) -> None:
        face_map = {
            "M": "left", "D": "right", "V": "top", "B": "top",
            "L": "bottom", "P": "bottom", "I": "center", "O": "center",
        }
        for c in faces.upper():
            name = face_map.get(c)
            if name:
                self.faces[name].setBrush(BLUE_BRUSH)

    # ------------------- utilidades internas ---------------
    def reset(self) -> None:
        self._shade_all(Qt.white)
        self._set_lines(False)
        for item in (
            self.corona, self.implante, self.sellador, self.ausente_fisio,
            self.protesis, self.super_num_circ, self.super_num_text,
        ):
            item.setVisible(False)
        self.has_bridge = False

    def _shade_all(self, color: Qt.GlobalColor) -> None:
        brush = QBrush(color)
        for face in self.faces.values():
            face.setBrush(brush)
            face.setPen(QPen(Qt.black, 2))
            face._selected = False  # type: ignore[attr-defined]

    def _set_lines(self, visible: bool) -> None:
        for ln in self.cross_lines:
            ln.setVisible(visible)

    def _set_protesis_text(self, label: str) -> None:
        self.protesis.setPlainText(label)
        top_rect = self.faces["top"].mapToScene(self.faces["top"].boundingRect()).boundingRect()
        tw, th = self.protesis.boundingRect().width(), self.protesis.boundingRect().height()
        self.protesis.setPos(top_rect.center().x() - tw / 2, top_rect.top() - 5 - th)
        self.protesis.setVisible(True)

    def _toggle_super(self, enabled: bool) -> None:
        self.super_num_circ.setVisible(enabled)
        self.super_num_text.setVisible(enabled)

    def _flag_bridge(self) -> None:
        self.has_bridge = True
        self.odontogram_view.update_bridges()


# ──────────────────────────────────────────────────────────────
# Vista completa del odontograma
# ──────────────────────────────────────────────────────────────
class OdontogramView(QGraphicsView):
    def __init__(self, locked: bool = False) -> None:
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.locked = locked
        self.current_state: str = "Ninguno"
        self.bridge_lines: List = []
        self.dientes: List[List[ToothItem]] = []
        self._create_teeth()

    # ------------------------------------------------------
    def _create_teeth(self) -> None:
        size, margin = 40, 10
        rows = [
            ["18","17","16","15","14","13","12","11","21","22","23","24","25","26","27","28"],
            ["55","54","53","52","51","61","62","63","64","65"],
            ["85","84","83","82","81","71","72","73","74","75"],
            ["48","47","46","45","44","43","42","41","31","32","33","34","35","36","37","38"],
        ]
        y_positions = [50, 200, 350, 500]

        width_row1 = len(rows[0]) * (size + margin) - margin
        width_row2 = len(rows[1]) * (size + margin) - margin
        width_row3 = len(rows[2]) * (size + margin) - margin
        offset2 = (width_row1 - width_row2) // 2
        offset3 = (width_row1 - width_row3) // 2

        for idx, row in enumerate(rows):
            y = y_positions[idx]
            x_start = 50 + (offset2 if idx == 1 else offset3 if idx == 2 else 0)
            t_row: List[ToothItem] = []
            for i, num in enumerate(row):
                x = x_start + i * (size + margin)
                t = ToothItem(x, y, size, self.scene, self, num)
                t_row.append(t)
                # número bajo la pieza
                txt = self.scene.addText(num, QFont("Arial", 10))
                txt.setDefaultTextColor(Qt.black)
                txt.setPos(x + size / 2 - txt.boundingRect().width() / 2, y + size + 3)
            self.dientes.append(t_row)

    # ------------------------------------------------------
    def set_current_state(self, name: str) -> None:
        self.current_state = name

    # ------------------------------------------------------
    def update_bridges(self) -> None:
        for ln in self.bridge_lines:
            self.scene.removeItem(ln)
        self.bridge_lines.clear()

        for row in self.dientes:
            for tooth in row:
                if tooth.has_bridge:
                    rect = tooth.faces["top"].mapToScene(tooth.faces["top"].boundingRect()).boundingRect()
                    y_line = rect.center().y() + tooth.size / 2 - 10
                    x_left, x_right = rect.left() - 5, rect.right() + 5
                    ln = self.scene.addLine(x_left, y_line, x_right, y_line, BRIDGE_PEN)
                    ln.setZValue(0)
                    self.bridge_lines.append(ln)

    # ------------------------------------------------------
    def apply_batch_states(self, states: List[Tuple[int, int, str]]) -> None:
        per_tooth: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for st, dnum, faces in states:
            name = ESTADOS_POR_NUM.get(st)
            if not name:
                print(f"[WARN] Estado {st} no definido")
                continue
            tooth = self.find_tooth(str(dnum))
            if not tooth:
                print(f"[WARN] Pieza {dnum} no encontrada")
                continue
            per_tooth[str(dnum)].append((name, faces))

        # reset
        for row in self.dientes:
            for t in row:
                t.reset()

        # aplica
        for num, lst in per_tooth.items():
            t = self.find_tooth(num)
            for name, faces in lst:
                if name == "Obturacion" and faces:
                    t.apply_obturation_faces(faces)
                else:
                    t.apply_state(name)
        self.update_bridges()

    # ------------------------------------------------------
    def find_tooth(self, num: str) -> ToothItem | None:
        for row in self.dientes:
            for t in row:
                if t.num == num:
                    return t
        return None


