#!/usr/bin/env python
# coding: utf-8

import sys
import os

# Diccionario de ESTADOS
ESTADOS = {
    "Ninguno": 0,
    "Obturacion": 1,
    "Agenesia": 2,
    "PD Ausente": 3,
    "Corona": 4,
    "Implante": 5,
    "Puente": 6,
    "Selladores": 7,
    "Ausente Fisiológico": 8,
    "Prótesis Removible SUPERIOR": 9,
    "Prótesis Removible INFERIOR": 10,
    "Prótesis Completa SUPERIOR": 11,
    "Prótesis Completa INFERIOR": 12,
    "Supernumerario": 13
}

# Mapeo inverso para ir de número a string
ESTADOS_POR_NUM = {v: k for k, v in ESTADOS.items()}


def resource_path(relative_path: str) -> str:
    """
    Retorna la ruta absoluta del recurso, compatible con PyInstaller y modo desarrollo.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def parse_dental_states(dental_str):
    """
    A partir de un string con formato p.ej. "111,212V,313D", devuelve
    una lista de tuplas (estado_int, diente_int, caras_str).
    """
    if not dental_str:
        return []
    items = [x.strip() for x in dental_str.split(",") if x.strip()]
    parsed_list = []
    for item in items:
        p = parse_item_with_backtracking(item)
        if p:
            parsed_list.append(p)
        else:
            print(f"WARNING: No se pudo interpretar: {item}")
    return parsed_list


def parse_item_with_backtracking(item_str):
    """
    Intenta parsear un item que contiene estado (1 o 2 dígitos),
    luego el número de diente (2 dígitos) y luego las caras (opcional).
    """
    # Intenta 2 dígitos de estado
    if len(item_str) >= 4:
        try:
            st_candidate = item_str[:2]
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:
                d_candidate = item_str[2:4]
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    faces = item_str[4:].upper()
                    return (st_int, d_int, faces)
        except:
            pass

    # Intenta 1 dígito de estado
    if len(item_str) >= 3:
        try:
            st_candidate = item_str[0]
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:
                d_candidate = item_str[1:3]
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    faces = item_str[3:].upper()
                    return (st_int, d_int, faces)
        except:
            pass

    return None
