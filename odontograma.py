#!/usr/bin/env python
# coding: utf-8
"""
Launcher del visualizador de Odontograma.
Ejemplo:
python odontograma.py 354495 "01/02/2025" "ODONTOLOGO DE PRUEBA COCH" 3 333
"""
import sys
import argparse
from typing import Any

from PyQt5.QtCore    import QSharedMemory, QSystemSemaphore
from PyQt5.QtWidgets import QApplication

# ────────────────────────────────
#  Estilo (opcional)
# ────────────────────────────────
try:
    from Styles.style import apply_style
except ImportError:
    def apply_style(app: Any) -> None:         # stub si no hay módulo
        pass

# ────────────────────────────────
#  Módulos propios
# ────────────────────────────────
from Modules.conexion_db import get_bocas_consulta_efector


# ════════════════════════════════════════════════════════════
#  BLOQUEO DE INSTANCIA ÚNICA
# ════════════════════════════════════════════════════════════
APP_ID = "OdontogramaSingletonKey"          # cadena única para la app

sem   = QSystemSemaphore(APP_ID + "_sem", 1)
sem.acquire()                               # evita condición de carrera
shared = QSharedMemory(APP_ID)
already_running = not shared.create(1)      # 1 byte es suficiente
sem.release()

if already_running:
    print("Ya hay otra instancia en ejecución.")
    sys.exit(0)


# ════════════════════════════════════════════════════════════
#  UTILIDADES
# ════════════════════════════════════════════════════════════
def build_data_dict(args, bocas_rows):
    return {
        "credencial":      args.credencial,
        "fecha":           args.fecha,
        "efectorNombre":   args.efectorNombre,
        "colegio":         args.colegio,
        "efectorCodFact":  args.efectorCodFact,
        "filas_bocas":     bocas_rows,
        "locked": True,
    }


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
def main() -> None:
    p = argparse.ArgumentParser("Visualizador Odontograma")
    p.add_argument("credencial",      type=str)
    p.add_argument("fecha",           type=str)   # dd/mm/aaaa
    p.add_argument("efectorNombre",   type=str)
    p.add_argument("colegio",         type=int)
    p.add_argument("efectorCodFact",  type=int)
    args = p.parse_args()

    # ── Obtener bocas de la DB
    bocas_rows = get_bocas_consulta_efector(
        idafiliado = args.credencial,
        colegio    = args.colegio,
        codfact    = args.efectorCodFact,
        fecha      = args.fecha,
    )

    data_dict = build_data_dict(args, bocas_rows)

    # ── Lanzar interfaz Qt
    app = QApplication(sys.argv)
    apply_style(app)
    from Modules.views import MainWindow
    MainWindow(data_dict).show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
