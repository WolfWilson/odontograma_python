#Modules/conexion_db.py
import pyodbc

def get_connection():
    drivers = [
        '{SQL Server Native Client 10.0}',  #  Driver específico para SQL Server 2012 (forzado)
        '{SQL Server Native Client 11.0}',  # Alternativa si falla
        '{ODBC Driver 13 for SQL Server}',  # Opción adicional
        '{ODBC Driver 17 for SQL Server}'   # Última versión, solo si fallan las anteriores
    ]
    server = 'Concentrador-desarrollo'
 #   server = 'PC-2193' # SERVER PARA PRUEBAS
    database = 'Prestacion'

    for driver in drivers:
        try:
            print(f"Probando conexión con {driver}...")
            conn = pyodbc.connect(
                f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
            )
            print("Conexión exitosa.")
            return conn
        except pyodbc.Error as e:
            print(f"Error al conectar con {driver}: {e}")

    raise Exception("No se pudo conectar a la base de datos con ningún driver.")




