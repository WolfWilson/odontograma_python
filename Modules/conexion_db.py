import pyodbc

def get_connection_prestaciones():
    drivers = [
        '{SQL Server Native Client 10.0}',
        '{SQL Server Native Client 11.0}',
        '{ODBC Driver 13 for SQL Server}',
        '{ODBC Driver 17 for SQL Server}'
    ]
    server = 'Concentrador'  # Ajusta
    database = 'Prestacion'

    for driver in drivers:
        try:
            print(f"Probando conexión con {driver} para Prestaciones...")
            conn = pyodbc.connect(
                f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
            )
            print("[OK] Conexión Prestaciones exitosa.")
            return conn
        except pyodbc.Error as e:
            print(f"Error al conectar con {driver}: {e}")

    raise Exception("No se pudo conectar a la base Prestaciones")


def get_connection_desarrollo():
    drivers = [
        '{SQL Server Native Client 10.0}',
        '{SQL Server Native Client 11.0}',
        '{ODBC Driver 13 for SQL Server}',
        '{ODBC Driver 17 for SQL Server}'
    ]
    server = 'concentrador-desarrollo'  # Ajusta
    database = 'Prestacion'

    for driver in drivers:
        try:
            print(f"Probando conexión con {driver} para Desarrollo...")
            conn = pyodbc.connect(
                f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
            )
            print("[OK] Conexión Desarrollo exitosa.")
            return conn
        except pyodbc.Error as e:
            print(f"Error al conectar con {driver}: {e}")

    raise Exception("No se pudo conectar a la base Desarrollo")


def get_bocas_consulta_estados(idafiliado, fecha):
    """
    Llama a [dbo].[odo_boca_consulta_estados] @idafiliado, @fecha
    en la base Prestaciones (Concentrador).
    Imprime columnas y filas en consola, y retorna la lista de dict.
    """
    conn = get_connection_prestaciones()
    cursor = conn.cursor()
    try:
        sp_name = "[dbo].[odo_boca_consulta_estados]"
        print(f"\nEjecutando SP {sp_name} {idafiliado}, '{fecha}'...")
        cursor.execute(f"EXEC {sp_name} ?, ?", (idafiliado, fecha))

        rows = cursor.fetchall()
        if not rows:
            print("[INFO] No se obtuvieron filas.")
            return []

        # Imprimimos columnas y filas
        col_names = [desc[0] for desc in cursor.description]
        print("Columnas:", col_names)
        for row in rows:
            print(row)

        # Convertimos cada fila en dict
        col_lower = [c.lower() for c in col_names]
        result = []
        for r in rows:
            row_dict = {}
            for idx, c in enumerate(col_lower):
                row_dict[c] = r[idx]
            result.append(row_dict)

        return result
    finally:
        cursor.close()
        conn.close()


def get_odontograma_data(idboca=None):
    """
    Llama a SP [dbo].[odo_buscaParametrosEstadoBoca] @idBoca
    en la base Desarrollo
    """
    if idboca is None:
        return {
            "credencial": "",
            "afiliado": "",
            "prestador": "",
            "fecha": "",
            "observaciones": "",
            "dientes": ""
        }

    conn = get_connection_desarrollo()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC [dbo].[odo_buscaParametrosEstadoBoca] ?", (idboca,))
        rows = cursor.fetchall()
        if not rows:
            print(f"No se encontraron filas para idBoca={idboca}")
            return {
                "credencial": "",
                "afiliado": "",
                "prestador": "",
                "fecha": "",
                "observaciones": "",
                "dientes": ""
            }
        first_row = rows[0]
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


#python odontograma.py 354495 "01/03/2025" "ODONTOLOGO DE PRUEBA COCH" 333