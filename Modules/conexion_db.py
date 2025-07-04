#Modules/conexion_db.py
import pyodbc
from datetime import datetime

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
    Llama a [dbo].[odo_boca_consulta_estados] @idafiliado, @fecha (en base Prestaciones).
    Formatea 'fechaCarga' en dd/mm/aaaa.
    Devuelve lista de dict con llaves en minúsculas.
    """
    conn = get_connection_desarrollo()
    cursor = conn.cursor()
    try:
        sp_name = "[dbo].[odo_boca_consulta_estados]"
        print(f"\n[DEBUG] Ejecutando SP {sp_name} {idafiliado}, '{fecha}'...")
        cursor.execute(f"EXEC {sp_name} ?, ?", (idafiliado, fecha))

        rows = cursor.fetchall()
        if not rows:
            print("[INFO] No se obtuvieron filas.")
            return []

        col_names = [desc[0] for desc in cursor.description]
        print("[DEBUG] Columnas devueltas:", col_names)
        for row in rows:
            print("[DEBUG] Row:", row)

        # Convertimos a dict
        col_lower = [c.lower() for c in col_names]
        result = []
        for r in rows:
            row_dict = {}
            for idx, c in enumerate(col_lower):
                val = r[idx]
                if c == 'fechacarga' and val and isinstance(val, datetime):
                    row_dict[c] = val.strftime("%d/%m/%Y")
                else:
                    row_dict[c] = val
            result.append(row_dict)

        return result
    finally:
        cursor.close()
        conn.close()


def get_odontograma_data(idboca=None):
    """
    Llama a [dbo].[odo_buscaParametrosEstadoBoca] @idBoca (en base Desarrollo).
    Formatea 'fecha' en dd/mm/aaaa.
    Imprime un debug y retorna dict con credencial, afiliado, prestador, fecha, observaciones, dientes.
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

    print(f"[DEBUG] Llamando a: EXEC [dbo].[odo_buscaParametrosEstadoBoca] {idboca} en 'concentrador-desarrollo'...")
    conn = get_connection_desarrollo()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC [dbo].[odo_buscaParametrosEstadoBoca] ?", (idboca,))
        rows = cursor.fetchall()
        if not rows:
            print(f"[WARN] No se encontraron filas para idBoca={idboca}")
            return {
                "credencial": "",
                "afiliado": "",
                "prestador": "",
                "fecha": "",
                "observaciones": "",
                "dientes": ""
            }
        first_row = rows[0]
        # Ajustamos la fecha a dd/mm/aaaa si es datetime
        dt = first_row.fecha
        if dt and isinstance(dt, datetime):
            fecha_str = dt.strftime("%d/%m/%Y")
        else:
            fecha_str = str(dt) if dt else ""

        data = {
            "credencial": str(first_row.credencial or ""),
            "afiliado": str(first_row.afiliado or ""),
            "prestador": str(first_row.prestador or ""),
            "fecha": fecha_str,
            "observaciones": str(first_row.observaciones or ""),
            "dientes": str(first_row.dientes or "")
        }
        print("[DEBUG] SP devolvió:", data)
        return data
    finally:
        cursor.close()
        conn.close()
