#!/usr/bin/env python
# coding: utf-8
"""
Modules/views.py   – Ventana principal del Odontograma (versión “responsive”)

Historial de cambios clave
──────────────────────────────────────────────────────────────────────────────
• 2025-07-31:  Ventana fija 1240×700; botón de descarga animado #btnDescargar.
• 2025-08-01:  Tabla de bocas con scroll, vista de dientes máx. 600 px.
• 2025-08-01:  **NUEVO** – Escalado responsivo GLOBAL:
    – Detecta resoluciones ≤ 1366 × 768 ⇒ aplica `scale = 0.80`.
    – Se redimensiona toda la ventana, fuentes, paddings, iconos y la escena
      del odontograma (QGraphicsView) con un `QTransform.scale(...)`.
    – Factor fácilmente configurable al inicio de la clase.
Todos los comentarios originales se conservan; lo añadido se marca con “NEW”.
"""

from __future__ import annotations

import os
from typing import Any, List, Mapping, Tuple, cast

from PyQt5.QtCore    import Qt, QSize
from PyQt5.QtGui     import (
    QColor,
    QFont,
    QIcon,
    QShowEvent,
    QTransform,
    QGuiApplication,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QRadioButton,
    QButtonGroup,
    QToolButton,
)
from typing import cast  
from Modules.conexion_db   import get_bocas_consulta_efector, get_odontograma_data
from Modules.menubox_prest import (
    get_menu_existentes,
    get_menu_requeridas,
    REQUERIDAS_FULL_SET,
)
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils         import resource_path, ESTADOS_POR_NUM
from Utils.sp_data_parse   import parse_dientes_sp
from Utils.actions         import capture_odontogram
from Utils.center_window   import center_on_screen
from Styles.animation      import apply_button_colorize_animation
from Styles                import style                     # NEW – reaplica QSS escalable

