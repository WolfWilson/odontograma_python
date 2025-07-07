"""
Conexión a SQL Server y wrappers para SP.
Compatible con SQL Server 2014; usa autenticación de Windows.
"""
import pyodbc
from datetime import datetime

# ───────────────────────── util interno ──────────────────────
def _get_connection(server: str, database: str):
    drivers = [
        '{SQL Server Native Client 10.0}',
        '{SQL Server Native Client 11.0}',
        '{ODBC Driver 13 for SQL Server}',
        '{ODBC Driver 17 for SQL Server}',
    ]
    for drv in drivers:
        try:
            print(f"[INFO] Intentando con {drv} -> {server}\\{database}")
            conn = pyodbc.connect(
                f"DRIVER={drv};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
            )
            print("[OK] Conexión exitosa.")
            return conn
        except pyodbc.Error as e:
            print(f"[WARN] {drv} falló: {e}")
    raise ConnectionError(f"No se pudo conectar a {server}\\{database}")

def get_connection_prestaciones():
    return _get_connection('Concentrador', 'Prestacion')

def get_connection_desarrollo():
    return _get_connection('concentrador-desarrollo', 'Prestacion')

# ─────────────────── SP 1: bocas por prestador ───────────────
def get_bocas_consulta_efector(idafiliado: str, colegio: int,
                               codfact: int, fecha: str) -> list[dict]:
    """
    EXEC [dbo].[odo_boca_consulta_efector]
         @idafiliado, @efectorColegio, @efectorCodFact, @fecha
    Devuelve: idBoca, fechaCarga, efectorColegio, efectorCodFact,
              efector, resumenClinico, …
    """
    conn   = get_connection_prestaciones()
    cursor = conn.cursor()
    try:
        sp = "[dbo].[odo_boca_consulta_efector]"
        print(f"[DEBUG] {sp} {idafiliado}, {colegio}, {codfact}, '{fecha}'")
        cursor.execute(f"EXEC {sp} ?, ?, ?, ?", (idafiliado, colegio, codfact, fecha))
        rows = cursor.fetchall()
        if not rows:
            print("[INFO] Sin resultados.")
            return []

        cols = [desc[0].lower() for desc in cursor.description]
        out  = []
        for r in rows:
            d = {}
            for i, col in enumerate(cols):
                val = r[i]
                if col == 'fechacarga' and isinstance(val, datetime):
                    d[col] = val.strftime("%d/%m/%Y")
                else:
                    d[col] = val
            out.append(d)
        print(f"[DEBUG] Filas obtenidas: {len(out)}")
        return out
    finally:
        cursor.close()
        conn.close()

# ─────────────────── SP 2: detalle de una boca ───────────────
def get_odontograma_data(idboca: int | None = None) -> dict:
    """
    EXEC [dbo].[odo_buscaParametrosEstadoBoca] @idBoca
    Devuelve dict con: credencial, afiliado, prestador, fecha,
                       observaciones, dientes.
    """
    if idboca is None:
        return {
            "credencial":    "",
            "afiliado":      "",
            "prestador":     "",
            "fecha":         "",
            "observaciones": "",
            "dientes":       "",
        }

    print(f"[DEBUG] EXEC [dbo].[odo_buscaParametrosEstadoBoca] {idboca}")
    conn   = get_connection_prestaciones()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC [dbo].[odo_buscaParametrosEstadoBoca] ?", (idboca,))
        rows = cursor.fetchall()
        if not rows:
            print(f"[WARN] idBoca {idboca} no encontrado.")
            return {
                "credencial":    "",
                "afiliado":      "",
                "prestador":     "",
                "fecha":         "",
                "observaciones": "",
                "dientes":       "",
            }

        r0 = rows[0]
        fecha_fmt = (
            r0.fecha.strftime("%d/%m/%Y") if isinstance(r0.fecha, datetime) else str(r0.fecha)
        )

        return {
            "credencial":    str(r0.credencial or ""),
            "afiliado":      str(r0.afiliado   or ""),
            "prestador":     str(r0.prestador  or ""),
            "fecha":         fecha_fmt,
            "observaciones": str(r0.observaciones or ""),
            "dientes":       str(r0.dientes or ""),
        }
    finally:
        cursor.close()
        conn.close()

# ──────────── Alias de compatibilidad para vistas viejas ─────
get_bocas_consulta_estados = get_bocas_consulta_efector
