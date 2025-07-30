#!/usr/bin/env python
# coding: utf-8
#Modules/views.py
"""
views.py – Ventana principal del Odontograma
· Menús de prestaciones delegados a Modules.menubox_prest
· Filtro radial:   Todos / Existentes / Requeridas
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Mapping, Tuple, cast
from PyQt5.QtCore    import Qt, QSize
from PyQt5.QtGui     import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QRadioButton, QButtonGroup,QToolButton,
)
from typing import cast
from Modules.conexion_db          import get_bocas_consulta_efector, get_odontograma_data
from Modules.menubox_prest        import (
    get_menu_existentes, get_menu_requeridas, REQUERIDAS_FULL_SET,
)
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils                import resource_path, ESTADOS_POR_NUM
from Utils.sp_data_parse          import parse_dientes_sp
from Utils.actions                import capture_odontogram   # ← refresh eliminado
from Utils.center_window import center_on_screen   # ← NUEVO
# ════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    """Ventana principal con odontograma + filtros de prestaciones."""

    # ────────────────────────────────────────────────────────────
    def __init__(self, data_dict: Mapping[str, Any]) -> None:
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")

        # ── SIN botones de minimizar / maximizar ──
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)  # type: ignore[attr-defined]
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)  # type: ignore[attr-defined]

        # --- flag de solo-lectura ---
        self.locked = bool(data_dict.get("locked", False))

        # --- estado interno ---
        self.current_idboca: int | None = None
        self.raw_states: List[Tuple[int, int, str]] = []

        # --- icono de la ventana ---
        ico = resource_path("src/icon.png")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        # --- vista odontograma ---
        self.odontogram_view = OdontogramView(locked=self.locked)
        self.odontogram_view.setStyleSheet("background: transparent;")
        self.odontogram_view.setFrameShape(QFrame.NoFrame)   # opcional

        # --- encabezado ---
        self._build_header()

        # --- filas de bocas iniciales ---
        filas_bocas = self._get_bocas(data_dict)

        # --- tabs de estados ---
        self.tabs = self._build_tabs(filas_bocas)
        self.tabs.setFixedWidth(310) 
        # --- radio-buttons de filtro ---
        self.grp_filtro = self._build_filter_radios()

        # ─────────── BOTÓN DESCARGAR ───────────
        btn_download = QPushButton("DESCARGAR")
        btn_download.setObjectName("btnDescargar")      # para el CSS
        btn_download.clicked.connect(self._do_download)

        # ─────────── CONTENEDOR ODONTOGRAMA + BOTÓN ───────────
        odo_box = QVBoxLayout()
        odo_box.addWidget(self.odontogram_view, 1)      # odontograma (expande)
        odo_box.addStretch()                            # empuja el botón abajo
        odo_box.addWidget(
            btn_download, 0,
            alignment=cast(Qt.Alignment,
                                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        )

        odo_container = QWidget()
        odo_container.setLayout(odo_box)

        # ─────────── SIDEBAR (radios + tabs) ───────────
        sidebar = QVBoxLayout()
        sidebar.addWidget(self.grp_filtro)
        sidebar.addWidget(self.tabs)
        sidebar.addStretch()

        # ─────────── LAYOUT PRINCIPAL ───────────
        body = QHBoxLayout()
        body.addLayout(sidebar, 0)
        body.addWidget(odo_container, 1)                # ← usa el nuevo contenedor

        root = QVBoxLayout()
        root.addWidget(self.header_frame)
        root.addLayout(body)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        # ventana un poco más compacta (ajusta a gusto)
        self.resize(1260, 640)

        if filas_bocas:
            self._on_boca_seleccionada(0, 0)


    # ───────────────────────── HEADER ─────────────────────────
    def _build_header(self) -> None:
        """Encabezado con datos del afiliado / prestador."""
        self.lblCredValue = self._val_lbl()
        self.lblAfilValue = self._val_lbl()
        self.lblPrestValue = self._val_lbl()
        self.lblFechaValue = self._val_lbl()
        self.lblObsValue   = self._val_lbl(word_wrap=True)

        hdr = QFrame()
        hdr.setObjectName("headerFrame")
        hdr.setMinimumHeight(100)
        self.header_frame = hdr

        g = QGridLayout(); g.setSpacing(12)
        for col, stretch in enumerate([1, 3, 1, 3]):
            g.setColumnStretch(col, stretch)

        bold = QFont("Segoe UI", 12, QFont.Bold)
        g.addWidget(self._key("CREDENCIAL:", bold), 0, 0)
        g.addWidget(self.lblCredValue,                 0, 1)
        g.addWidget(self._key("AFILIADO:",   bold),    0, 2)
        g.addWidget(self.lblAfilValue,                 0, 3)
        g.addWidget(self._key("PRESTADOR:",  bold),    1, 0)
        g.addWidget(self.lblPrestValue,                1, 1)
        g.addWidget(self._key("FECHA:",      bold),    1, 2)
        g.addWidget(self.lblFechaValue,                1, 3)
        g.addWidget(self._key("OBSERVACIONES:", bold),
            2, 0, alignment=Qt.AlignmentFlag.AlignTop)
        g.addWidget(self.lblObsValue, 2, 1, 1, 3)
        hdr.setLayout(g)
    # ───────────────────── override de showEvent ───────────────────
    def showEvent(self, event) -> None:             # type: ignore[override]
        super().showEvent(event)
        if not getattr(self, "_centered", False):   # solo la primera vez
            center_on_screen(self)
            self._centered = True

    # helpers de header -------------------------------------------------
    def _key(self, txt: str, f: QFont) -> QLabel:
        lbl = QLabel(txt)
        lbl.setFont(f)
        lbl.setStyleSheet("color:white;")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(6); eff.setOffset(0, 0)
        eff.setColor(QColor(0, 0, 0, 180))
        lbl.setGraphicsEffect(eff)
        return lbl

    def _val_lbl(self, *, word_wrap: bool = False) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;")
        return lbl

    # ────────────────────────── TABS ─────────────────────────
    def _build_tabs(self, filas_bocas: List[Dict[str, str]]) -> QTabWidget:

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        # ─── Bocas disponibles ───
        w_bocas = QWidget()
        self._fill_tab_bocas(w_bocas, filas_bocas)
        tabs.addTab(w_bocas, "Bocas Disponibles")

        # ─── Prestaciones EXISTENTES ───
        menu_ex = get_menu_existentes(self._on_estado_clicked)
        tabs.addTab(menu_ex, "Pres Existentes")

        # ─── Prestaciones REQUERIDAS ───
        menu_req = get_menu_requeridas(self._on_estado_clicked)

        # Aquí puedes personalizar **todos** los botones del menú
        for btn in menu_req.findChildren(QToolButton):
            btn.setIconSize(QSize(25, 25))              # ⇦ 1) tamaño más chico
            # ejemplo para cambiar el ícono si lo deseas:
            # if btn.toolTip() == "Caries":
            #     btn.setIcon(QIcon(resource_path("src/icon_caries_alt.png")))

        tabs.addTab(menu_req, "Prest Requeridas")

        return tabs

    # ───────────────────── FILTER RADIOS ─────────────────────
    def _build_filter_radios(self) -> QWidget:
        rb_all  = QRadioButton("Todos");     rb_all.setChecked(True)
        rb_ex   = QRadioButton("Solo Existentes")
        rb_req  = QRadioButton("Solo Requeridas")

        self.filter_group = QButtonGroup(self)
        for i, rb in enumerate((rb_all, rb_ex, rb_req)):
            self.filter_group.addButton(rb, i)
        self.filter_group.buttonToggled.connect(self._reapply_filter)

        box = QFrame(); lay = QHBoxLayout(box)
        for rb in (rb_all, rb_ex, rb_req): lay.addWidget(rb)
        return box

    # ───────────────────── TAB “BOCAS” ───────────────────────
    def _fill_tab_bocas(self, cont: QWidget, filas: List[Dict[str, str]]) -> None:
        lay = QVBoxLayout(cont)
        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca", "Fecha Carga", "Resumen Clínico"])

        # ── selección de FILAS completas ───────────────────────
        self.tableBocas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBocas.setSelectionMode(QTableWidget.SingleSelection)

        # clic con el mouse
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)

        # ⌨ flechas ↑ / ↓  → cambia celda actual
        self.tableBocas.currentCellChanged.connect(
            lambda row, col, *_: self._on_boca_seleccionada(row, col)
        )

        lay.addWidget(self.tableBocas)

        self.tableBocas.setRowCount(len(filas))
        for i, d in enumerate(filas):
            self.tableBocas.setItem(i, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(i, 1, QTableWidgetItem(str(d.get("fechacarga", ""))))
            self.tableBocas.setItem(i, 2, QTableWidgetItem(str(d.get("resumenclinico", ""))))
        self.tableBocas.setColumnHidden(0, True)


    # ──────────────────── DATA HELPERS ───────────────────────
    def _get_bocas(self, data: Mapping[str, Any]) -> List[Dict[str, str]]:
        filas = cast(List[Dict[str, str]], data.get("filas_bocas", []))
        if filas:
            return filas
        try:
            return get_bocas_consulta_efector(
                idafiliado=str(data.get("credencial", "")),
                colegio=int(str(data.get("colegio", "0")) or 0),
                codfact=int(str(data.get("efectorCodFact", "0")) or 0),
                fecha=str(data.get("fecha", "")),
            )
        except Exception as exc:
            print("[WARN] No se pudo obtener bocas:", exc)
            return []

    # ───────────────────── EVENTS / SLOTS ────────────────────
    def _on_boca_seleccionada(self, row: int, _col: int) -> None:
        itm = self.tableBocas.item(row, 0)
        if not (itm and itm.text().isdigit()):
            return
        self.current_idboca = int(itm.text())

        data = get_odontograma_data(self.current_idboca)
        self.lblCredValue.setText(str(data.get("credencial", "")))
        self.lblAfilValue .setText(str(data.get("afiliado", "")))
        self.lblPrestValue.setText(str(data.get("prestador", "")))
        self.lblFechaValue.setText(str(data.get("fecha", "")))
        self.lblObsValue  .setText(str(data.get("observaciones", "")))

        # estados brutos
        self.raw_states = parse_dientes_sp(str(data.get("dientes", "")))
        self._reapply_filter()

    # ----- FILTRO aplicado al canvas -----
    def _reapply_filter(self) -> None:
        if not self.raw_states:
            return
        mode = self.filter_group.checkedId()
        if mode == 1:        # solo EXISTENTES
            flt = lambda n: ESTADOS_POR_NUM[n] not in REQUERIDAS_FULL_SET
        elif mode == 2:      # solo REQUERIDAS
            flt = lambda n: ESTADOS_POR_NUM[n] in REQUERIDAS_FULL_SET
        else:                # TODOS
            flt = lambda n: True

        self.odontogram_view.apply_batch_states(
            [s for s in self.raw_states if flt(s[0])]
        )

    # ───────────────────── CALLBACK estado clic ─────────────────────
    def _on_estado_clicked(self, estado: str) -> None:
        """
        Recibe el nombre del estado que se hace clic en los menús de
        prestaciones y lo envía a la vista de odontograma.
        """
        self.odontogram_view.set_current_state(estado)
    

    # ----- CALLBACK estado clic -----
    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if not path:
            return
        try:
            cred  = self.lblCredValue.text()
            fecha = self.lblFechaValue.text()      # dd/mm/aaaa
            tag   = f"{cred}_{fecha}"              # «12345678_01/02/2025»

            saved = capture_odontogram(
                self.odontogram_view,
                patient_name=tag,                  # ← nuevo
                captures_dir=path,
            )
            QMessageBox.information(self, "Captura guardada", saved)
        except Exception as ex:
            QMessageBox.warning(self, "Error", str(ex))

