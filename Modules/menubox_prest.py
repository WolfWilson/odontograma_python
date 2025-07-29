#!/usr/bin/env python
# coding: utf-8
"""
menubox_prest.py – construcción de paneles de estados
"""

from __future__ import annotations
from typing import Callable, Dict, Optional, Set

from Modules.menu_estados import MenuEstados

# ───────── base de iconos ──────────────────────────────────
_PROTESIS_BASE = {
    "Prótesis Removible SUPERIOR": "icon_prs",
    "Prótesis Removible INFERIOR": "icon_pri",
    "Prótesis Completa SUPERIOR":  "icon_pcs",
    "Prótesis Completa INFERIOR":  "icon_pci",
}
_OTHER_ICONS = {
    "Obturacion":          "icon_obturacion.png",
    "Agenesia":            "icon_agenesia.png",
    "PD Ausente":          "icon_pd_ausente.png",
    "Corona":              "icon_corona.png",
    "Implante":            "icon_implante.png",
    "Puente":              "icon_puente.png",
    "Selladores":          "icon_selladores.png",
    "Ausente Fisiológico": "icon_ausente_fisio.png",
    "Caries":              "icon_cariesR.png",
    "Extracción":          "icon_extraccionR.png",
}

# Conjuntos exportados ──────────────────────────────────────
_PROTESIS_B = {f"{k}_B" for k in _PROTESIS_BASE}
_PROTESIS_R = {f"{k}_R" for k in _PROTESIS_BASE}

REQUERIDAS_FULL_SET: Set[str] = _PROTESIS_B | {"Caries", "Extracción"}
_EXISTENTES_EXCLUDE: Set[str] = {"Supernumerario"} | REQUERIDAS_FULL_SET

# ───────── helpers ─────────────────────────────────────────
def _build_icon_dict(
    *,
    prosthesis_suffix: str,
    include: Optional[Set[str]] = None,
    exclude: Optional[Set[str]] = None,
) -> Dict[str, str]:
    def _ok(name: str) -> bool:
        if include and name not in include:
            return False
        if exclude and name in exclude:
            return False
        return True

    d: Dict[str, str] = {}
    # íconos “normales”
    for n, f in _OTHER_ICONS.items():
        if _ok(n):
            d[n] = f
    # prótesis
    for base, prefix in _PROTESIS_BASE.items():
        full = f"{base}_{prosthesis_suffix}"
        if _ok(full):
            d[full] = f"{prefix}{prosthesis_suffix}.png"
    return d

# ───────── paneles listos ──────────────────────────────────
def get_menu_existentes(cb, *, locked=False) -> MenuEstados:
    dic = _build_icon_dict(
        prosthesis_suffix="R",
        exclude=_EXISTENTES_EXCLUDE,
    )
    return MenuEstados(cb, locked=locked,
                       title="Prestaciones Existentes",
                       icon_dict=dic)

def get_menu_requeridas(cb, *, locked=False) -> MenuEstados:
    dic = _build_icon_dict(
        prosthesis_suffix="B",
        include=REQUERIDAS_FULL_SET,
    )
    return MenuEstados(cb, locked=locked,
                       title="Prestaciones Requeridas",
                       icon_dict=dic)