# ════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    """Ventana principal con odontograma + filtros de prestaciones."""

    # ─────── Parámetros de “responsive” (editar aquí) ────────
    _LOW_RESOLUTION  = (1366, 768)   # umbral: ancho, alto
    _LOWRES_SCALE    = 0.80          # factor en pantallas pequeñas
    _HIRES_SCALE     = 1.00          # factor habitual

    # --------------------------------------------------------
    def __init__(self, data: Mapping[str, Any]) -> None:
        super().__init__()

        # ——— 1) Determinar factor de escala global ——————————
        self._scale_factor = self._compute_scale_factor()

        # ——— 2) Aplicar hoja de estilos con awareness del factor
        app_inst = cast(QApplication, QApplication.instance())
        style.apply_style(app_inst, scale=self._scale_factor)

        # ——— 3) Configurar ventana fija (dimensiones * factor) ——
        BASE_W, BASE_H = 1240, 700
        self.setWindowTitle("Odontograma – Auditoría por Prestador")
        self.setFixedSize(int(BASE_W * self._scale_factor),
                          int(BASE_H * self._scale_factor))
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)  # type: ignore[attr-defined]
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)  # type: ignore[attr-defined]

        # —— estado interno ——
        self.locked = bool(data.get("locked", False))
        self.current_idboca: int | None = None
        self.raw_states: List[Tuple[int, int, str]] = []

        # —— icono ——
        ico = resource_path("src/icon.png")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        # —— Vista odontograma (QGraphicsView) ——
        self.odontogram_view = OdontogramView(locked=self.locked)
        self._apply_scale_to_view()                                        # NEW
        self.odontogram_view.setStyleSheet("background: transparent;")
        self.odontogram_view.setFrameShape(QFrame.NoFrame)
        self.odontogram_view.setMaximumHeight(int(600 * self._scale_factor))  # NEW

        # —— Encabezado ——
        self._build_header()

        # —— Datos iniciales ——
        filas_bocas = self._get_bocas(data)

        # —— Tabs + radios ——
        self.tabs = self._build_tabs(filas_bocas)
        self.tabs.setFixedWidth(int(320 * self._scale_factor))             # NEW
        self.grp_filtro = self._build_filter_radios()

        # —— Botón descargar ——
        btn_download = QToolButton(self)
        btn_download.setObjectName("btnDescargar")
        btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_download.setToolTip("Descargar captura")

        ico_save = resource_path("src/save-file.png")
        if os.path.exists(ico_save):
            size = int(35 * self._scale_factor)                            # NEW
            btn_download.setIcon(QIcon(ico_save))
            btn_download.setIconSize(QSize(size, size))
        else:
            btn_download.setText("💾")

        btn_download.clicked.connect(self._do_download)
        apply_button_colorize_animation(btn_download)

        # —— Layout canvas + botón ——
        odo_box = QVBoxLayout()
        odo_box.setContentsMargins(0, 0, 0, 0)
        odo_box.setSpacing(4)
        odo_box.addWidget(self.odontogram_view, 1)
        odo_box.addStretch()
        odo_box.addWidget(
            btn_download, alignment=Qt.AlignRight | Qt.AlignBottom  # type: ignore[attr-defined]
        )
        odo_container = QWidget()
        odo_container.setLayout(odo_box)

        # —— Sidebar ——
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(6)
        sidebar.addWidget(self.grp_filtro)
        sidebar.addWidget(self.tabs)
        sidebar.addStretch()

        # —— Layout principal ——
        body = QHBoxLayout()
        body.addLayout(sidebar, 0)
        body.addWidget(odo_container, 1)

        root = QVBoxLayout()
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(int(8 * self._scale_factor))                       # NEW
        root.addWidget(self.header_frame)
        root.addLayout(body)

        cont = QWidget()
        cont.setLayout(root)
        self.setCentralWidget(cont)

        # —— centrar al mostrar ——
        self._centered = False
        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # ───────────────────────── utils de escala ─────────────────────────
    def _compute_scale_factor(self) -> float:
        """Devuelve 0.8 si la pantalla es ≤ 1366 × 768, si no 1.0."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            size = screen.availableGeometry().size()
            if (
                size.width() <= self._LOW_RESOLUTION[0]
                or size.height() <= self._LOW_RESOLUTION[1]
            ):
                return self._LOWRES_SCALE
        return self._HIRES_SCALE

    def _apply_scale_to_view(self) -> None:
        """Zoom proporcional al QGraphicsView (dientes, líneas, etc.)."""
        self.odontogram_view.resetTransform()
        self.odontogram_view.setTransform(
            QTransform().scale(self._scale_factor, self._scale_factor)
        )

    # ───────────────────────── HEADER ─────────────────────────
    def _build_header(self) -> None:
        base_font_pt = int(12 * self._scale_factor)                       # NEW
        bold = QFont("Segoe UI", base_font_pt, QFont.Bold)

        self.lblCredValue = self._val_lbl()
        self.lblAfilValue = self._val_lbl()
        self.lblPrestValue = self._val_lbl()
        self.lblFechaValue = self._val_lbl()
        self.lblObsValue = self._val_lbl(word_wrap=True)

        hdr = QFrame()                 # crea el widget
        hdr.setObjectName("headerFrame")   # luego asigna el objectName
        hdr.setMinimumHeight(int(100 * self._scale_factor))               # NEW

        grid = QGridLayout()
        grid.setSpacing(int(12 * self._scale_factor))                     # NEW
        for c, s in enumerate([1, 3, 1, 3]):
            grid.setColumnStretch(c, s)

        grid.addWidget(self._key("CREDENCIAL:", bold), 0, 0)
        grid.addWidget(self.lblCredValue, 0, 1)
        grid.addWidget(self._key("AFILIADO:", bold), 0, 2)
        grid.addWidget(self.lblAfilValue, 0, 3)
        grid.addWidget(self._key("PRESTADOR:", bold), 1, 0)
        grid.addWidget(self.lblPrestValue, 1, 1)
        grid.addWidget(self._key("FECHA:", bold), 1, 2)
        grid.addWidget(self.lblFechaValue, 1, 3)
        grid.addWidget(
            self._key("OBSERVACIONES:", bold), 2, 0, alignment=Qt.AlignTop  # type: ignore[attr-defined]
        )
        grid.addWidget(self.lblObsValue, 2, 1, 1, 3)

        hdr.setLayout(grid)
        self.header_frame = hdr

    def _key(self, txt: str, f: QFont) -> QLabel:
        lbl = QLabel(txt)
        lbl.setFont(f)
        lbl.setStyleSheet("color:white;")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(6)
        eff.setOffset(0, 0)
        eff.setColor(QColor(0, 0, 0, 180))
        lbl.setGraphicsEffect(eff)
        return lbl

    def _val_lbl(self, *, word_wrap=False) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet(
            "color:black; font-weight:bold; background:transparent;"
        )
        return lbl

    # ───────────────────────── TABS ──────────────────────────
    def _build_tabs(self, filas: List[dict[str, str]]) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        # — Tab de bocas —
        w_bocas = QWidget()
        self._fill_tab_bocas(w_bocas, filas)
        tabs.addTab(w_bocas, "Bocas")

        # — Tabs de prestaciones —
        tabs.addTab(get_menu_existentes(self._on_estado_clicked), "Pres Existentes")
        menu_req = get_menu_requeridas(self._on_estado_clicked)

        # Iconos de menú requeridas → escala
        from PyQt5.QtWidgets import QToolButton

        for b in menu_req.findChildren(QToolButton):
            b.setIconSize(QSize(int(25 * self._scale_factor), int(25 * self._scale_factor)))
        tabs.addTab(menu_req, "Prest Requeridas")

        return tabs

    # ─────────────────────── RADIOS ──────────────────────────
    def _build_filter_radios(self) -> QWidget:
        rb_all = QRadioButton("Todos")
        rb_all.setChecked(True)
        rb_ex = QRadioButton("Solo Existentes")
        rb_req = QRadioButton("Solo Requeridas")

        self.filter_group = QButtonGroup(self)
        for i, rb in enumerate((rb_all, rb_ex, rb_req)):
            self.filter_group.addButton(rb, i)
        self.filter_group.buttonToggled.connect(self._reapply_filter)

        box = QFrame()
        lay = QHBoxLayout(box)
        lay.setSpacing(int(6 * self._scale_factor))                        # NEW
        for rb in (rb_all, rb_ex, rb_req):
            lay.addWidget(rb)
        return box

    # ──── TAB BOCAS (16 filas máx · con scroll) ────
    def _fill_tab_bocas(self, cont: QWidget, filas: List[dict[str, str]]) -> None:
        lay = QVBoxLayout(cont)

        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca", "Fecha Carga", "Resumen Clínico"]
        )
        self.tableBocas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBocas.setSelectionMode(QTableWidget.SingleSelection)
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        self.tableBocas.currentCellChanged.connect(
            lambda r, c, *_: self._on_boca_seleccionada(r, c)
        )
        lay.addWidget(self.tableBocas)

        # — rellenar —
        self.tableBocas.setRowCount(len(filas))
        for i, d in enumerate(filas):
            self.tableBocas.setItem(i, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(i, 1, QTableWidgetItem(str(d.get("fechacarga", ""))))
            self.tableBocas.setItem(i, 2, QTableWidgetItem(str(d.get("resumenclinico", ""))))
        self.tableBocas.setColumnHidden(0, True)

        # — alto máximo (16 filas) —
        MAX_ROWS = 16
        head_h = self.tableBocas.horizontalHeader().height()  # type: ignore[attr-defined]
        rows_h = sum(
            self.tableBocas.rowHeight(i)
            for i in range(min(MAX_ROWS, self.tableBocas.rowCount()))
        )
        self.tableBocas.setMaximumHeight(
            int((head_h + rows_h + 6) * self._scale_factor)
        )                                                                   # NEW
        self.tableBocas.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)     # type: ignore[attr-defined]

    # ──────────── DATA helpers & slots ────────────
    def _get_bocas(self, data: Mapping[str, Any]) -> List[dict[str, str]]:
        filas = cast(List[dict[str, str]], data.get("filas_bocas", []))
        if filas:
            return filas
        try:
            return get_bocas_consulta_efector(
                idafiliado=str(data.get("credencial", "")),
                colegio=int(str(data.get("colegio", "0")) or 0),
                codfact=int(str(data.get("efectorCodFact", "0")) or 0),
                fecha=str(data.get("fecha", "")),
            )
        except Exception as e:
            print("[WARN] get_bocas:", e)
            return []

    def _on_boca_seleccionada(self, row: int, _col: int) -> None:
        itm = self.tableBocas.item(row, 0)
        if not (itm and itm.text().isdigit()):
            return
        self.current_idboca = int(itm.text())
        data = get_odontograma_data(self.current_idboca)

        self.lblCredValue.setText(str(data.get("credencial", "")))
        self.lblAfilValue.setText(str(data.get("afiliado", "")))
        self.lblPrestValue.setText(str(data.get("prestador", "")))
        self.lblFechaValue.setText(str(data.get("fecha", "")))
        self.lblObsValue.setText(str(data.get("observaciones", "")))

        self.raw_states = parse_dientes_sp(str(data.get("dientes", "")))
        self._reapply_filter()

    def _reapply_filter(self) -> None:
        if not self.raw_states:
            return
        mode = self.filter_group.checkedId()
        flt = (
            (lambda n: True)
            if mode == 0
            else (lambda n: ESTADOS_POR_NUM[n] not in REQUERIDAS_FULL_SET)
            if mode == 1
            else (lambda n: ESTADOS_POR_NUM[n] in REQUERIDAS_FULL_SET)
        )
        self.odontogram_view.apply_batch_states(
            [s for s in self.raw_states if flt(s[0])]
        )

    def _on_estado_clicked(self, estado: str) -> None:
        self.odontogram_view.set_current_state(estado)

    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if not path:
            return
        try:
            tag = f"{self.lblCredValue.text()}_{self.lblFechaValue.text()}"
            saved = capture_odontogram(
                self.odontogram_view, patient_name=tag, captures_dir=path
            )
            QMessageBox.information(self, "Captura guardada", saved)
        except Exception as ex:
            QMessageBox.warning(self, "Error al guardar", str(ex))

    # — centrar solo la primera vez —
    def showEvent(self, e: QShowEvent) -> None:  # type: ignore[override]
        super().showEvent(e)
        if not getattr(self, "_centered", False):
            center_on_screen(self)
            self._centered = True
