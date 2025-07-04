#!/usr/bin/env python
# coding: utf-8
"""
Ventana principal del Odontograma.
• Muestra la lista de bocas devueltas por:   get_bocas_consulta_efector()
      ⇒ idBoca, fechaCarga, resumenClinico
• Al seleccionar una boca llama:             get_odontograma_data(idBoca)
      ⇒ credencial, afiliado, prestador, fecha, observaciones, dientes
"""

import os
from typing import List, Dict

from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton,
    QLabel, QLineEdit, QTabWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QTableWidget, QTableWidgetItem
)

# ──────────────────────────────────────────────────────────────
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils        import resource_path, parse_dental_states
from Modules.menu_estados import MenuEstados
from Modules.conexion_db  import (
    get_bocas_consulta_efector,
    get_odontograma_data,
)

# ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    # ----------------------------------------------------------
    def __init__(self, data_dict: Dict):
        super().__init__()
        self.setWindowTitle("Odontograma – Auditoría por Prestador")

        # ── Parámetros recibidos ──────────────────────────────
        self.idafiliado  = str(data_dict.get("credencial",      ""))
        self.fecha_param = str(data_dict.get("fecha",           ""))
        self.colegio     = str(data_dict.get("colegio",         ""))
        self.codfact     = str(data_dict.get("efectorCodFact",  ""))
        self.efectorName = str(data_dict.get("efectorNombre",   ""))

        # ── Ícono de ventana ──────────────────────────────────
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # ── Hoja de estilo ────────────────────────────────────
        self.setup_stylesheet()

        # ── Vista del odontograma ─────────────────────────────
        self.odontogram_view = OdontogramView(locked=False)

        # ── Campos de detalle (SP#2) ─────────────────────────
        self.credencialEdit    = QLineEdit()
        self.afiliadoEdit      = QLineEdit()
        self.prestadorEdit     = QLineEdit()
        self.fechaEdit         = QLineEdit()
        self.observacionesEdit = QLineEdit()
        for w in (
            self.credencialEdit, self.afiliadoEdit,
            self.prestadorEdit, self.fechaEdit, self.observacionesEdit
        ):
            w.setReadOnly(True)

        # ── SP#1 – lista de bocas ────────────────────────────
        bocas_rows = data_dict.get("filas_bocas")
        if bocas_rows is None:  # por si se llama a la vista directamente
            try:
                bocas_rows = get_bocas_consulta_efector(
                    idafiliado = int(self.idafiliado) if self.idafiliado.isdigit() else 0,
                    colegio    = int(self.colegio)   if self.colegio.isdigit()    else 0,
                    codfact    = int(self.codfact)   if self.codfact.isdigit()    else 0,
                    fecha      = self.fecha_param,
                )
            except Exception as e:
                print("[WARN] No se pudo obtener bocas:", e)
                bocas_rows = []

        # ───────────────────── Layout superior ───────────────
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

        # ───────────────────── Pestañas laterales ────────────
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)

        # ··· Pestaña «Bocas Disponibles»
        self.tab_bocas = QWidget()
        self.build_tab_bocas(self.tab_bocas, bocas_rows)
        self.tabs.addTab(self.tab_bocas, "Bocas Disponibles")

        # ··· Pestaña «Prestaciones Existentes»
        self.menu_existentes = MenuEstados(
            on_estado_selected = self.on_estado_clicked,
            locked             = False,
            title              = "Prestaciones Existentes",
        )
        self.tabs.addTab(self.menu_existentes, "Prestaciones Existentes")

        # ··· Pestaña «Prestaciones Requeridas»
        self.menu_requeridas = MenuEstados(
            on_estado_selected = self.on_estado_clicked,
            locked             = False,
            title              = "Prestaciones Requeridas",
            estados_personalizados = {
                "Caries":                         "icon_cariesR.png",
                "Extracción":                     "icon_extraccionR.png",
                "Prótesis Removible SUPERIOR":    "icon_prsR.png",
                "Prótesis Removible INFERIOR":    "icon_priR.png",
                "Prótesis Completa SUPERIOR":     "icon_pcsR.png",
                "Prótesis Completa INFERIOR":     "icon_pciR.png",
            },
        )
        self.tabs.addTab(self.menu_requeridas, "Prestaciones Requeridas")

        # ── Botón «Descargar» ─────────────────────────────────
        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        # ───────────────────── Layout principal ──────────────
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.tabs)
        leftLayout.addWidget(self.descargarButton)
        leftLayout.addStretch()

        odontoLayout = QVBoxLayout()
        odontoLayout.addWidget(self.odontogram_view)

        hLayout = QHBoxLayout()
        hLayout.addLayout(leftLayout,  stretch=0)
        hLayout.addLayout(odontoLayout, stretch=1)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayout)

        container = QWidget(); container.setLayout(mainLayout)
        self.setCentralWidget(container)
        self.resize(1300, 800)

        # ── Selecciona automáticamente la primera boca ───────
        self.cargar_por_defecto(bocas_rows)

    # ----------------------------------------------------------
    #  Construcción de pestaña «Bocas Disponibles»
    # ----------------------------------------------------------
    def build_tab_bocas(self, container: QWidget, filas_bocas: List[Dict]):
        layout = QVBoxLayout()

        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(
            ["idBoca (oculto)", "Fecha Carga", "Resumen Clínico"]
        )
        self.tableBocas.cellClicked.connect(self.on_boca_seleccionada)
        layout.addWidget(self.tableBocas)

        container.setLayout(layout)
        self.cargar_tabla_bocas(filas_bocas)

        # Oculta idBoca
        self.tableBocas.setColumnHidden(0, True)

    # ----------------------------------------------------------
    def cargar_tabla_bocas(self, filas: List[Dict]):
        print("[DEBUG] cargar_tabla_bocas ⇒", filas)
        self.tableBocas.setRowCount(len(filas))
        for row_idx, rd in enumerate(filas):
            idboca   = str(rd.get("idboca", ""))
            fecha    = str(rd.get("fechacarga", ""))
            resumen  = str(rd.get("resumenclinico", ""))

            self.tableBocas.setItem(row_idx, 0, QTableWidgetItem(idboca))
            self.tableBocas.setItem(row_idx, 1, QTableWidgetItem(fecha))
            self.tableBocas.setItem(row_idx, 2, QTableWidgetItem(resumen))

    # ----------------------------------------------------------
    def on_boca_seleccionada(self, row: int, col: int):
        """Carga la boca seleccionada y pinta el odontograma."""
        idboca_str = self.tableBocas.item(row, 0).text().strip()
        if not idboca_str.isdigit():
            return
        idboca = int(idboca_str)

        data = get_odontograma_data(idboca)

        self.credencialEdit.setText(data.get("credencial",    ""))
        self.afiliadoEdit.setText(data.get("afiliado",        ""))
        self.prestadorEdit.setText(data.get("prestador",      ""))
        self.fechaEdit.setText(data.get("fecha",              ""))
        self.observacionesEdit.setText(data.get("observaciones", ""))

        dientes_str = data.get("dientes", "")
        self.odontogram_view.apply_batch_states(parse_dental_states(dientes_str))

        print(f"[DEBUG] Seleccionaste idBoca={idboca} ⇒ {data}")

    # ----------------------------------------------------------
    def cargar_por_defecto(self, filas_bocas: List[Dict]):
        """Carga la primera boca por defecto (si existe)."""
        if filas_bocas:
            first_id = filas_bocas[0].get("idboca")
            if first_id:
                self.on_boca_seleccionada(0, 0)

    # ----------------------------------------------------------
    def setup_stylesheet(self):
        """Aplica fondo y transparencia."""
        bg_path = resource_path("src/background.jpg")
        if os.path.exists(bg_path):
            bg_path_ = bg_path.replace("\\", "/")
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{
                    background-image: url("{bg_path_}");
                    background-repeat: no-repeat;
                    background-position: center;
                }}
                QLineEdit, QPushButton, QToolButton, QTabWidget::pane, QComboBox,
                QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit, QTableWidget {{
                    background-color: rgba(255, 255, 255, 0.8);
                }}
                QLabel {{ background: transparent; }}
                QGraphicsView {{ background-color: rgba(255, 255, 255, 0.9); }}
            """)

    # ----------------------------------------------------------
    def on_estado_clicked(self, estado_str: str):
        print(f"[INFO] Estado seleccionado: {estado_str}")
        self.odontogram_view.set_current_state(estado_str)

    # ----------------------------------------------------------
    def on_descargar_clicked(self):
        """Guarda toda la ventana en PNG."""
        from PyQt5.QtWidgets import QFileDialog
        cred = self.credencialEdit.text().strip().replace(" ", "_") or "SIN_CREDENCIAL"
        fecha = self.fechaEdit.text().strip().replace(" ", "_") or "SIN_FECHA"
        file_name = f"odontograma_{cred}_{fecha}.png"

        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not folder:
            return
        full_path = os.path.join(folder, file_name)
        if self.grab().save(full_path, "PNG"):
            print(f"[OK] Captura guardada: {full_path}")
        else:
            print("[ERROR] No se pudo guardar la imagen.")
