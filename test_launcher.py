# test_launcher.py
import sys
import time
from PyQt5.QtCore    import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

# Asumimos que Utils/loading_img.py está accesible
from Utils.loading_img import LoadingSplash

# 1. Un Worker FALSO que solo espera 4 segundos
class FakeWorker(QObject):
    finished = pyqtSignal()

    def run(self):
        print("Trabajo FALSO iniciado... esperando 4 segundos.")
        time.sleep(4)
        print("Trabajo FALSO terminado.")
        self.finished.emit()

# 2. El lanzador de prueba
def main_test():
    app = QApplication(sys.argv)
    
    # Una ventana principal FALSA y muy simple
    main_win: QMainWindow | None = None
    
    splash = LoadingSplash(app,
                           gif_rel_path="src/teeth.gif",
                           message="Probando animación…")

    def on_finished():
        nonlocal main_win
        print("Creando ventana final.")
        # Creamos una ventana genérica, no la tuya
        main_win = QMainWindow()
        main_win.setWindowTitle("Prueba Exitosa")
        main_win.setCentralWidget(QLabel("Si ves esto, el sistema de hilos y splash funciona."))
        main_win.resize(400, 200)
        splash.finish(main_win)

    thread = QThread()
    worker = FakeWorker()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()
    splash.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_test()