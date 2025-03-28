#!/usr/bin/env python
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils import resource_path, parse_dental_states
from Modules.menu_estados import MenuEstados
from Modules.conexion_db import get_bocas_consulta_estados, get_odontograma_data


class MainWindow(QMainWindow):
    def __init__(self, data_dict):
        super().__init__()
        self.setWindowTitle("Odontograma (Mostrar Fecha, Efector y Observaciones)")

        # 1) Recibir parámetros
        self.data_dict = data_dict
        self.idafiliado     = data_dict.get("credencial","")
        self.fecha          = data_dict.get("fecha","")
        self.efectorColegio = data_dict.get("efectorColegio","")
        self.efectorCodFact = data_dict.get("efectorCodFact","")

        # 2) Icono
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 3) Stylesheet
        self.setup_stylesheet()

        # 4) Odontograma
        self.odontogram_view = OdontogramView(locked=False)

        # 5) Inputs (se muestran arriba)
        self.credencialEdit = QLineEdit(self.idafiliado)
        self.fechaEdit      = QLineEdit(self.fecha)

        # Observaciones se va actualizando al seleccionar la fila
        self.observacionesEdit = QLineEdit("")
        self.observacionesEdit.setMaxLength(100)

        # Llamamos a get_bocas_consulta_estados
        try:
            if self.idafiliado.isdigit():
                bocas_rows = get_bocas_consulta_estados(int(self.idafiliado), self.fecha)
            else:
                bocas_rows = []
        except Exception as e:
            print("[WARN] No se pudo obtener bocas:", e)
            bocas_rows = []

        # Layout superior
        formLayout = QFormLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Credencial:"))
        row1.addWidget(self.credencialEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Fecha:"))
        row1.addWidget(self.fechaEdit)
        formLayout.addRow(row1)

        # Observaciones -> se actualiza cada vez que el usuario seleccione una fila
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Observaciones:"))
        row2.addWidget(self.observacionesEdit)
        formLayout.addRow(row2)

        # 6) Pestañas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)

        # Pestaña Bocas
        self.tab_bocas = QWidget()
        self.build_tab_bocas(self.tab_bocas, bocas_rows)
        self.tabs.addTab(self.tab_bocas, "Bocas Disponibles")

        # Pestaña Prestaciones Existentes
        self.menu_existentes = MenuEstados(
            on_estado_selected=self.on_estado_clicked,
            locked=False,
            title="Prestaciones Existentes"
        )
        self.tabs.addTab(self.menu_existentes, "Prestaciones Existentes")

        # Pestaña Prestaciones Requeridas
        self.menu_requeridas = MenuEstados(
            on_estado_selected=self.on_estado_clicked,
            locked=False,
            title="Prestaciones Requeridas",
            estados_personalizados={
                "Caries": "icon_cariesR.png",
                "Extracción": "icon_extraccionR.png",
                "Prótesis Removible SUPERIOR": "icon_prsR.png",
                "Prótesis Removible INFERIOR": "icon_priR.png",
                "Prótesis Completa SUPERIOR": "icon_pcsR.png",
                "Prótesis Completa INFERIOR": "icon_pciR.png",
            }
        )
        self.tabs.addTab(self.menu_requeridas, "Prestaciones Requeridas")

        # Botón Descargar
        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.tabs)
        leftLayout.addWidget(self.descargarButton)
        leftLayout.addStretch()

        odontoLayout = QVBoxLayout()
        odontoLayout.addWidget(self.odontogram_view)

        hLayout = QHBoxLayout()
        hLayout.addLayout(leftLayout, stretch=0)
        hLayout.addLayout(odontoLayout, stretch=1)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayout)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        # Pintar la primer boca si existe
        self.cargar_por_defecto(bocas_rows)

    def build_tab_bocas(self, container, filas_bocas):
        """
        Muestra col0= idBoca (oculto), col1=fechaCarga, col2=efector, col3=observaciones,
        col4 y 5 si quisieras efectorColegio y codFact, etc.
        """
        from PyQt5.QtWidgets import QVBoxLayout, QCheckBox, QTableWidget, QTableWidgetItem

        layout = QVBoxLayout()

        self.chkEfector = QCheckBox("Filtrar Efector Presupuesto")
        self.chkEfector.setChecked(True)
        self.chkEfector.stateChanged.connect(self.on_filtrar_efector)
        layout.addWidget(self.chkEfector)

        self.tableBocas = QTableWidget()
        # 4 col => 0 => idBoca (oculto), 1 => fechaBoca, 2 => efector, 3 => resumen
        self.tableBocas.setColumnCount(4)
        self.tableBocas.setHorizontalHeaderLabels(["idBoca","Fecha Carga","Efector","Observaciones"])
        self.tableBocas.cellClicked.connect(self.on_boca_seleccionada)
        layout.addWidget(self.tableBocas)

        container.setLayout(layout)

        self.filas_bocas_original = filas_bocas
        self.cargar_tabla_bocas(filas_bocas)

        # Ocultamos col 0 => idBoca
        self.tableBocas.setColumnHidden(0, True)

    def cargar_tabla_bocas(self, filas):
        """
        Solo necesitamos idboca, fechacarga, efector, resumenclinico.
        Filtramos efectorcolegio y efectorcodfact aparte (no se muestran)
        """
        print("[DEBUG] cargar_tabla_bocas =>", filas)
        self.tableBocas.setRowCount(len(filas))
        for row_idx, rd in enumerate(filas):
            # Ajustar keys (idboca, fechacarga, efector, resumenclinico)
            idboca  = str(rd.get("idboca",""))
            fecha   = str(rd.get("fechacarga",""))
            efector = str(rd.get("efector",""))
            resumen = str(rd.get("resumenclinico",""))

            # col0 => idBoca (oculto)
            self.tableBocas.setItem(row_idx, 0, QTableWidgetItem(idboca))
            # col1 => fecha
            self.tableBocas.setItem(row_idx, 1, QTableWidgetItem(fecha))
            # col2 => efector
            self.tableBocas.setItem(row_idx, 2, QTableWidgetItem(efector))
            # col3 => resumen
            self.tableBocas.setItem(row_idx, 3, QTableWidgetItem(resumen))

    def on_filtrar_efector(self, state):
        """
        Filtro: si 'efectorcolegio' y 'efectorcodfact' coinciden
        """
        if state == Qt.Checked:
            c = self.efectorColegio
            f = self.efectorCodFact
            filas_filtradas = []
            for row in self.filas_bocas_original:
                # si row_data[efectorcolegio]== c y efectorcodfact==f => lo muestra
                if (str(row.get("efectorcolegio","")) == c and
                    str(row.get("efectorcodfact","")) == f):
                    filas_filtradas.append(row)
            self.cargar_tabla_bocas(filas_filtradas)
        else:
            # Sin filtrar
            self.cargar_tabla_bocas(self.filas_bocas_original)

    def on_boca_seleccionada(self, row, col):
        """
        Toma idBoca (col0 oculto), llama get_odontograma_data => pinta
        y además setea self.observacionesEdit con el 'Observaciones' col3
        """
        idboca_str = self.tableBocas.item(row, 0).text().strip()
        if not idboca_str.isdigit():
            return
        # col3 => Observaciones
        obs_item = self.tableBocas.item(row, 3)
        observaciones_val = obs_item.text() if obs_item else ""

        self.observacionesEdit.setText(observaciones_val)

        idboca = int(idboca_str)
        data_odo = get_odontograma_data(idboca)
        dientes_str = data_odo.get("dientes","")
        self.odontogram_view.apply_batch_states(parse_dental_states(dientes_str))
        print(f"[DEBUG] Seleccionaste idBoca={idboca}. Observaciones='{observaciones_val}'")

    def cargar_por_defecto(self, filas_bocas):
        if filas_bocas:
            primer = filas_bocas[0]
            primer_id = primer.get("idboca","")
            primer_resumen = str(primer.get("resumenclinico",""))
            self.observacionesEdit.setText(primer_resumen)

            if primer_id:
                data_odo = get_odontograma_data(primer_id)
                dientes_str = data_odo.get("dientes","")
                self.odontogram_view.apply_batch_states(parse_dental_states(dientes_str))

    def setup_stylesheet(self):
        bg_path = resource_path("src/background.jpg")
        if os.path.exists(bg_path):
            bg_path_ = bg_path.replace('\\', '/')
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{
                    background-image: url("{bg_path_}");
                    background-repeat: no-repeat;
                    background-position: center;
                }}
                QLineEdit, QPushButton, QToolButton, QTabWidget::pane, QComboBox,
                QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit, QTableWidget {{
                    background-color: rgba(255,255,255, 0.8);
                }}
                QLabel {{
                    background: transparent;
                }}
                QGraphicsView {{
                    background-color: rgba(255,255,255, 0.9);
                }}
            """)

    def on_estado_clicked(self, estado_str):
        print(f"[INFO] Estado seleccionado: {estado_str}")
        self.odontogram_view.set_current_state(estado_str)

    def on_descargar_clicked(self):
        from PyQt5.QtWidgets import QFileDialog

        afil = self.credencialEdit.text().strip().replace(" ", "_")
        fecha = self.fechaEdit.text().strip().replace(" ", "_")
        if not afil: afil = "SIN_AFILIADO"
        if not fecha: fecha = "SIN_FECHA"
        file_name = f"odontograma_{afil}_{fecha}.png"

        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not folder_path:
            return

        full_path = os.path.join(folder_path, file_name)
        pixmap = self.grab()
        if pixmap.save(full_path, "PNG"):
            print(f"[OK] Captura guardada: {full_path}")
        else:
            print("[ERROR] No se pudo guardar la imagen.")
