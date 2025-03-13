# odontograma.py
import sys
import argparse
from PyQt5.QtWidgets import QApplication

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
    # Argumento posicional (numero). También lo hacemos opcional con `nargs='?'`.
    parser.add_argument("numero", type=int, nargs='?', default=None,
                        help="Número para buscar en la BD (p.ej. 87). Si no se pasa, se abrirá vacío.")

    args = parser.parse_args()

    # Llamamos a get_odontograma_data con args.numero
    data = get_odontograma_data(args.numero)

    app = QApplication(sys.argv)
    apply_style(app)

    w = MainWindow(data)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
