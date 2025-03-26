#!/usr/bin/env python
# coding: utf-8

import sys
import argparse
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QRect

try:
    from PyQt5.QtWidgets import QFileDialog
    from Modules.style import apply_style
except ImportError:
    def apply_style(x):
        pass

from Modules.conexion_db import get_odontograma_data
from Modules.views import MainWindow

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("numero", type=int, nargs='?', default=None,
                        help="Número para buscar en la BD (p.ej. 87). Si no se pasa, se abrirá el modo normal.")
    args = parser.parse_args()

    data = get_odontograma_data(args.numero)
    app = QApplication(sys.argv)
    apply_style(app)

    w = MainWindow(data)

    ruta_carpeta = r"\\concentrador\DocumentosConectividad\EstadoBoca"
    if not os.path.exists(ruta_carpeta):
        # os.makedirs(ruta_carpeta, exist_ok=True)  # si lo quieres crear localmente
        pass

    if args.numero is not None:
        # MODO SILENCIOSO => NO mostrar la ventana
        # 1) Forzamos el layout sin .show()
        w.resize(1300, 800)  # Ajusta según tu preferencia
        app.processEvents()   # Fuerza que se generen los layouts, etc.

        # 2) Renderizamos el widget en un pixmap
        w.resize(1300, 800)
        app.processEvents()

        pixmap = QPixmap(w.size())
        pixmap.fill(Qt.transparent)

        # Versión simple:
        w.render(pixmap)

        # Guardar PNG
        nombre_archivo = f"{args.numero}.png"
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        guardado_ok = pixmap.save(ruta_completa, "PNG")

        if guardado_ok:
            print(f"[OK] Captura silenciosa guardada en {ruta_completa}")
        else:
            print(f"[ERROR] No se pudo guardar la captura en {ruta_completa}")

        sys.exit(0)
    else:
        # MODO NORMAL
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()


#python odontograma.py 87
""""
pyinstaller --onefile --noconsole `                                                                                                           
>>     --add-data "Source;Source" `
>>     --add-data "leyenda.png;." `
>>     --hidden-import=Modules.conexion_db `
>>     --hidden-import=Modules.modelos `
>>     --hidden-import=Modules.views `
>>     --hidden-import=Modules.utils `
>>     --hidden-import=Modules.style `
>>     odontograma.py"
"""