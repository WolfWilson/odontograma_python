#!/usr/bin/env python
# coding: utf-8
"""
Modules/modelos_sin_imagenes.py

Odontograma sin imágenes – versión **completa y actualizada**.
· Filas centradas horizontalmente respecto al ancho máximo
· Espaciado vertical configurable con TOP_PADDING y BETWEEN_ROWS_EXTRA
· Prótesis:
    – Mantiene listas independientes de etiquetas rojas y azules
    – Nunca descarta un rótulo (acumula)
    – El bloque azul se renderiza siempre por encima del rojo
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

# Configuración y mapeos -------------------------------------------------------
from Modules.utils import (
    ESTADOS_POR_NUM,
    PROTESIS_SHORT,
    TEETH_ROWS,
    Y_POSITIONS,
    TOOTH_SIZE,
    TOOTH_MARGIN,
    FACE_MAP,
)

# Paleta gráfica ---------------------------------------------------------------
from Styles.style_models import (
    BLUE, YELLOW, WHITE, BLACK,
    RED, DARK_GRAY,
    BLUE_PEN, YELLOW_PEN, DOT_BLUE_PEN, BRIDGE_PEN,
    WHITE_BRUSH, BLUE_BRUSH, YELLOW_BRUSH, TRANSPARENT_BRUSH,
)

# -------- pinceles / bolígrafos auxiliares ------------------------------------
RED_BRUSH  = QBrush(RED)
RED_PEN    = QPen(RED, 2)
DOT_RED_PEN = QPen(RED, 2, Qt.DotLine)                    # type: ignore[attr-defined]
RED_BRIDGE_PEN = QPen(RED, 3)

# Espaciado vertical -----------------------------------------------------------
TOP_PADDING        = -10
BETWEEN_ROWS_EXTRA = 60

# ─────────────────────────────────────────────────────────────
# Cara individual de diente
# ─────────────────────────────────────────────────────────────
class ToothFacePolygon(QGraphicsPolygonItem):
    _selected: bool

    def __init__(self, pts: List[Tuple[float, float]], parent: "ToothItem") -> None:
        super().__init__(QPolygonF([QPointF(x, y) for x, y in pts]))
        self.tooth = parent
        self.setBrush(WHITE_BRUSH)
        self.setPen(QPen(BLACK, 2))
        self._selected = False

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore[override]
        view = self.tooth.odontogram_view
        if view.locked:
            return

        state = view.current_state
        if state == "Obturacion":
            self._selected = not self._selected
            self.setBrush(BLUE_BRUSH if self._selected else WHITE_BRUSH)
        elif state == "Puente":
            self.tooth.has_bridge = not self.tooth.has_bridge
            view.update_bridges()
        else:
            self.tooth.apply_state(state)
        super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────
# Pieza dental completa
# ─────────────────────────────────────────────────────────────
class ToothItem:
    """
    Pieza dental con todas sus caras, overlays y estados.
    Soporta múltiples prótesis rojas y azules.
    """
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
        fs = s / 3  # “face size”
        pts = {
            "top":    [(x, y), (x + s, y), (x + s - fs, y + fs), (x + fs, y + fs)],
            "right":  [(x + s, y), (x + s, y + s), (x + s - fs, y + s - fs), (x + s - fs, y + fs)],
            "bottom": [(x + s, y + s), (x, y + s), (x + fs, y + s - fs), (x + s - fs, y + s - fs)],
            "left":   [(x, y + s), (x, y), (x + fs, y + fs), (x + fs, y + s - fs)],
            "center": [(x + fs, y + fs), (x + s - fs, y + fs), (x + s - fs, y + s - fs),
                       (x + fs, y + s - fs)],
        }
        self.faces: Dict[str, ToothFacePolygon] = {
            n: ToothFacePolygon(poly, self) for n, poly in pts.items()
        }
        for face in self.faces.values():
            self._scene.addItem(face)

    # ----------------------- overlays ----------------------
    def _create_overlays(self, x: int, y: int, s: int) -> None:
        # --- líneas cruzadas (por defecto azules) ------------
        ln1 = cast(QGraphicsLineItem, self._scene.addLine(x, y, x + s, y + s, BLUE_PEN))
        ln2 = cast(QGraphicsLineItem, self._scene.addLine(x + s, y, x, y + s, BLUE_PEN))
        self.cross_lines = [ln1, ln2]
        for ln in self.cross_lines:
            ln.setVisible(False)

        # --- corona -----------------------------------------
        r = s * 1.1
        self.corona = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - r / 2, y + s / 2 - r / 2, r, r, RED_PEN, TRANSPARENT_BRUSH
            ),
        )
        self.corona.setVisible(False)

        # --- implante ---------------------------------------
        self.implante = cast(QGraphicsTextItem,
                             self._scene.addText("IMP", QFont("Arial", 10, QFont.Bold)))
        self.implante.setDefaultTextColor(RED)
        self.implante.setPos(x + 5, y + 5)
        self.implante.setVisible(False)

        # --- sellador ---------------------------------------
        sr = s * 0.2
        self.sellador = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - sr / 2, y + s / 2 - sr / 2, sr, sr, RED_PEN, RED_BRUSH
            ),
        )
        self.sellador.setVisible(False)

        # --- ausente fisiológico -----------------------------
        self.ausente_fisio = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(
                x + s / 2 - s / 2, y + s / 2 - s / 2, s, s, DOT_RED_PEN, TRANSPARENT_BRUSH
            ),
        )
        self.ausente_fisio.setVisible(False)

        # --- supernumerario ---------------------------------
        sup_r = s * 0.4
        cx, cy = x + s / 2 - sup_r / 2, y + s / 2 - sup_r / 2
        self.super_num_circ = cast(
            QGraphicsEllipseItem,
            self._scene.addEllipse(cx, cy, sup_r, sup_r, BLUE_PEN, TRANSPARENT_BRUSH),
        )
        self.super_num_circ.setVisible(False)
        self.super_num_text = cast(QGraphicsTextItem,
                                   self._scene.addText("S", QFont("Arial", 12, QFont.Bold)))
        self.super_num_text.setDefaultTextColor(BLACK)
        self.super_num_text.setPos(
            cx + sup_r / 2 - self.super_num_text.boundingRect().width() / 2,
            cy + sup_r / 2 - self.super_num_text.boundingRect().height() / 2,
        )
        self.super_num_text.setVisible(False)

        # --- prótesis (dos items, listas de labels) ----------
        font = QFont("Arial", 12, QFont.Bold)
        self.item_red  = cast(QGraphicsTextItem, self._scene.addText("", font))
        self.item_red.setDefaultTextColor(RED)
        self.item_red.setZValue(2)

        self.item_blue = cast(QGraphicsTextItem, self._scene.addText("", font))
        self.item_blue.setDefaultTextColor(BLUE)
        self.item_blue.setZValue(3)

        self.labels_red:  List[str] = []
        self.labels_blue: List[str] = []

        self.item_red.setVisible(False)
        self.item_blue.setVisible(False)

    # --------------- gestión de prótesis -------------------
    def _add_protesis_label(self, label: str, *, blue: bool) -> None:
        """Añade `label` a la lista roja o azul (sin duplicados)."""
        lst = self.labels_blue if blue else self.labels_red
        if label not in lst:
            lst.append(label)
            self._render_protesis()
            print(f"[DBG]  Pieza {self.num}: +{label} ({'azul' if blue else 'roja'})")

    def _render_protesis(self) -> None:
        """Concatena y posiciona los bloques de prótesis sin solaparse."""
        txt_red  = " ".join(self.labels_red)
        txt_blue = " ".join(self.labels_blue)

        self.item_red.setPlainText(txt_red)
        self.item_blue.setPlainText(txt_blue)

        self.item_red.setVisible(bool(txt_red))
        self.item_blue.setVisible(bool(txt_blue))

        top_rect = self.faces["top"].mapToScene(
            self.faces["top"].boundingRect()).boundingRect()
        cx = top_rect.center().x()
        base_y = top_rect.top() - 5

        h_red  = self.item_red.boundingRect().height()  if txt_red else 0
        h_blue = self.item_blue.boundingRect().height() if txt_blue else 0

        if txt_red:
            w = self.item_red.boundingRect().width()
            self.item_red.setPos(cx - w / 2, base_y - h_red)

        if txt_blue:
            w = self.item_blue.boundingRect().width()
            offset = h_red + 4 if txt_red else 0
            self.item_blue.setPos(cx - w / 2,
                                  base_y - h_blue - offset)

    # -------------- métodos de estado ----------------------
    def apply_state(self, name: str, *, code: int | None = None) -> None:
        """
        Aplica un estado.
        · Prótesis → lista roja o azul (según sufijo o código).
        """
        # — obturación / caries —
        if name in ("Obturacion", "Caries"):
            brush = RED_BRUSH if name == "Obturacion" else BLUE_BRUSH
            for face in self.faces.values():
                face.setBrush(brush)
            return

        # — prótesis —
        if name in PROTESIS_SHORT:
            label = PROTESIS_SHORT[name]
            blue = name.endswith("_B") or (code is not None and 16 <= code <= 19)
            self._add_protesis_label(label, blue=blue)
            return

        # — otros estados (solo lo esencial; conserva los tuyos) —
        handlers: Dict[str, Callable[[], None]] = {
            "Ninguno":              self.reset,
            "Agenesia":             lambda: self._shade_all(DARK_GRAY),
            "PD Ausente":           lambda: self._set_lines(True, width=4),
            "Corona":               lambda: self.corona.setVisible(True),
            "Implante":             lambda: self.implante.setVisible(True),
            "Selladores":           lambda: self.sellador.setVisible(True),
            "Ausente Fisiológico":  lambda: self.ausente_fisio.setVisible(True),
            "Supernumerario":       lambda: self._toggle_super(True),
            "Puente":               self._flag_bridge,
            "Extracción":           self._apply_extraccion,
        }
        if handler := handlers.get(name):
            handler()
        else:
            print(f"[WARN] Estado no manejado: {name}")

    # --------- utilidades internas de ToothItem ------------
    def apply_obturation_faces(self, faces: str, state_name: str) -> None:
        brush = RED_BRUSH if state_name == "Obturacion" else BLUE_BRUSH
        for c in faces.upper():
            face_name = FACE_MAP.get(c)
            if face_name:
                self.faces[face_name].setBrush(brush)

    def _apply_extraccion(self) -> None:
        self._set_lines(True)

    def _shade_all(self, color) -> None:
        brush = QBrush(color)
        for f in self.faces.values():
            f.setBrush(brush)
            f.setPen(QPen(BLACK, 2))
            f._selected = False

    def _set_lines(self, visible: bool, *, width: int | None = None) -> None:
        if width is not None:
            pen = QPen(RED, width)
            for l in self.cross_lines:
                l.setPen(pen)
        for l in self.cross_lines:
            l.setVisible(visible)

    def _toggle_super(self, enabled: bool) -> None:
        self.super_num_circ.setVisible(enabled)
        self.super_num_text.setVisible(enabled)

    def _flag_bridge(self) -> None:
        self.has_bridge = True
        self.odontogram_view.update_bridges()

    def reset(self) -> None:
        """Restablece la pieza a su estado inicial."""
        self._shade_all(WHITE)
        self._set_lines(False)
        for itm in (
            self.corona, self.implante, self.sellador, self.ausente_fisio,
            self.super_num_circ, self.super_num_text,
        ):
            itm.setVisible(False)
        # prótesis
        self.labels_red.clear()
        self.labels_blue.clear()
        self._render_protesis()
        self.has_bridge = False


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

    # ------------------------ creación ---------------------
    def _create_teeth(self) -> None:
        size, margin = TOOTH_SIZE, TOOTH_MARGIN
        base_width = max(len(r) for r in TEETH_ROWS) * (size + margin) - margin
    
        for idx, row in enumerate(TEETH_ROWS):
            row_w = len(row) * (size + margin) - margin
            offset_x = (base_width - row_w) // 2
            y = Y_POSITIONS[idx] + TOP_PADDING + idx * BETWEEN_ROWS_EXTRA

            t_row: List[ToothItem] = []
            for i, num in enumerate(row):
                x = 50 + offset_x + i * (size + margin)
                t = ToothItem(x, y, size, self._scene, self, num)
                t_row.append(t)

                txt = cast(QGraphicsTextItem,
                           self._scene.addText(num, QFont("Arial", 10)))
                txt.setDefaultTextColor(BLACK)
                txt.setPos(
                    x + size / 2 - txt.boundingRect().width() / 2,
                    y + size + 3
                )
            self.dientes.append(t_row)

    # ---------------- cambio de estado actual --------------
    def set_current_state(self, name: str) -> None:
        self.current_state = name

    # ------------------------- puente ----------------------
    def update_bridges(self) -> None:
        for ln in self.bridge_lines:
            self._scene.removeItem(ln)
        self.bridge_lines.clear()

        for row in self.dientes:
            for t in row:
                if t.has_bridge:
                    rect = t.faces["top"].mapToScene(
                        t.faces["top"].boundingRect()).boundingRect()
                    y_line = rect.center().y() + t.size / 2 - 10
                    x_left, x_right = rect.left() - 5, rect.right() + 5
                    ln = cast(QGraphicsLineItem,
                              self._scene.addLine(x_left, y_line,
                                                  x_right, y_line, RED_BRIDGE_PEN))
                    ln.setZValue(0)
                    self.bridge_lines.append(ln)

    # --------------- aplicar batch de estados --------------
    def apply_batch_states(self, states: List[Tuple[int, int, str]]) -> None:
        """
        · states = [(codEstado, numPieza, caras), ...]
        """
        per_tooth: Dict[str, List[Tuple[int, str, str]]] = defaultdict(list)
        for cod, pieza, caras in states:
            nombre = ESTADOS_POR_NUM.get(cod)
            if not nombre:
                print(f"[WARN] Estado {cod} no definido")
                continue
            per_tooth[str(pieza)].append((cod, nombre, caras))

        # reset general
        for fila in self.dientes:
            for t in fila:
                t.reset()

        # aplicar
        for num, lst in per_tooth.items():
            t = self.find_tooth(num)
            if not t:
                print(f"[WARN] Pieza {num} no encontrada")
                continue
            for cod, nombre, caras in lst:
                if nombre in ("Obturacion", "Caries") and caras:
                    t.apply_obturation_faces(caras, nombre)
                else:
                    t.apply_state(nombre, code=cod)
        self.update_bridges()

    # ----------------- utilidades --------------------------
    def find_tooth(self, num: str) -> ToothItem | None:
        for row in self.dientes:
            for t in row:
                if t.num == num:
                    return t
        return None
