#!/usr/bin/env python
# coding: utf-8

import sys
import pyodbc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QHeaderView
)

class DriverTester(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test de drivers ODBC")
        self.resize(700, 400)
        self._init_ui()

    def _init_ui(self):
        # ——— Campos de servidor y base ———
        lbl_server = QLabel("Servidor:")
        self.cb_server = QComboBox()
        # Puedes precargar nombres frecuentes:
        self.cb_server.addItems(["Concentrador", "concentrador-desarrollo", ""])
        self.cb_server.setEditable(True)

        lbl_db = QLabel("Base de datos:")
        self.cb_db = QComboBox()
        self.cb_db.setEditable(False)

        btn_load_db = QPushButton("Cargar bases")
        btn_load_db.clicked.connect(self.load_databases)

        btn_test = QPushButton("Probar drivers")
        btn_test.clicked.connect(self.test_drivers)

        # Layout horizontal superior
        hbox = QHBoxLayout()
        hbox.addWidget(lbl_server)
        hbox.addWidget(self.cb_server)
        hbox.addWidget(btn_load_db)
        hbox.addSpacing(20)
        hbox.addWidget(lbl_db)
        hbox.addWidget(self.cb_db)
        hbox.addWidget(btn_test)

        # ——— Tabla de resultados ———
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Driver", "Resultado"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents) # type: ignore[attr-defined]
        hdr.setSectionResizeMode(1, QHeaderView.Stretch) # type: ignore[attr-defined]

        # Layout principal
        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addWidget(self.table)

    def load_databases(self):
        """Conecta al servidor en master y recupera sys.databases."""
        self.cb_db.clear()
        server = self.cb_server.currentText().strip()
        if not server:
            return

        for name in pyodbc.drivers():
            drv = f"{{{name}}}"
            try:
                conn = pyodbc.connect(
                    f"DRIVER={drv};SERVER={server};DATABASE=master;Trusted_Connection=yes;",
                    timeout=3
                )
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sys.databases ORDER BY name")
                names = [row[0] for row in cursor.fetchall()]
                conn.close()
                # Cargamos y salimos
                self.cb_db.addItems(names)
                print(f"[OK] Cargadas {len(names)} bases usando driver {drv}")
                return
            except Exception:
                continue
        print("[ERROR] No se pudo conectar a master con ningún driver.")

    def test_drivers(self):
        server = self.cb_server.currentText().strip()
        database = self.cb_db.currentText().strip()
        if not server or not database:
            return

        self.table.setRowCount(0)
        for name in pyodbc.drivers():
            drv = f"{{{name}}}"
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(drv))

            conn_str = (
                f"DRIVER={drv};SERVER={server};"
                f"DATABASE={database};Trusted_Connection=yes;"
            )
            try:
                conn = pyodbc.connect(conn_str, timeout=3)
                conn.close()
                res = "OK"
            except Exception as e:
                msg = str(e).split(";")[0]
                res = f"Fallo: {msg}"
            self.table.setItem(row, 1, QTableWidgetItem(res))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DriverTester()
    w.show()
    sys.exit(app.exec_())
