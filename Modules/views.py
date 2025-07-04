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
        self.setWindowTitle("Odontograma con 2 SP y Fechas Formateadas")

        # Recibimos parámetros
        self.data_dict = data_dict
        self.idafiliado     = data_dict.get("credencial", "")
        self.fecha_param    = data_dict.get("fecha", "")
        self.efectorColegio = data_dict.get("efectorColegio", "")
        self.efectorCodFact = data_dict.get("efectorCodFact", "")

        # Icono
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Stylesheet
        self.setup_stylesheet()

        # Odontograma
        self.odontogram_view = OdontogramView(locked=False)

        # Campos para SP #2 (de desarrollo)
        # => Llenos cuando se selecciona una fila
        self.credencialEdit   = QLineEdit("")
        self.afiliadoEdit     = QLineEdit("")
        self.prestadorEdit    = QLineEdit("")
        self.fechaEdit        = QLineEdit("")
        self.observacionesEdit= QLineEdit("")

        for w in [self.credencialEdit, self.afiliadoEdit,
                  self.prestadorEdit, self.fechaEdit, self.observacionesEdit]:
            w.setReadOnly(True)  # solo se setea al hacer clic en la tabla

        # Llamamos al SP #1 => get_bocas_consulta_estados
        try:
            if self.idafiliado.isdigit():
                bocas_rows = get_bocas_consulta_estados(int(self.idafiliado), self.fecha_param)
            else:
                bocas_rows = []
        except Exception as e:
            print("[WARN] No se pudo obtener bocas:", e)
            bocas_rows = []

        # Layout superior => Credencial, Afiliado, Prestador, Fecha, Observaciones
        formLayout = QFormLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Credencial:"))
        row1.addWidget(self.credencialEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Afiliado:"))
        row1.addWidget(self.afiliadoEdit)
        formLayout.addRow(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Prestador:"))
        row2.addWidget(self.prestadorEdit)
        row2.addSpacing(20)
        row2.addWidget(QLabel("Fecha:"))
        row2.addWidget(self.fechaEdit)
        formLayout.addRow(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Observaciones:"))
        row3.addWidget(self.observacionesEdit)
        formLayout.addRow(row3)

        # Pestañas a la izquierda
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)

        # Pestaña Bocas => donde tenemos la tabla
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
                "Prótesis Completa INFERIOR": "icon_pciR.png"
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

        # Pintar la primer boca
        self.cargar_por_defecto(bocas_rows)

    def build_tab_bocas(self, container, filas_bocas):
        """
        1) Filtro Efector => chkEfector
        2) Tabla con 3 cols => [0 => idBoca, 1 => fechaCarga, 2 => efector].
        """
        from PyQt5.QtWidgets import QVBoxLayout, QCheckBox, QTableWidget, QTableWidgetItem

        layout = QVBoxLayout()

        self.chkEfector = QCheckBox("Filtrar Efector Presupuesto")
        self.chkEfector.setChecked(True)
        self.chkEfector.stateChanged.connect(self.on_filtrar_efector)
        layout.addWidget(self.chkEfector)

        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(["idBoca(oculto)","Fecha Carga","Efector"])
        self.tableBocas.cellClicked.connect(self.on_boca_seleccionada)
        layout.addWidget(self.tableBocas)

        container.setLayout(layout)

        self.filas_bocas_original = filas_bocas
        self.cargar_tabla_bocas(filas_bocas)

        # Ocultamos la col 0
        self.tableBocas.setColumnHidden(0, True)

    def cargar_tabla_bocas(self, filas):
        """
        col0 => idboca,
        col1 => fechaCarg,
        col2 => efector.
        No mostramos Observaciones (viene del 2do SP).
        """
        print("[DEBUG] cargar_tabla_bocas =>", filas)
        self.tableBocas.setRowCount(len(filas))
        for row_idx, rd in enumerate(filas):
            idboca  = str(rd.get("idboca",""))
            fecha   = str(rd.get("fechacarga",""))  # ya formateado dd/mm/aaaa
            efector = str(rd.get("efector",""))

            self.tableBocas.setItem(row_idx, 0, QTableWidgetItem(idboca))
            self.tableBocas.setItem(row_idx, 1, QTableWidgetItem(fecha))
            self.tableBocas.setItem(row_idx, 2, QTableWidgetItem(efector))

    def on_filtrar_efector(self, state):
        """
        Filtra por efectorcolegio, efectorcodfact => no se muestra en la tabla, pero
        está en filas_bocas_original. 
        """
        if state == Qt.Checked:
            c = self.efectorColegio
            f = self.efectorCodFact
            filtradas = []
            for row in self.filas_bocas_original:
                if (str(row.get("efectorcolegio","")) == c and
                    str(row.get("efectorcodfact","")) == f):
                    filtradas.append(row)
            self.cargar_tabla_bocas(filtradas)
        else:
            self.cargar_tabla_bocas(self.filas_bocas_original)

    def on_boca_seleccionada(self, row, col):
        """
        1) Toma idBoca (col0).
        2) Llama get_odontograma_data => 
           credencial, afiliado, prestador, fecha, observaciones, dientes
        3) Setea form + pinta QGraphicsView
        """
        idboca_str = self.tableBocas.item(row, 0).text().strip()
        if not idboca_str.isdigit():
            return

        idboca = int(idboca_str)
        # Llamar 2do SP
        data_sp2 = get_odontograma_data(idboca)

        self.credencialEdit.setText(data_sp2.get("credencial",""))
        self.afiliadoEdit.setText(data_sp2.get("afiliado",""))
        self.prestadorEdit.setText(data_sp2.get("prestador",""))
        self.fechaEdit.setText(data_sp2.get("fecha",""))
        self.observacionesEdit.setText(data_sp2.get("observaciones",""))

        # Pintar 
        dientes_str = data_sp2.get("dientes","")
        self.odontogram_view.apply_batch_states(parse_dental_states(dientes_str))

        print(f"[DEBUG] Seleccionaste idBoca={idboca}, SP2 devolvió => {data_sp2}")

    def cargar_por_defecto(self, filas_bocas):
        """
        Si hay al menos 1 fila => llama get_odontograma_data para la 1ra,
        y setea los campos en el form + pinta QGraphicsView.
        """
        if filas_bocas:
            first_idboca = filas_bocas[0].get("idboca","")
            if first_idboca:
                data_sp2 = get_odontograma_data(first_idboca)

                self.credencialEdit.setText(data_sp2.get("credencial",""))
                self.afiliadoEdit.setText(data_sp2.get("afiliado",""))
                self.prestadorEdit.setText(data_sp2.get("prestador",""))
                self.fechaEdit.setText(data_sp2.get("fecha",""))
                self.observacionesEdit.setText(data_sp2.get("observaciones",""))

                di = data_sp2.get("dientes","")
                self.odontogram_view.apply_batch_states(parse_dental_states(di))

    def setup_stylesheet(self):
        """
        Aplica la hoja de estilo con background.jpg, 
        translucidez en QLineEdit, QComboBox, etc.
        """
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
        # Tomamos Cred + Fecha del form
        cred = self.credencialEdit.text().strip().replace(" ", "_")
        f = self.fechaEdit.text().strip().replace(" ", "_")
        if not cred: cred = "SIN_CREDENCIAL"
        if not f: f = "SIN_FECHA"
        file_name = f"odontograma_{cred}_{f}.png"

        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not folder_path:
            return

        full_path = os.path.join(folder_path, file_name)
        pixmap = self.grab()
        if pixmap.save(full_path, "PNG"):
            print(f"[OK] Captura guardada: {full_path}")
        else:
            print("[ERROR] No se pudo guardar la imagen.")
