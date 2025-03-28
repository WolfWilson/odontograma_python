#!/usr/bin/env python
# coding: utf-8

import sys
import argparse
from PyQt5.QtWidgets import QApplication

try:
    from PyQt5.QtWidgets import QFileDialog
    from Modules.style import apply_style
except ImportError:
    def apply_style(x):
        pass

from Modules.conexion_db import get_odontograma_data, get_bocas_consulta_estados
from Modules.views import MainWindow

def main():
    parser = argparse.ArgumentParser()
    # Cuatro argumentos posicionales: credencial, fecha, efectorColegio, efectorCodFact
    parser.add_argument("credencial", type=str, help="idafiliado, p.ej. 354495")
    parser.add_argument("fecha", type=str, help='Fecha p.ej. "22/05/2024"')
    parser.add_argument("efectorColegio", type=str, help='Nombre o cole del Efector')
    parser.add_argument("efectorCodFact", type=str, help='Código Facturador p.ej. 333')
    
    args = parser.parse_args()
    
    # Llamamos al primer procedimiento, por ejemplo:
    # get_bocas_consulta_estados(args.credencial, args.fecha)
    # (Ajusta según tu SP, parseos, etc.)
    # Podrías guardarlo en "filas_iniciales" o algo así.
    # Por ejemplo:
    # filas_iniciales = get_bocas_consulta_estados(args.credencial, args.fecha)

    # Armamos data_dict para pasarlo a la vista
    data_dict = {
        "credencial": args.credencial,
        "fecha": args.fecha,
        "efectorColegio": args.efectorColegio,
        "efectorCodFact": args.efectorCodFact,
        # "filas_bocas": filas_iniciales  # si querés pasarlo
    }

    app = QApplication(sys.argv)
    apply_style(app)

    w = MainWindow(data_dict)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
