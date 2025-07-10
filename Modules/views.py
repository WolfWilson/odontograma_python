#!/usr/bin/env python
# coding: utf-8
"""
views.py – Ventana principal del Odontograma
· Lista bocas  → get_bocas_consulta_efector()
· Detalle      → get_odontograma_data(idBoca)
"""
from __future__ import annotations

import os
from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Modules.conexion_db import get_bocas_consulta_efector, get_odontograma_data
from Modules.menu_estados import MenuEstados
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils import parse_dental_states, resource_path


# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""

    # -------------------------------------------------------------------------
    def __init__(self, data_dict: Dict[str, str | List[Dict[str, str]]]) -> None:
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")

        # --- Parámetros -----------------------------------------------------
        self.idafiliado: str = str(data_dict.get("credencial", ""))
        self.fecha_param: str = str(data_dict.get("fecha", ""))
        self.colegio: str = str(data_dict.get("colegio", ""))
        self.codfact: str = str(data_dict.get("efectorCodFact", ""))
        self.efectorName: str = str(data_dict.get("efectorNombre", ""))

        # --- Icono ----------------------------------------------------------
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Vista odontograma --------------------------------------------
        self.odontogram_view = OdontogramView(locked=False)

        # --- Labels de valores (negro, fondo transparente) -----------------
        self.lblCredValue = self._value_label()
        self.lblAfilValue = self._value_label()
        self.lblPrestValue = self._value_label()
        self.lblFechaValue = self._value_label()
        self.lblObsValue = self._value_label(word_wrap=True)

        # --- Encabezado -----------------------------------------------------
        header = self._build_header()

        # --- Datos de bocas -------------------------------------------------
        bocas_rows: List[Dict[str, str]] | None = data_dict.get("filas_bocas")
        if bocas_rows is None:
            try:
                bocas_rows = get_bocas_consulta_efector(
                    idafiliado=self.idafiliado,
                    colegio=int(self.colegio) if self.colegio.isdigit() else 0,
                    codfact=int(self.codfact) if self.codfact.isdigit() else 0,
                    fecha=self.fecha_param,
                )
            except Exception as exc:
                print("[WARN] No se pudo obtener bocas:", exc)
                bocas_rows = []

        # --- Pestañas -------------------------------------------------------
        self.tabs = self._build_tabs(bocas_rows)

        # --- Botón Descargar ------------------------------------------------
        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        # --- Layout general -------------------------------------------------
        sidebar = QVBoxLayout()
        sidebar.addWidget(self.tabs)
        sidebar.addWidget(self.descargarButton)
        sidebar.addStretch()

        odontogram_layout = QVBoxLayout()
        odontogram_layout.addWidget(self.odontogram_view)

        body = QHBoxLayout()
        body.addLayout(sidebar, 0)
        body.addLayout(odontogram_layout, 1)

        root = QVBoxLayout()
        root.addWidget(header)
        root.addLayout(body)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        # --- Selección inicial --------------------------------------------
        self._cargar_por_defecto(bocas_rows)

    # ------------------------------------------------------------------ UI
    def _build_header(self) -> QFrame:
        """Encabezado justificado azul."""
        header = QFrame(objectName="headerFrame")
        header.setMinimumHeight(100)

        grid = QGridLayout(spacing=12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 3)

        f = QFont("Segoe UI", 12)

        grid.addWidget(self._key("CREDENCIAL:", f), 0, 0)
        grid.addWidget(self.lblCredValue, 0, 1)
        grid.addWidget(self._key("AFILIADO:", f), 0, 2)
        grid.addWidget(self.lblAfilValue, 0, 3)

        grid.addWidget(self._key("PRESTADOR:", f), 1, 0)
        grid.addWidget(self.lblPrestValue, 1, 1)
        grid.addWidget(self._key("FECHA:", f), 1, 2)
        grid.addWidget(self.lblFechaValue, 1, 3)

        grid.addWidget(self._key("OBSERVACIONES:", f), 2, 0, Qt.AlignTop)
        grid.addWidget(self.lblObsValue, 2, 1, 1, 3)

        header.setLayout(grid)
        return header

    # ------------------------------------------------------------------
    def _key(self, text: str, font: QFont) -> QLabel:
        lbl = QLabel(text, objectName="keyLabel")
        lbl.setFont(font)
        self._add_shadow(lbl)
        return lbl

    def _value_label(self, *, word_wrap: bool = False) -> QLabel:
        lbl = QLabel(objectName="valueLabel")
        lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;")
        lbl.setMinimumWidth(150)
        return lbl

    def _add_shadow(self, lbl: QLabel) -> None:
        """Aplica una sombra negra suave alrededor del texto."""
        shadow = QGraphicsDropShadowEffect(blurRadius=6)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        lbl.setGraphicsEffect(shadow)

    # -------------------------------------------------------------- pestañas
    def _build_tabs(self, bocas_rows: List[Dict[str, str]]) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        tab_bocas = QWidget()
        self._build_tab_bocas(tab_bocas, bocas_rows)
        tabs.addTab(tab_bocas, "Bocas Disponibles")

        tabs.addTab(
            MenuEstados(
                on_estado_selected=self._on_estado_clicked,
                locked=False,
                title="Prestaciones Existentes",
            ),
            "Pres Existentes",
        )

        tabs.addTab(
            MenuEstados(
                on_estado_selected=self._on_estado_clicked,
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

    def _build_tab_bocas(
        self, container: QWidget, filas_bocas: List[Dict[str, str]]
    ) -> None:
        layout = QVBoxLayout()
        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca (oculto)", "Fecha Carga", "Resumen Clínico"]
        )
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        layout.addWidget(self.tableBocas)
        container.setLayout(layout)

        self._cargar_tabla_bocas(filas_bocas)
        self.tableBocas.setColumnHidden(0, True)

    # --------------------------------------------------------- carga/eventos
    def _cargar_tabla_bocas(self, filas: List[Dict[str, str]]) -> None:
        self.tableBocas.setRowCount(len(filas))
        for r, d in enumerate(filas):
            self.tableBocas.setItem(r, 0, QTableWidgetItem(str(d.get("idboca", ""))))
            self.tableBocas.setItem(
                r, 1, QTableWidgetItem(str(d.get("fechacarga", "")))
            )
            self.tableBocas.setItem(
                r, 2, QTableWidgetItem(str(d.get("resumenclinico", "")))
            )

    def _on_boca_seleccionada(self, row: int, _col: int) -> None:
        id_item = self.tableBocas.item(row, 0)
        if not (id_item and id_item.text().strip().isdigit()):
            return

        idboca = int(id_item.text())
        data = get_odontograma_data(idboca)

        self.lblCredValue.setText(data.get("credencial", ""))
        self.lblAfilValue.setText(data.get("afiliado", ""))
        self.lblPrestValue.setText(data.get("prestador", ""))
        self.lblFechaValue.setText(data.get("fecha", ""))
        self.lblObsValue.setText(data.get("observaciones", ""))

        self.odontogram_view.apply_batch_states(
            parse_dental_states(data.get("dientes", ""))
        )
        print(f"[DEBUG] Seleccionaste idBoca={idboca} ⇒ {data}")

    def _cargar_por_defecto(self, filas_bocas: List[Dict[str, str]]) -> None:
        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # -------------------------------------------------------------- slots
    def _on_estado_clicked(self, estado: str) -> None:
        print(f"[INFO] Estado seleccionado: {estado}")
        self.odontogram_view.set_current_state(estado)

    def on_descargar_clicked(self) -> None:
        cred = self.lblCredValue.text().strip().replace(" ", "_") or "SIN_CREDENCIAL"
        fecha = self.lblFechaValue.text().strip().replace(" ", "_") or "SIN_FECHA"
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not path:
            return
        full = os.path.join(path, f"odontograma_{cred}_{fecha}.png")
        if self.grab().save(full, "PNG"):
            print("[OK] Captura guardada:", full)
        else:
            print("[ERROR] No se pudo guardar la imagen.")