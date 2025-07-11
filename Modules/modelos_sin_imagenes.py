#!/usr/bin/env python
# coding: utf-8
"""
Odontograma sin imágenes – versión optimizada.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Tuple, cast

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QBrush, QFont, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

# Configuración y mapeos
from Modules.utils import (
    ESTADOS_POR_NUM,
    PROTESIS_SHORT,
    TEETH_ROWS,
    Y_POSITIONS,
    TOOTH_SIZE,
    TOOTH_MARGIN,
    FACE_MAP,
)

# Paleta gráfica
from Modules.style_models import (
    BLUE, YELLOW, WHITE, BLACK,
    RED, DARK_GRAY, DARK_YELLOW,
    BLUE_PEN, YELLOW_PEN, DOT_BLUE_PEN, BRIDGE_PEN,
    WHITE_BRUSH, BLUE_BRUSH, YELLOW_BRUSH, TRANSPARENT_BRUSH,
)

# ─────────────────────────────────────────────────────────────
# Cara individual
# ─────────────────────────────────────────────────────────────
class ToothFacePolygon(QGraphicsPolygonItem):
    _selected: bool

    def __init__(self, pts: List[Tuple[float, float]], parent: "ToothItem") -> None:
        super().__init__(QPolygonF([QPointF(x, y) for x, y in pts]))
        self.tooth = parent
        self.setBrush(WHITE_BRUSH)
        self.setPen(QPen(BLACK, 2))
        self._selected = False

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

    def _toggle_obturation(self) -> None:
        self._selected = not self._selected
        self.setBrush(BLUE_BRUSH if self._selected else WHITE_BRUSH)

# ─────────────────────────────────────────────────────────────
# Pieza dental completa
# ─────────────────────────────────────────────────────────────
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
        self._scene = scene
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
            self._scene.addItem(face)

    # ----------------------- overlays ----------------------
    def _create_overlays(self, x: int, y: int, s: int) -> None:
        ln1 = cast(QGraphicsLineItem, self._scene.addLine(x, y, x + s, y + s, BLUE_PEN))
        ln2 = cast(QGraphicsLineItem, self._scene.addLine(x + s, y, x, y + s, BLUE_PEN))
        self.cross_lines: List[QGraphicsLineItem] = [ln1, ln2]
        for ln in self.cross_lines:
            ln.setVisible(False)

        r = s * 1.1
        self.corona = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - r / 2, y + s / 2 - r / 2, r, r, BLUE_PEN, TRANSPARENT_BRUSH
            ),
        )
        self.corona.setVisible(False)

        self.implante = cast(QGraphicsTextItem, self._scene.addText("IMP", QFont("Arial", 10, QFont.Bold)))
        self.implante.setDefaultTextColor(BLACK)
        self.implante.setPos(x + 5, y + 5)
        self.implante.setVisible(False)

        sr = s * 0.2
        self.sellador = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - sr / 2, y + s / 2 - sr / 2, sr, sr, YELLOW_PEN, YELLOW_BRUSH
            ),
        )
        self.sellador.setVisible(False)

        self.ausente_fisio = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - s / 2, y + s / 2 - s / 2, s, s, DOT_BLUE_PEN, TRANSPARENT_BRUSH
            ),
        )
        self.ausente_fisio.setVisible(False)

        self.protesis = cast(QGraphicsTextItem, self._scene.addText("", QFont("Arial", 12, QFont.Bold)))
        self.protesis.setDefaultTextColor(RED)
        self.protesis.setVisible(False)

        sup_r = s * 0.4
        cx, cy = x + s / 2 - sup_r / 2, y + s / 2 - sup_r / 2
        self.super_num_circ = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(cx, cy, sup_r, sup_r, BLUE_PEN, TRANSPARENT_BRUSH),
        )
        self.super_num_circ.setVisible(False)
        self.super_num_text = cast(QGraphicsTextItem, self._scene.addText("S", QFont("Arial", 12, QFont.Bold)))
        self.super_num_text.setDefaultTextColor(BLACK)
        self.super_num_text.setPos(
            cx + sup_r / 2 - self.super_num_text.boundingRect().width() / 2,
            cy + sup_r / 2 - self.super_num_text.boundingRect().height() / 2,
        )
        self.super_num_text.setVisible(False)

    # ------------------ métodos de estado -------------------
    def apply_state(self, name: str) -> None:
        if name == "Obturacion":
            for face in self.faces.values():
                face.setBrush(BLUE_BRUSH)
            return

        if name in PROTESIS_SHORT:
            self._set_protesis_text(PROTESIS_SHORT[name])
            return

        handlers: Dict[str, Callable[[], None]] = {
            "Ninguno":              self.reset,
            "Agenesia":             lambda: self._shade_all(DARK_GRAY),
            "PD Ausente":           lambda: self._set_lines(True),
            "Corona":               lambda: self.corona.setVisible(True),
            "Implante":             lambda: self.implante.setVisible(True),
            "Selladores":           lambda: self.sellador.setVisible(True),
            "Ausente Fisiológico":  lambda: self.ausente_fisio.setVisible(True),
            "Supernumerario":       lambda: self._toggle_super(True),
            "Puente":               self._flag_bridge,
            "Extracción":           self._apply_extraccion,
            "Caries":               lambda: self.faces["center"].setBrush(QBrush(DARK_YELLOW)),
        }
        func = handlers.get(name)
        if func:
            func()
        else:
            print(f"[WARN] Estado no manejado: {name}")

    def _apply_extraccion(self) -> None:
        self._set_lines(True)
        self._shade_all(RED)

    def apply_obturation_faces(self, faces: str) -> None:
        for c in faces.upper():
            name = FACE_MAP.get(c)
            if name:
                self.faces[name].setBrush(BLUE_BRUSH)

    # ------------- utilidades internas ---------------------
    def reset(self) -> None:
        self._shade_all(WHITE)
        self._set_lines(False)
        for item in (
            self.corona, self.implante, self.sellador, self.ausente_fisio,
            self.protesis, self.super_num_circ, self.super_num_text,
        ):
            item.setVisible(False)
        self.has_bridge = False

    def _shade_all(self, color) -> None:
        brush = QBrush(color)
        for face in self.faces.values():
            face.setBrush(brush)
            face.setPen(QPen(BLACK, 2))
            face._selected = False

    def _set_lines(self, visible: bool) -> None:
        for ln in self.cross_lines:
            ln.setVisible(visible)

    def _set_protesis_text(self, label: str) -> None:
        self.protesis.setPlainText(label)
        top_rect = self.faces["top"].mapToScene(
            self.faces["top"].boundingRect()
        ).boundingRect()
        tw = self.protesis.boundingRect().width()
        th = self.protesis.boundingRect().height()
        self.protesis.setPos(top_rect.center().x() - tw / 2, top_rect.top() - 5 - th)
        self.protesis.setVisible(True)

    def _toggle_super(self, enabled: bool) -> None:
        self.super_num_circ.setVisible(enabled)
        self.super_num_text.setVisible(enabled)

    def _flag_bridge(self) -> None:
        self.has_bridge = True
        self.odontogram_view.update_bridges()


# ─────────────────────────────────────────────────────────────
# Vista completa del odontograma
# ─────────────────────────────────────────────────────────────
class OdontogramView(QGraphicsView):
    def __init__(self, locked: bool = False) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.locked = locked
        self.current_state: str = "Ninguno"
        self.bridge_lines: List[QGraphicsLineItem] = []
        self.dientes: List[List[ToothItem]] = []
        self._create_teeth()

    # ------------------------------------------------------
    def _create_teeth(self) -> None:
        size, margin = TOOTH_SIZE, TOOTH_MARGIN
        width_row1 = len(TEETH_ROWS[0]) * (size + margin) - margin
        width_row2 = len(TEETH_ROWS[1]) * (size + margin) - margin
        width_row3 = len(TEETH_ROWS[2]) * (size + margin) - margin
        offset2 = (width_row1 - width_row2) // 2
        offset3 = (width_row1 - width_row3) // 2

        for idx, row in enumerate(TEETH_ROWS):
            y = Y_POSITIONS[idx]
            x_start = 50 + (offset2 if idx == 1 else offset3 if idx == 2 else 0)
            t_row: List[ToothItem] = []
            for i, num in enumerate(row):
                x = x_start + i * (size + margin)
                t = ToothItem(x, y, size, self._scene, self, num)
                t_row.append(t)
                txt = cast(QGraphicsTextItem, self._scene.addText(num, QFont("Arial", 10)))
                txt.setDefaultTextColor(BLACK)
                txt.setPos(
                    x + size / 2 - txt.boundingRect().width() / 2,
                    y + size + 3
                )
            self.dientes.append(t_row)

    # ------------------------------------------------------
    def set_current_state(self, name: str) -> None:
        self.current_state = name

    # ------------------------------------------------------
    def update_bridges(self) -> None:
        for ln in self.bridge_lines:
            self._scene.removeItem(ln)
        self.bridge_lines.clear()

        for row in self.dientes:
            for tooth in row:
                if tooth.has_bridge:
                    rect = tooth.faces["top"].mapToScene(
                        tooth.faces["top"].boundingRect()
                    ).boundingRect()
                    y_line = rect.center().y() + tooth.size / 2 - 10
                    x_left, x_right = rect.left() - 5, rect.right() + 5
                    ln = cast(
                        QGraphicsLineItem,
                        self._scene.addLine(x_left, y_line, x_right, y_line, BRIDGE_PEN),
                    )
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
            if tooth is None:
                print(f"[WARN] Pieza {dnum} no encontrada")
                continue
            per_tooth[str(dnum)].append((name, faces))

        for row in self.dientes:
            for t in row:
                t.reset()

        for num, lst in per_tooth.items():
            t = self.find_tooth(num)
            assert t is not None   # para Pylance
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
