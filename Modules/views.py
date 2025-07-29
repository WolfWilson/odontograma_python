#!/usr/bin/env python
# coding: utf-8
"""
views.py – Ventana principal del Odontograma

• Radial-filter: Todos / Existentes / Requeridas
• Menús de prestaciones delegados a Modules.menubox_prest
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Mapping, Tuple, cast

from PyQt5.QtCore   import Qt
from PyQt5.QtGui    import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QRadioButton, QButtonGroup,
)

from Modules.conexion_db     import get_bocas_consulta_efector, get_odontograma_data
from Modules.menubox_prest   import (
    get_menu_existentes, get_menu_requeridas, REQUERIDAS_SET,
)
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils          import resource_path, ESTADOS_POR_NUM
from Utils.sp_data_parse    import parse_dientes_sp
from Utils.actions          import capture_odontogram, make_refresh_button


# ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self, data_dict: Mapping[str, Any]) -> None:
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")
        self.current_idboca: int | None = None
        self.raw_states: List[Tuple[int, int, str]] = []

        ico = resource_path("src/icon.png")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        self.odontogram_view = OdontogramView(locked=False)
        self._build_header()
        filas_bocas = self._get_bocas(data_dict)
        self.tabs = self._build_tabs(filas_bocas)
        self.grp_filtro = self._build_filter_radios()

        # --- botón descargar + refresh ---
        btn_download = QPushButton("DESCARGAR")
        btn_download.clicked.connect(self._do_download)
        btn_bar = QHBoxLayout()
        btn_bar.addWidget(btn_download)
        btn_bar.addWidget(make_refresh_button(on_click=self._do_refresh))
        btn_bar.addStretch()

        # --- sidebar ---
        sidebar = QVBoxLayout()
        sidebar.addWidget(self.grp_filtro)
        sidebar.addWidget(self.tabs)
        sidebar.addLayout(btn_bar)
        sidebar.addStretch()

        # --- layout principal ---
        body = QHBoxLayout()
        body.addLayout(sidebar, 0)
        body.addWidget(self.odontogram_view, 1)

        root = QVBoxLayout()
        root.addWidget(self.header_frame)
        root.addLayout(body)

        container = QWidget(); container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # ───────────────── HEADER ─────────────────
    def _build_header(self) -> None:
        self.lblCredValue = self._val_lbl()
        self.lblAfilValue = self._val_lbl()
        self.lblPrestValue = self._val_lbl()
        self.lblFechaValue = self._val_lbl()
        self.lblObsValue   = self._val_lbl(word_wrap=True)

        hdr = QFrame(); hdr.setObjectName("headerFrame"); hdr.setMinimumHeight(100)
        self.header_frame = hdr

        g = QGridLayout(); g.setSpacing(12)
        for col, st in enumerate([1, 3, 1, 3]): g.setColumnStretch(col, st)
        bold = QFont("Segoe UI", 12, QFont.Bold)

        g.addWidget(self._key("CREDENCIAL:", bold), 0, 0); g.addWidget(self.lblCredValue, 0, 1)
        g.addWidget(self._key("AFILIADO:",   bold), 0, 2); g.addWidget(self.lblAfilValue, 0, 3)
        g.addWidget(self._key("PRESTADOR:",  bold), 1, 0); g.addWidget(self.lblPrestValue, 1, 1)
        g.addWidget(self._key("FECHA:",      bold), 1, 2); g.addWidget(self.lblFechaValue, 1, 3)
        g.addWidget(self._key("OBSERVACIONES:", bold),
                    2, 0, alignment=Qt.AlignTop)                  # type: ignore[arg-defined]
        g.addWidget(self.lblObsValue, 2, 1, 1, 3)
        hdr.setLayout(g)

    def _key(self, txt: str, f: QFont) -> QLabel:
        lbl = QLabel(txt); lbl.setFont(f); lbl.setStyleSheet("color:white;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(6); eff.setOffset(0, 0)
        eff.setColor(QColor(0, 0, 0, 180)); lbl.setGraphicsEffect(eff); return lbl

    def _val_lbl(self, *, word_wrap=False) -> QLabel:
        lbl = QLabel(); lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;"); return lbl

    # ───────────────── TABS ─────────────────
    def _build_tabs(self, filas_bocas: List[Dict[str, str]]) -> QTabWidget:
        tabs = QTabWidget(); tabs.setTabPosition(QTabWidget.West)

        w_bocas = QWidget(); self._fill_tab_bocas(w_bocas, filas_bocas)
        tabs.addTab(w_bocas, "Bocas Disponibles")

        tabs.addTab(get_menu_existentes(self._on_estado_clicked), "Pres Existentes")
        tabs.addTab(get_menu_requeridas(self._on_estado_clicked), "Prest Requeridas")
        return tabs

    # ──────────────── FILTER RADIOS ─────────
    def _build_filter_radios(self) -> QWidget:
        rb_all, rb_ex, rb_req = QRadioButton("Todos"), QRadioButton("Solo Existentes"), QRadioButton("Solo Requeridas")
        rb_all.setChecked(True)
        self.filter_group = QButtonGroup(self)
        for i, rb in enumerate((rb_all, rb_ex, rb_req)): self.filter_group.addButton(rb, i)
        self.filter_group.buttonToggled.connect(self._reapply_filter)
        box = QFrame(); lay = QHBoxLayout(box); [lay.addWidget(rb) for rb in (rb_all, rb_ex, rb_req)]
        return box

    # ───────────────── BOCAS TAB ────────────
    def _fill_tab_bocas(self, cont: QWidget, filas: List[Dict[str, str]]) -> None:
        lay = QVBoxLayout(cont); self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(["idBoca", "Fecha Carga", "Resumen Clínico"])
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        lay.addWidget(self.tableBocas)
        self.tableBocas.setRowCount(len(filas))
        for i, d in enumerate(filas):
            self.tableBocas.setItem(i, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(i, 1, QTableWidgetItem(str(d.get("fechacarga", ""))))
            self.tableBocas.setItem(i, 2, QTableWidgetItem(str(d.get("resumenclinico", ""))))
        self.tableBocas.setColumnHidden(0, True)

    # ──────────────── DATA HELPERS ──────────
    def _get_bocas(self, data: Mapping[str, Any]) -> List[Dict[str, str]]:
        filas = cast(List[Dict[str, str]], data.get("filas_bocas", []))
        if filas:
            return filas
        try:
            return get_bocas_consulta_efector(
                idafiliado=str(data.get("credencial", "")),
                colegio   =int(str(data.get("colegio", "0")) or 0),
                codfact   =int(str(data.get("efectorCodFact", "0")) or 0),
                fecha     =str(data.get("fecha", "")),
            )
        except Exception as e:
            print("[WARN] No se pudo obtener bocas:", e); return []

    # ──────────────── EVENTS/SLOTS ──────────
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
        self.raw_states = parse_dientes_sp(str(data.get("dientes", "")))
        self._reapply_filter()

    # -------- filtro aplicado al canvas ----------
    def _reapply_filter(self) -> None:
        if not self.raw_states:
            return
        mode = self.filter_group.checkedId()
        if mode == 1:
            flt = lambda n: ESTADOS_POR_NUM[n] not in REQUERIDAS_SET
        elif mode == 2:
            flt = lambda n: ESTADOS_POR_NUM[n] in REQUERIDAS_SET
        else:
            flt = lambda n: True
        self.odontogram_view.apply_batch_states([s for s in self.raw_states if flt(s[0])])

    # -------- botones ----------
    def _on_estado_clicked(self, estado: str) -> None:
        self.odontogram_view.set_current_state(estado)

    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if not path:
            return
        try:
            saved = capture_odontogram(self.odontogram_view,
                                       patient_name=self.lblAfilValue.text(),
                                       captures_dir=path)
            QMessageBox.information(self, "Captura guardada", saved)
        except Exception as ex:
            QMessageBox.warning(self, "Error", str(ex))

    def _do_refresh(self) -> None:
        if self.current_idboca is None:
            return
        try:
            data = get_odontograma_data(self.current_idboca)
            self.raw_states = parse_dientes_sp(str(data.get("dientes", "")))
            self._reapply_filter()
            QMessageBox.information(self, "Actualizado", "Odontograma refrescado.")
        except Exception as ex:
            QMessageBox.warning(self, "Error al refrescar", str(ex))
