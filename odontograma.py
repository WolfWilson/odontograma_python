#!odontrograma.py    main launcher
# coding: utf-8
"""
Ejemplo de uso:
python odontograma.py 354495 "01/02/2025" "ODONTOLOGO DE PRUEBA COCH" 3 333
"""
import sys, argparse
from typing import Any
from PyQt5.QtWidgets import QApplication

try:
    from Styles.style import apply_style              # opcional
except ImportError:
    def apply_style(app: Any) -> None: pass            # stub

from Modules.conexion_db import get_bocas_consulta_efector

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

def main() -> None:
    p = argparse.ArgumentParser("Visualizador Odontograma")
    p.add_argument("credencial",      type=str)
    p.add_argument("fecha",           type=str)            # dd/mm/aaaa
    p.add_argument("efectorNombre",   type=str)            # solo para mostrar
    p.add_argument("colegio",         type=int)
    p.add_argument("efectorCodFact",  type=int)
    args = p.parse_args()

    # ── SP de cabecera (4 parámetros) ────────────────────────
    bocas_rows = get_bocas_consulta_efector(
        idafiliado = args.credencial,
        colegio    = args.colegio,
        codfact    = args.efectorCodFact,
        fecha      = args.fecha,
    )

    data_dict = build_data_dict(args, bocas_rows)

    app = QApplication(sys.argv)
    apply_style(app)
    from Modules.views import MainWindow
    MainWindow(data_dict).show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
