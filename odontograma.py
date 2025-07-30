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
    def apply_style(app: Any) -> None:  # stub si no hay módulo
        pass

# ────────────────────────────────
#  Módulos propios
# ────────────────────────────────
from Modules.conexion_db import get_bocas_consulta_efector
from Modules.views       import MainWindow
from Utils.loading_img   import LoadingSplash           # ← splash reutilizable

# ════════════════════════════════════════════════════════════
#  BLOQUEO DE INSTANCIA ÚNICA
# ════════════════════════════════════════════════════════════
APP_ID = "OdontogramaSingletonKey"  # cadena única para la app

_sem   = QSystemSemaphore(APP_ID + "_sem", 1)
_sem.acquire()                       # evita condición de carrera
_shared = QSharedMemory(APP_ID)
_already_running = not _shared.create(1)  # 1 byte es suficiente
_sem.release()

if _already_running:
    print("Ya hay otra instancia en ejecución.")
    sys.exit(0)

# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════
def _build_data_dict(args, bocas_rows):
    """Combina los datos de CLI + DB en un solo dict para MainWindow."""
    return {
        "credencial":      args.credencial,
        "fecha":           args.fecha,
        "efectorNombre":   args.efectorNombre,
        "colegio":         args.colegio,
        "efectorCodFact":  args.efectorCodFact,
        "filas_bocas":     bocas_rows,
        "locked": True,                    # ← lectura-sola (auditoría)
    }

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
def main() -> None:
    # ── CLI ──
    p = argparse.ArgumentParser("Visualizador Odontograma")
    p.add_argument("credencial",      type=str)
    p.add_argument("fecha",           type=str)   # dd/mm/aaaa
    p.add_argument("efectorNombre",   type=str)
    p.add_argument("colegio",         type=int)
    p.add_argument("efectorCodFact",  type=int)
    args = p.parse_args()

    # ── DB: filas de bocas ──
    bocas_rows = get_bocas_consulta_efector(
        idafiliado = args.credencial,
        colegio    = args.colegio,
        codfact    = args.efectorCodFact,
        fecha      = args.fecha,
    )

    data_dict = _build_data_dict(args, bocas_rows)

    # ── Qt App ──
    app = QApplication(sys.argv)
    apply_style(app)

    # ── Splash animado mientras se construye la GUI ──
    splash = LoadingSplash(app,
                           gif_rel_path="src/teeth.gif",
                           message="Cargando…")
    splash.show()
    app.processEvents()               # fuerza repintado del GIF

    # ── Ventana principal ──
    win = MainWindow(data_dict)       # ← guardamos la referencia
    win.show()

    splash.finish(win)                # cierra el splash cuando todo listo
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
