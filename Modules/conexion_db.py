#!/usr/bin/env python
# coding: utf-8
"""
Módulo de conexión a SQL Server.
Prioridad a los drivers que probaste y funcionan.
"""

import os
import pyodbc
from datetime import datetime
from functools import lru_cache
from typing import List

# ─── 1. Orden preferente de drivers comprobados ────────────────────
_PREFERRED_ORDER = (
    "SQL Server",
    "SQL Server Native Client 11.0",
    "ODBC Driver 11 for SQL Server",
    "ODBC Driver 17 for SQL Server",
)

def _installed_sql_drivers() -> List[str]:
    raw = pyodbc.drivers()
    normalized = [d if d.startswith("{") else f"{{{d}}}" for d in raw]
    print(f"[DEBUG] Drivers ODBC detectados: {normalized}")
    return normalized

def _ordered_drivers() -> List[str]:
    installed = _installed_sql_drivers()
    preferred = [f"{{{d}}}" for d in _PREFERRED_ORDER if f"{{{d}}}" in installed]
    others    = [d for d in installed if d not in preferred]
    order = preferred + others
    print(f"[DEBUG] Orden de prueba de drivers: {order}")
    return order

@lru_cache(maxsize=4)
def _find_working_driver(server: str, database: str) -> str:
    # Permite forzar un driver concreto con la variable SQL_DRIVER
    env_drv = os.getenv("SQL_DRIVER")
    if env_drv:
        drv = env_drv if env_drv.startswith("{") else f"{{{env_drv}}}"
        print(f"[INFO] Forzando driver por env: {drv}")
        return drv

    for drv in _ordered_drivers():
        try:
            print(f"[INFO] Probando driver {drv} → servidor={server}, base={database}")
            pyodbc.connect(
                f"DRIVER={drv};SERVER={server};DATABASE={database};Trusted_Connection=yes;",
                timeout=3
            ).close()
            print(f"[OK] Driver válido: {drv}")
            return drv
        except pyodbc.Error as e:
            print(f"[WARN] {drv} falló: {e}")

    raise ConnectionError(f"Ningún driver ODBC válido para {server}/{database}")

# ─── 2. Función genérica de conexión ───────────────────────────────

def _get_connection(server: str, database: str) -> pyodbc.Connection:
    drv = _find_working_driver(server, database)
    return pyodbc.connect(
        f"DRIVER={drv};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    )

# ─── 3. Atajos para tus bases habituales ───────────────────────────

def get_connection_prestaciones() -> pyodbc.Connection:
    return _get_connection("Concentrador", "Prestacion")

def get_connection_desarrollo() -> pyodbc.Connection:
    return _get_connection("concentrador-desarrollo", "Prestacion")

# ─── 4. Wrappers para tus SP (sin modificar lógica) ───────────────

def get_bocas_consulta_efector(
    idafiliado: str,
    colegio: int,
    codfact: int,
    fecha: str,
) -> list[dict]:
    conn   = get_connection_prestaciones()
    cursor = conn.cursor()
    try:
        sp = "[dbo].[odo_boca_consulta_efector]"
        print(f"[DEBUG] Ejecutando: {sp} {idafiliado}, {colegio}, {codfact}, '{fecha}'")
        cursor.execute(f"EXEC {sp} ?, ?, ?, ?", (idafiliado, colegio, codfact, fecha))
        rows = cursor.fetchall()
        if not rows:
            print("[INFO] Sin resultados.")
            return []

        cols = [d[0].lower() for d in cursor.description]
        out  = []
        for r in rows:
            d = {}
            for i, col in enumerate(cols):
                val = r[i]
                if col == "fechacarga" and isinstance(val, datetime):
                    d[col] = val.strftime("%d/%m/%Y")
                else:
                    d[col] = val
            out.append(d)
        print(f"[DEBUG] Filas obtenidas: {len(out)}")
        return out
    finally:
        cursor.close()
        conn.close()

def get_odontograma_data(idboca: int | None = None) -> dict:
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
                "credencial": "", "afiliado": "",
                "prestador": "", "fecha": "",
                "observaciones": "", "dientes": "",
            }

        r = rows[0]
        fecha_fmt   = r.fecha.strftime("%d/%m/%Y") if isinstance(r.fecha, datetime) else str(r.fecha)
        dientes_str = str(r.dientes or "")
        print(f"[DEBUG] Dientes (idBoca={idboca}): {dientes_str}")
        return {
            "credencial":    str(r.credencial or ""),
            "afiliado":      str(r.afiliado   or ""),
            "prestador":     str(r.prestador  or ""),
            "fecha":         fecha_fmt,
            "observaciones": str(r.observaciones or ""),
            "dientes":       dientes_str,
        }
    finally:
        cursor.close()
        conn.close()

# Alias para compatibilidad con código antiguo
get_bocas_consulta_estados = get_bocas_consulta_efector
