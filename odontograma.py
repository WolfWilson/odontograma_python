#!/usr/bin/env python
# coding: utf-8
"""
Launcher del visualizador de Odontograma (versión sin hilos).
python odontograma.py 354495 "30/07/2025" "ODONTOLOGO DE PRUEBA COCH" 3 333
"""
from __future__ import annotations

import sys
import argparse
from typing import Any, Dict, List

from PyQt5.QtCore    import QSharedMemory, QSystemSemaphore
from PyQt5.QtWidgets import QApplication

# ─── Estilo opcional ────────────────────────────────────────
try:
    from Styles.style import apply_style
except ImportError:
    def apply_style(app: Any) -> None: pass

# ─── Módulos propios ────────────────────────────────────────
from Modules.conexion_db import get_bocas_consulta_efector
from Modules.views       import MainWindow
from Utils.loading_img   import LoadingSplash

# ─── Instancia única ────────────────────────────────────────
APP_ID = "OdontogramaSingletonKey"
_sem   = QSystemSemaphore(APP_ID + "_sem", 1)
_sem.acquire()
_shared = QSharedMemory(APP_ID)
if not _shared.create(1):
    print("Ya hay otra instancia en ejecución.")
    sys.exit(0)
_sem.release()

# ─── Helper dict de datos ───────────────────────────────────
def _build_data_dict(args, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "credencial":      args.credencial,
        "fecha":           args.fecha,
        "efectorNombre":   args.efectorNombre,
        "colegio":         args.colegio,
        "efectorCodFact":  args.efectorCodFact,
        "filas_bocas":     rows,
        "locked":          True,
    }

# ─── MAIN ───────────────────────────────────────────────────
def main() -> None:
    # 1) CLI --------------------------------------------------
    p = argparse.ArgumentParser("Visualizador Odontograma")
    p.add_argument("credencial")
    p.add_argument("fecha")          # dd/mm/aaaa
    p.add_argument("efectorNombre")
    p.add_argument("colegio", type=int)
    p.add_argument("efectorCodFact", type=int)
    args = p.parse_args()

    # 2) Qt App + splash inmediato ---------------------------
    app = QApplication(sys.argv)
    apply_style(app)                                # <-- si el CSS es válido
    splash = LoadingSplash(
        app,
        gif_rel_path="src/teeth.gif",               # usa tu ruta relativa
        message="Cargando…"
    )
    splash.show()
    app.processEvents()                             # pinta el primer frame

    # 3) Consulta BD (bloqueante) ----------------------------
    filas = get_bocas_consulta_efector(
        idafiliado=args.credencial,
        colegio=args.colegio,
        codfact=args.efectorCodFact,
        fecha=args.fecha,
    )
    data = _build_data_dict(args, filas)

    # 4) Ventana principal -----------------------------------
    win = MainWindow(data)
    win.show()

    # 5) Cerrar splash y entrar al loop ----------------------
    splash.finish(win)
    sys.exit(app.exec_())


if __name__ == "__main__":
    
    main()
