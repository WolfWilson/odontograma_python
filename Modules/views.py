#!/usr/bin/env python
# coding: utf-8
"""
Modules/views.py   – Ventana principal (tamaño fijo 1260×600)

Cambios clave:
• setFixedSize(1260,600)  → la ventana nunca se agranda.
• OdontogramView máx. 320 px de alto.
• Tabla de bocas: máx. 16 filas visibles → scroll automático.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Mapping, Tuple, cast

from PyQt5.QtCore    import Qt, QSize
from PyQt5.QtGui     import QColor, QFont, QIcon, QShowEvent
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QRadioButton, QButtonGroup,
    QToolButton
)

from Modules.conexion_db   import get_bocas_consulta_efector, get_odontograma_data
from Modules.menubox_prest import get_menu_existentes, get_menu_requeridas, REQUERIDAS_FULL_SET
from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils         import resource_path, ESTADOS_POR_NUM
from Utils.sp_data_parse   import parse_dientes_sp
from Utils.actions         import capture_odontogram
from Utils.center_window   import center_on_screen
from Styles.animation import apply_button_colorize_animation

# ════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    """Ventana principal con odontograma + filtros de prestaciones."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        super().__init__()

        # —— Ventana fija 1260×600 ——
        self.setWindowTitle("Odontograma – Auditoría por Prestador")
        self.setFixedSize(1240, 700)                      # <—— lí­mite único
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

        # —— Vista odontograma (max 600 px) ——
        self.odontogram_view = OdontogramView(locked=self.locked)
        self.odontogram_view.setStyleSheet("background: transparent;")
        self.odontogram_view.setFrameShape(QFrame.NoFrame)
        self.odontogram_view.setMaximumHeight(600)        # <—— evita estirar

        # —— Encabezado ——
        self._build_header()

        # —— Datos iniciales ——
        filas_bocas = self._get_bocas(data)

        # —— Tabs + radios ——
        self.tabs = self._build_tabs(filas_bocas); self.tabs.setFixedWidth(320) # tabla de estados
        self.grp_filtro = self._build_filter_radios()

