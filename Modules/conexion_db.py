# Modules/conexion_db.py
import pyodbc

def get_connection():
    drivers = [
        '{SQL Server Native Client 10.0}',
        '{SQL Server Native Client 11.0}',
        '{ODBC Driver 13 for SQL Server}',
        '{ODBC Driver 17 for SQL Server}'
    ]
    server = 'Concentrador-desarrollo'
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


def get_odontograma_data(numero=None):
    """
    - Si numero is None => Diccionario vacío (sin datos).
    - Si numero tiene valor => llama al SP y:
      1) Imprime por consola el result set completo (columnas + filas).
      2) Retorna la información de la primera fila en un diccionario.
    """
    # Caso sin número => interfaz en blanco
    if numero is None:
        return {
            "credencial": "",
            "afiliado": "",
            "prestador": "",
            "fecha": "",
            "observaciones": "",
            "dientes": ""
        }

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Ejecuta el SP
        cursor.execute("EXEC odo_buscaParametrosEstadoBoca ?", (numero,))

        try:
            # Obtenemos todas las filas
            rows = cursor.fetchall()
        except pyodbc.ProgrammingError:
            # El SP no devolvió SELECT
            print("El SP no devolvió un SELECT. No hay result set.")
            rows = []

        # Si no hay filas, retornamos vacío
        if not rows:
            print("No se encontraron filas. Interface vacía.")
            return {
                "credencial": "",
                "afiliado": "",
                "prestador": "",
                "fecha": "",
                "observaciones": "",
                "dientes": ""
            }

        # Imprimir columnas y filas en consola
        col_names = [desc[0] for desc in cursor.description]
        print("\n--- Resultado del SP ---")
        print("\t".join(col_names))
        for row in rows:
            print("\t".join(str(x) for x in row))
        print("--- Fin del resultado ---\n")

        # Tomamos solo la primera fila para armar el diccionario
        first_row = rows[0]

        # Usamos índice o getattr(), según cómo quieras acceder
        # Supongamos que las columnas se llaman [credencial, afiliado, prestador, fecha, observaciones, dientes]
        return {
            "credencial": str(first_row.credencial or ""),
            "afiliado": str(first_row.afiliado or ""),
            "prestador": str(first_row.prestador or ""),
            "fecha": str(first_row.fecha) if first_row.fecha else "",
            "observaciones": str(first_row.observaciones or ""),
            "dientes": str(first_row.dientes or "")
        }

    finally:
        cursor.close()
        conn.close()
