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
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from Modules.conexion_db import get_bocas_consulta_efector, get_odontograma_data
from Modules.menu_estados import MenuEstados
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils import resource_path
from Utils.sp_data_parse import parse_dientes_sp
from Utils.actions import capture_odontogram, make_refresh_button


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""

    # ------------------------------------------------------------------
    def __init__(self, data_dict: Mapping[str, Any]) -> None:   # ← Mapping, Any
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")

        # ---------- Estado interno ----------
        self.current_idboca: int | None = None

        # ---------- Icono ----------
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # ---------- Vista odontograma ----------
        self.odontogram_view = OdontogramView(locked=False)

        # ---------- Labels encabezado ----------
        self.lblCredValue = self._value_label()
        self.lblAfilValue = self._value_label()
        self.lblPrestValue = self._value_label()
        self.lblFechaValue = self._value_label()
        self.lblObsValue = self._value_label(word_wrap=True)

        header = self._build_header()

        # ---------- Bocas disponibles ----------
        filas_bocas_raw = data_dict.get("filas_bocas", [])
        filas_bocas: List[Dict[str, str]] = (
            cast(List[Dict[str, str]], filas_bocas_raw) if isinstance(filas_bocas_raw, list) else []
        )

        if not filas_bocas:
            try:
                filas_bocas = get_bocas_consulta_efector(
                    idafiliado=str(data_dict.get("credencial", "")),
                    colegio=int(str(data_dict.get("colegio", "0")) or 0),
                    codfact=int(str(data_dict.get("efectorCodFact", "0")) or 0),
                    fecha=str(data_dict.get("fecha", "")),
                )
            except Exception as exc:
                print("[WARN] No se pudo obtener bocas:", exc)

        # ---------- Pestañas ----------
        self.tabs = self._build_tabs(filas_bocas)

        # ---------- Botones ----------
        self.btn_download = QPushButton("DESCARGAR")
        self.btn_download.clicked.connect(self._do_download)

        self.btn_refresh: QToolButton = make_refresh_button(on_click=self._do_refresh)

        btn_bar = QHBoxLayout()
        btn_bar.addWidget(self.btn_download)
        btn_bar.addWidget(self.btn_refresh)
        btn_bar.addStretch()

        # ---------- Layout general ----------
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
        root.addWidget(header)
        root.addLayout(body)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        # ---------- Selección inicial ----------
        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # =================================================================
    # --------------------------- HEADER -------------------------------
    # =================================================================
    def _build_header(self) -> QFrame:
        hdr = QFrame()                  # ← antes QFrame(objectName="headerFrame")
        hdr.setObjectName("headerFrame")
        hdr.setMinimumHeight(100)

        grid = QGridLayout()            # ← antes QGridLayout(spacing=12)
        grid.setSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 3)

        font_bold = QFont("Segoe UI", 12, QFont.Bold)

        grid.addWidget(self._key("CREDENCIAL:", font_bold), 0, 0)
        grid.addWidget(self.lblCredValue, 0, 1)
        grid.addWidget(self._key("AFILIADO:", font_bold), 0, 2)
        grid.addWidget(self.lblAfilValue, 0, 3)

        grid.addWidget(self._key("PRESTADOR:", font_bold), 1, 0)
        grid.addWidget(self.lblPrestValue, 1, 1)
        grid.addWidget(self._key("FECHA:", font_bold), 1, 2)
        grid.addWidget(self.lblFechaValue, 1, 3)

        grid.addWidget(self._key("OBSERVACIONES:", font_bold), 2, 0, Qt.AlignTop)  # type: ignore[attr-defined]
        grid.addWidget(self.lblObsValue, 2, 1, 1, 3)

        hdr.setLayout(grid)
        return hdr

    def _key(self, text: str, font: QFont) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet("color:white;")
        self._add_shadow(lbl)           # ← sin cambios
        return lbl

    def _value_label(self, *, word_wrap: bool = False) -> QLabel:
        lbl = QLabel()
        lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;")
        return lbl

    def _add_shadow(self, lbl: QLabel) -> None:
        shadow = QGraphicsDropShadowEffect()  # ← antes con blurRadius kwarg
        shadow.setBlurRadius(6)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        lbl.setGraphicsEffect(shadow)

    # =================================================================
    # ---------------------------- TABS -------------------------------
    # =================================================================
    def _build_tabs(self, filas_bocas: List[Dict[str, str]]) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        # ---- Bocas disponibles --------------------------------------
        t_bocas = QWidget()
        self._build_tab_bocas(t_bocas, filas_bocas)
        tabs.addTab(t_bocas, "Bocas Disponibles")

        # ---- Prestaciones existentes --------------------------------
        tabs.addTab(
            MenuEstados(self._on_estado_clicked, locked=False, title="Prestaciones Existentes"),
            "Pres Existentes",
        )

        # ---- Prestaciones requeridas --------------------------------
        tabs.addTab(
            MenuEstados(
                self._on_estado_clicked,
                locked=False,
                title="Prestaciones Requeridas",
                estados_personalizados={
                    "Caries": "icon_cariesR.png",
                    "Extracción": "icon_extraccionR.png",
                    "Prótesis Removible SUPERIOR": "icon_prsR.png",
                    "Prótesis Removible INFERIOR": "icon_priR.png",
                    "Prótesis Completa SUPERIOR": "icon_pcsR.png",
                    "Prótesis Completa INFERIOR": "icon_pciR.png",
                },
            ),
            "Prest Requeridas",
        )
        return tabs

    def _build_tab_bocas(self, container: QWidget, filas: List[Dict[str, str]]) -> None:
        layout = QVBoxLayout()
        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca", "Fecha Carga", "Resumen Clínico"]
        )
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        layout.addWidget(self.tableBocas)
        container.setLayout(layout)

        self.tableBocas.setRowCount(len(filas))
        for i, d in enumerate(filas):
            self.tableBocas.setItem(i, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(i, 1, QTableWidgetItem(str(d.get("fechacarga", ""))))
            self.tableBocas.setItem(i, 2, QTableWidgetItem(str(d.get("resumenclinico", ""))))
        self.tableBocas.setColumnHidden(0, True)

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

        # ------------------ NUEVO parseo centralizado -----------------
        self.odontogram_view.apply_batch_states(
            parse_dientes_sp(str(data.get("dientes", "")))
        )

    def _on_estado_clicked(self, estado: str) -> None:
        self.odontogram_view.set_current_state(estado)

    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not path:
            return
        try:
            saved = capture_odontogram(
                self.odontogram_view,
                patient_name=self.lblAfilValue.text(),
                captures_dir=path,
            )
            QMessageBox.information(self, "Captura guardada", saved)
        except Exception as ex:
            QMessageBox.warning(self, "Error", str(ex))

    def _do_refresh(self) -> None:
        if self.current_idboca is None:
            return
        try:
            data = get_odontograma_data(self.current_idboca)
            self.odontogram_view.apply_batch_states(
                parse_dientes_sp(str(data.get("dientes", "")))
            )
            QMessageBox.information(self, "Actualizado", "Odontograma refrescado.")
        except Exception as ex:
            QMessageBox.warning(self, "Error al refrescar", str(ex))
