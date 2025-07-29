#!/usr/bin/env python
# coding: utf-8
"""
menubox_prest.py

Genera los paneles de prestaciones:
    • get_menu_existentes(...)   → variantes rojas  (_R)
    • get_menu_requeridas(...)   → variantes azules (_B)
"""

from __future__ import annotations
from typing import Callable, Dict, Optional, Set

from Modules.menu_estados import MenuEstados
from Modules.utils        import resource_path


# ──────────────────────────────────────────────────────────────
# Estados base y prefijos de icono
# ──────────────────────────────────────────────────────────────
_PROTESIS_PREFIX = {
    "Prótesis Removible SUPERIOR":  "icon_prs",
    "Prótesis Removible INFERIOR":  "icon_pri",
    "Prótesis Completa SUPERIOR":   "icon_pcs",
    "Prótesis Completa INFERIOR":   "icon_pci",
}

_NON_PROTESIS_ICONS = {
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
    # "Supernumerario":    "icon_supernumerario.png",
}

_PROTESIS: Set[str] = set(_PROTESIS_PREFIX.keys())
REQUERIDAS_SET      = _PROTESIS | {"Caries", "Extracción"}
_EXISTENTES_EXCL    = {"Supernumerario", "Caries", "Extracción"}


# ──────────────────────────────────────────────────────────────
def _build_icon_dict(
    *,
    prosthesis_suffix: str,
    include: Optional[Set[str]] = None,
    exclude: Optional[Set[str]] = None,
) -> Dict[str, str]:
    """
    Devuelve dict estado→icono aplicando:
      · sufijo de prótesis (_R / _B)
      · filtros include / exclude sobre el nombre base
    """
    def _allowed(base: str) -> bool:
        if include and base not in include:
            return False
        if exclude and base in exclude:
            return False
        return True

    icons: Dict[str, str] = {}

    # Estados no-prótesis
    for name, file in _NON_PROTESIS_ICONS.items():
        if _allowed(name):
            icons[name] = file

    # Prótesis
    for base, prefix in _PROTESIS_PREFIX.items():
        if not _allowed(base):
            continue
        full_state = f"{base}_{prosthesis_suffix}"
        icons[full_state] = f"{prefix}{prosthesis_suffix}.png"

    return icons


# ──────────────────────────────────────────────────────────────
# Paneles listos para usar en views.py
# ──────────────────────────────────────────────────────────────
def get_menu_existentes(on_click: Callable[[str], None], *, locked: bool = False) -> MenuEstados:
    """Panel «Prestaciones Existentes» – variante roja (_R)."""
    icon_dict = _build_icon_dict(
        prosthesis_suffix="R",
        exclude=_EXISTENTES_EXCL,
    )
    return MenuEstados(on_click, locked=locked,
                       title="Prestaciones Existentes",
                       icon_dict=icon_dict)


def get_menu_requeridas(on_click: Callable[[str], None], *, locked: bool = False) -> MenuEstados:
    """Panel «Prestaciones Requeridas» – variante azul (_B)."""
    icon_dict = _build_icon_dict(
        prosthesis_suffix="B",      # ← ★ cambio clave: antes era "_A"
        include=REQUERIDAS_SET,
    )
    return MenuEstados(on_click, locked=locked,
                       title="Prestaciones Requeridas",
                       icon_dict=icon_dict)