# —— Botón descargar ——
        # CORREGIDO: Se crea el botón y LUEGO se le asigna el nombre.
        btn_download = QToolButton(self)
        btn_download.setObjectName("btnDescargar")

        btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_download.setToolTip("Descargar captura")

        ico_save = resource_path("src/save-file.png")
        if os.path.exists(ico_save):
            btn_download.setIcon(QIcon(ico_save))
            btn_download.setIconSize(QSize(35, 35))
        else:
            btn_download.setText("💾")
        
        btn_download.clicked.connect(self._do_download)

        # APLICA LA ANIMACIÓN AQUÍ
        apply_button_colorize_animation(btn_download)

        # —— Layout canvas + botón ——
        odo_box = QVBoxLayout(); odo_box.setContentsMargins(0,0,0,0); odo_box.setSpacing(4)
        odo_box.addWidget(self.odontogram_view, 1)
        odo_box.addStretch()
        odo_box.addWidget(btn_download, alignment=Qt.AlignRight | Qt.AlignBottom) # type: ignore[attr-defined]
        odo_container = QWidget(); odo_container.setLayout(odo_box)

        # —— Sidebar ——
        sidebar = QVBoxLayout(); sidebar.setContentsMargins(0,0,0,0); sidebar.setSpacing(6)
        sidebar.addWidget(self.grp_filtro); sidebar.addWidget(self.tabs); sidebar.addStretch()

        # —— Layout principal ——
        body = QHBoxLayout(); body.addLayout(sidebar, 0); body.addWidget(odo_container, 1)
        root = QVBoxLayout(); root.setContentsMargins(10,10,10,10); root.setSpacing(8)
        root.addWidget(self.header_frame); root.addLayout(body)
        cont = QWidget(); cont.setLayout(root); self.setCentralWidget(cont)

        # —— centrar al mostrar ——
        self._centered = False
        if filas_bocas:
            self._on_boca_seleccionada(0, 0)

    # ───────────────── HEADER ─────────────────
    def _build_header(self) -> None:
        self.lblCredValue = self._val_lbl(); self.lblAfilValue = self._val_lbl()
        self.lblPrestValue = self._val_lbl(); self.lblFechaValue = self._val_lbl()
        self.lblObsValue   = self._val_lbl(word_wrap=True)

        hdr = QFrame(objectName="headerFrame"); hdr.setMinimumHeight(100) # type: ignore[attr-defined]
        self.header_frame = hdr
        bold = QFont("Segoe UI", 12, QFont.Bold)

        grid = QGridLayout(); grid.setSpacing(12)
        for c, s in enumerate([1,3,1,3]): grid.setColumnStretch(c, s)
        grid.addWidget(self._key("CREDENCIAL:", bold), 0,0); grid.addWidget(self.lblCredValue,0,1)
        grid.addWidget(self._key("AFILIADO:", bold),   0,2); grid.addWidget(self.lblAfilValue,0,3)
        grid.addWidget(self._key("PRESTADOR:", bold),  1,0); grid.addWidget(self.lblPrestValue,1,1)
        grid.addWidget(self._key("FECHA:", bold),      1,2); grid.addWidget(self.lblFechaValue,1,3)
        grid.addWidget(self._key("OBSERVACIONES:", bold), 2,0, alignment=Qt.AlignTop) # type: ignore[attr-defined]
        grid.addWidget(self.lblObsValue, 2,1,1,3)
        hdr.setLayout(grid)

    def _key(self, txt: str, f: QFont) -> QLabel:
        lbl = QLabel(txt); lbl.setFont(f); lbl.setStyleSheet("color:white;")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(6); eff.setOffset(0,0)
        eff.setColor(QColor(0,0,0,180)); lbl.setGraphicsEffect(eff); return lbl
    def _val_lbl(self, *, word_wrap=False) -> QLabel:
        lbl = QLabel(); lbl.setWordWrap(word_wrap)
        lbl.setStyleSheet("color:black; font-weight:bold; background:transparent;"); return lbl

    # ───────────────── TABS ─────────────────
    def _build_tabs(self, filas: List[Dict[str,str]]) -> QTabWidget:
        tabs = QTabWidget(); tabs.setTabPosition(QTabWidget.West)
        w_bocas = QWidget(); self._fill_tab_bocas(w_bocas, filas); tabs.addTab(w_bocas, "Bocas")
        tabs.addTab(get_menu_existentes(self._on_estado_clicked), "Pres Existentes")
        menu_req = get_menu_requeridas(self._on_estado_clicked)
        from PyQt5.QtWidgets import QToolButton
        for b in menu_req.findChildren(QToolButton): b.setIconSize(QSize(25,25))
        tabs.addTab(menu_req, "Prest Requeridas"); return tabs

    # ───────────────── RADIOS ─────────────────
    def _build_filter_radios(self) -> QWidget:
        rb_all = QRadioButton("Todos"); rb_all.setChecked(True)
        rb_ex  = QRadioButton("Solo Existentes"); rb_req = QRadioButton("Solo Requeridas")
        self.filter_group = QButtonGroup(self)
        for i, rb in enumerate((rb_all, rb_ex, rb_req)): self.filter_group.addButton(rb, i)
        self.filter_group.buttonToggled.connect(self._reapply_filter)
        box = QFrame(); lay = QHBoxLayout(box); [lay.addWidget(x) for x in (rb_all, rb_ex, rb_req)]
        return box

    # ─────────── TAB BOCAS (16 filas máx) ───────────
    def _fill_tab_bocas(self, cont: QWidget, filas: List[Dict[str,str]]) -> None:
        lay = QVBoxLayout(cont)
        self.tableBocas = QTableWidget()
        self.tableBocas.setColumnCount(3)
        self.tableBocas.setHorizontalHeaderLabels(["idBoca","Fecha Carga","Resumen Clínico"])
        self.tableBocas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableBocas.setSelectionMode(QTableWidget.SingleSelection)
        self.tableBocas.cellClicked.connect(self._on_boca_seleccionada)
        self.tableBocas.currentCellChanged.connect(
            lambda r,c,*_: self._on_boca_seleccionada(r,c))
        lay.addWidget(self.tableBocas)

        self.tableBocas.setRowCount(len(filas))
        for i,d in enumerate(filas):
            self.tableBocas.setItem(i,0,QTableWidgetItem(str(d.get("idboca",""))))
            self.tableBocas.setItem(i,1,QTableWidgetItem(str(d.get("fechacarga",""))))
            self.tableBocas.setItem(i,2,QTableWidgetItem(str(d.get("resumenclinico",""))))
        self.tableBocas.setColumnHidden(0, True)

        MAX_ROWS = 16
        head_h = self.tableBocas.horizontalHeader().height() # type: ignore[attr-defined]
        rows_h = sum(self.tableBocas.rowHeight(i)
                     for i in range(min(MAX_ROWS, self.tableBocas.rowCount())))
        self.tableBocas.setMaximumHeight(head_h + rows_h + 6)
        self.tableBocas.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # type: ignore[attr-defined]

    # ─────────── DATA helpers & slots ───────────
    def _get_bocas(self, data: Mapping[str,Any]) -> List[Dict[str,str]]:
        filas = cast(List[Dict[str,str]], data.get("filas_bocas", []))
        if filas:
            return filas
        try:
            return get_bocas_consulta_efector(
                idafiliado=str(data.get("credencial","")),
                colegio=int(str(data.get("colegio","0")) or 0),
                codfact=int(str(data.get("efectorCodFact","0")) or 0),
                fecha=str(data.get("fecha","")),
            )
        except Exception as e:
            print("[WARN] get_bocas:", e); return []

    def _on_boca_seleccionada(self, row:int, _col:int) -> None:
        itm = self.tableBocas.item(row,0)
        if not (itm and itm.text().isdigit()): return
        self.current_idboca = int(itm.text())
        data = get_odontograma_data(self.current_idboca)
        self.lblCredValue.setText(str(data.get("credencial","")))
        self.lblAfilValue .setText(str(data.get("afiliado","")))
        self.lblPrestValue.setText(str(data.get("prestador","")))
        self.lblFechaValue.setText(str(data.get("fecha","")))
        self.lblObsValue  .setText(str(data.get("observaciones","")))
        self.raw_states = parse_dientes_sp(str(data.get("dientes",""))); self._reapply_filter()

    def _reapply_filter(self) -> None:
        if not self.raw_states: return
        mode = self.filter_group.checkedId()
        flt = (lambda n: True) if mode==0 else (lambda n: ESTADOS_POR_NUM[n] not in REQUERIDAS_FULL_SET) if mode==1 else (lambda n: ESTADOS_POR_NUM[n] in REQUERIDAS_FULL_SET)
        self.odontogram_view.apply_batch_states([s for s in self.raw_states if flt(s[0])])

    def _on_estado_clicked(self, estado:str) -> None: self.odontogram_view.set_current_state(estado)

    def _do_download(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if not path: return
        try:
            tag = f"{self.lblCredValue.text()}_{self.lblFechaValue.text()}"
            saved = capture_odontogram(self.odontogram_view, patient_name=tag, captures_dir=path)
            QMessageBox.information(self, "Captura guardada", saved)
        except Exception as ex:
            QMessageBox.warning(self, "Error al guardar", str(ex))

    def showEvent(self, e:QShowEvent) -> None:  # type: ignore[override]
        super().showEvent(e)
        if not self._centered: center_on_screen(self); self._centered=True
