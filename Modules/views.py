#!/usr/bin/env python
# coding: utf-8
"""
views.py – Ventana principal del Odontograma
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping, cast

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

from Modules.conexion_db import get_bocas_consulta_efector, get_odontograma_data
from Modules.menu_estados import MenuEstados, build_icon_dict
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils import resource_path
from Utils.sp_data_parse import parse_dientes_sp
from Utils.actions import capture_odontogram, make_refresh_button


class MainWindow(QMainWindow):
    """Ventana principal."""

    # ------------------------------------------------------------------
    def __init__(self, data_dict: Mapping[str, Any]) -> None:
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")
        self.current_idboca: int | None = None

        # ---------- icono ----------
        icon_file = resource_path("src/icon.png")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))

        # ---------- vista principal ----------
        self.odontogram_view = OdontogramView(locked=False)

        # ---------- encabezado ----------
        self._build_header()

        # ---------- datos de bocas ----------
        filas_bocas = self._get_bocas(data_dict)

        # ---------- pestañas ----------
        self.tabs = self._build_tabs(filas_bocas)

        # ---------- botones inferiores ----------
        btn_bar = QHBoxLayout()
        btn_download = QPushButton("DESCARGAR")
        btn_download.clicked.connect(self._do_download)
        btn_refresh: QToolButton = make_refresh_button(on_click=self._do_refresh)
        btn_bar.addWidget(btn_download)
        btn_bar.addWidget(btn_refresh)
        btn_bar.addStretch()

        # ---------- layout completo ----------
        sidebar = QVBoxLayout()
        sidebar.addWidget(self.tabs)
        sidebar.addLayout(btn_bar)
        sidebar.addStretch()

        odo_layout = QVBoxLayout()
        odo_layout.addWidget(self.odontogram_view)

        body = QHBoxLayout()
        body.addLayout(sidebar, 0)
        body.addLayout(odo_layout, 1)

        root = QVBoxLayout()
        root.addWidget(self.header_frame)
        root.addLayout(body)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        # selección inicial
        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # =================================================================
    # ---------------------- HEADER -----------------------------------
    # =================================================================
    def _build_header(self) -> None:
        """Crea self.header_frame y etiquetas."""
        self.lblCredValue = self._value_lbl()
        self.lblAfilValue = self._value_lbl()
        self.lblPrestValue = self._value_lbl()
        self.lblFechaValue = self._value_lbl()
        self.lblObsValue = self._value_lbl(word_wrap=True)

        hdr = QFrame()
        hdr.setObjectName("headerFrame")
        hdr.setMinimumHeight(100)
        self.header_frame = hdr

        g = QGridLayout()
        g.setSpacing(12)
        for col, stretch in enumerate([1, 3, 1, 3]):
            g.setColumnStretch(col, stretch)

        bold = QFont("Segoe UI", 12, QFont.Bold)
        g.addWidget(self._key("CREDENCIAL:", bold), 0, 0)
        g.addWidget(self.lblCredValue, 0, 1)
        g.addWidget(self._key("AFILIADO:", bold), 0, 2)
        g.addWidget(self.lblAfilValue, 0, 3)

        g.addWidget(self._key("PRESTADOR:", bold), 1, 0)
        g.addWidget(self.lblPrestValue, 1, 1)
        g.addWidget(self._key("FECHA:", bold), 1, 2)
        g.addWidget(self.lblFechaValue, 1, 3)

        g.addWidget(self._key("OBSERVACIONES:", bold), 2, 0,
                    alignment=Qt.AlignTop)  # type: ignore[attr-defined]
        g.addWidget(self.lblObsValue, 2, 1, 1, 3)

        hdr.setLayout(g)

    def _key(self, text: str, font: QFont) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet("color:white;")
        self._shadow(lbl)
        return lbl

    def _value_lbl(self, *, word_wrap: bool = False) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;")
        return lbl

    def _shadow(self, lbl: QLabel) -> None:
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(6)
        sh.setOffset(0, 0)
        sh.setColor(QColor(0, 0, 0, 180))
        lbl.setGraphicsEffect(sh)

    # =================================================================
    # -------------------------- TABS ---------------------------------
    # =================================================================
    def _build_tabs(self, filas_bocas: List[Dict[str, str]]) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        # bocas
        w_bocas = QWidget()
        self._fill_tab_bocas(w_bocas, filas_bocas)
        tabs.addTab(w_bocas, "Bocas Disponibles")

        # EXISTENTES (prótesis rojas)
        icon_exist = build_icon_dict(
            prosthesis_suffix="R",
            exclude={"Supernumerario", "Caries", "Extracción"},
        )
        tabs.addTab(
            MenuEstados(self._on_estado_clicked,
                        locked=False,
                        title="Prestaciones Existentes",
                        icon_dict=icon_exist),
            "Pres Existentes",
        )

        # REQUERIDAS (prótesis azules, sufijo A) – sólo prótesis + caries/extracción
        icon_req = build_icon_dict(
            prosthesis_suffix="A",
            include=[
                "Caries", "Extracción",
                "Prótesis Removible SUPERIOR", "Prótesis Removible INFERIOR",
                "Prótesis Completa SUPERIOR",  "Prótesis Completa INFERIOR",
            ],
        )
        tabs.addTab(
            MenuEstados(self._on_estado_clicked,
                        locked=False,
                        title="Prestaciones Requeridas",
                        icon_dict=icon_req),
            "Prest Requeridas",
        )
        return tabs

    # ---------------------- tabla de bocas ---------------------------
    def _fill_tab_bocas(self, container: QWidget, filas: List[Dict[str, str]]) -> None:
        layout = QVBoxLayout(container)
        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca", "Fecha Carga", "Resumen Clínico"]
        )
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        layout.addWidget(self.tableBocas)

        self.tableBocas.setRowCount(len(filas))
        for i, d in enumerate(filas):
            self.tableBocas.setItem(i, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(i, 1, QTableWidgetItem(str(d.get("fechacarga", ""))))
            self.tableBocas.setItem(i, 2, QTableWidgetItem(str(d.get("resumenclinico", ""))))
        self.tableBocas.setColumnHidden(0, True)

    # =================================================================
    # ------------------------ DATA helpers ---------------------------
    # =================================================================
    def _get_bocas(self, data: Mapping[str, Any]) -> List[Dict[str, str]]:
        filas_raw = data.get("filas_bocas", [])
        filas: List[Dict[str, str]] = (
            cast(List[Dict[str, str]], filas_raw) if isinstance(filas_raw, list) else []
        )
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

    # =================================================================
    # ---------------------- EVENTOS / SLOTS --------------------------
    # =================================================================
    def _on_boca_seleccionada(self, row: int, _col: int) -> None:
        item = self.tableBocas.item(row, 0)
        if not (item and item.text().isdigit()):
            return
        self.current_idboca = int(item.text())

        data = get_odontograma_data(self.current_idboca)
        self.lblCredValue.setText(str(data.get("credencial", "")))
        self.lblAfilValue.setText(str(data.get("afiliado", "")))
        self.lblPrestValue.setText(str(data.get("prestador", "")))
        self.lblFechaValue.setText(str(data.get("fecha", "")))
        self.lblObsValue.setText(str(data.get("observaciones", "")))

        states = parse_dientes_sp(str(data.get("dientes", "")))
        self.odontogram_view.apply_batch_states(states)

    # -------------------------- callbacks ----------------------------
    def _on_estado_clicked(self, estado: str) -> None:
        self.odontogram_view.set_current_state(estado)

    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
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
            self.odontogram_view.apply_batch_states(
                parse_dientes_sp(str(data.get("dientes", ""))))
            QMessageBox.information(self, "Actualizado", "Odontograma refrescado.")
        except Exception as ex:
            QMessageBox.warning(self, "Error al refrescar", str(ex))
