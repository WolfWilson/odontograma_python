#test_conexion_Concentrador.py
import pyodbc

def main():
    # Ajusta estos valores:
    driver_candidates = [
        '{SQL Server Native Client 10.0}',
        '{SQL Server Native Client 11.0}',
        '{ODBC Driver 13 for SQL Server}',
        '{ODBC Driver 17 for SQL Server}'
    ]
    server = 'Concentrador'   # o "Concentrador-Prestacion\\Instancia", o IP, etc.
    database = 'Prestacion'

    # Parámetros para el SP
    idafiliado = 354495
    fecha = '01/03/2025'

    # Recorremos distintos drivers hasta conectar
    conn = None
    for drv in driver_candidates:
        try:
            print(f"Probando conexión con {drv}...")
            conn = pyodbc.connect(
                f"DRIVER={drv};"
                f"SERVER={server};"
                f"DATABASE={database};"
                "Trusted_Connection=yes;"
            )
            print(f"[OK] Conectado con driver: {drv}")
            break
        except pyodbc.Error as e:
            print(f"[FAIL] Error con {drv}: {e}")

    if not conn:
        print("No se pudo conectar a la base de datos con ningún driver.")
        return

    # Ejecutar SP
    sp_name = "[dbo].[odo_boca_consulta_estados]"
    print(f"\nEjecutando SP {sp_name} {idafiliado}, '{fecha}'...")
    try:
        cursor = conn.cursor()
        cursor.execute(f"EXEC {sp_name} ?, ?", (idafiliado, fecha))
        rows = cursor.fetchall()
        if not rows:
            print("[INFO] No se obtuvieron filas.")
        else:
            # Mostrar nombres de columnas
            col_names = [desc[0] for desc in cursor.description]
            print("Columnas:", col_names)
            # Imprimir filas
            for row in rows:
                print(row)  # row es una tupla; puedes formatearla como quieras
    except pyodbc.Error as e:
        print("[ERROR] Al ejecutar el SP:", e)
    finally:
        cursor.close()
        conn.close()


def build_tab_bocas(self, container, filas_bocas):
    layout = QVBoxLayout()

    self.tableBocas = QTableWidget()
    self.tableBocas.setColumnCount(5)
    self.tableBocas.setHorizontalHeaderLabels(["idboca","fechaCarga","colegio","codfact","resumen"])
    layout.addWidget(self.tableBocas)

    container.setLayout(layout)

    self.cargar_tabla_bocas(filas_bocas)

def cargar_tabla_bocas(self, filas):
    print("cargar_tabla_bocas =>", filas)
    self.tableBocas.setRowCount(len(filas))
    for row_idx, rd in enumerate(filas):
        # Ajusta tus claves
        self.tableBocas.setItem(row_idx, 0, QTableWidgetItem(str(rd.get("idboca",""))))
        self.tableBocas.setItem(row_idx, 1, QTableWidgetItem(str(rd.get("fechacarga",""))))
        self.tableBocas.setItem(row_idx, 2, QTableWidgetItem(str(rd.get("efectorcolegio",""))))
        self.tableBocas.setItem(row_idx, 3, QTableWidgetItem(str(rd.get("efectorcodfact",""))))
        self.tableBocas.setItem(row_idx, 4, QTableWidgetItem(str(rd.get("resumenclinico",""))))
       

if __name__ == "__main__":
    main()
