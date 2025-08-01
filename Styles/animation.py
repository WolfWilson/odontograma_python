# Styles/animation.py
"""
Módulo para aplicar animaciones y efectos gráficos a los widgets de la aplicación.
"""
from typing import Optional
from PyQt5.QtWidgets import QToolButton, QGraphicsColorizeEffect
from PyQt5.QtCore import QEvent, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor

def apply_button_colorize_animation(button: QToolButton):
    """
    Aplica una animación que tiñe el ícono del botón con un color de acento
    al pasar el mouse por encima.
    """
    colorize_effect = QGraphicsColorizeEffect(button)
    colorize_effect.setColor(QColor("#4682b4"))
    colorize_effect.setStrength(0.0)
    button.setGraphicsEffect(colorize_effect)

    button.animation = QPropertyAnimation(colorize_effect, b"strength")
    button.animation.setDuration(300)
    button.animation.setEasingCurve(QEasingCurve.InOutCubic)

    original_enterEvent = button.enterEvent
    original_leaveEvent = button.leaveEvent

    # CORREGIDO: Se cambia el nombre del parámetro de 'event' a 'a0'
    def new_enterEvent(a0: Optional[QEvent]) -> None:
        button.animation.setStartValue(colorize_effect.strength())
        button.animation.setEndValue(0.7)
        button.animation.start()
        original_enterEvent(a0)

    # CORREGIDO: Se cambia el nombre del parámetro de 'event' a 'a0'
    def new_leaveEvent(a0: Optional[QEvent]) -> None:
        button.animation.setStartValue(colorize_effect.strength())
        button.animation.setEndValue(0.0)
        button.animation.start()
        original_leaveEvent(a0)

    button.enterEvent = new_enterEvent
    button.leaveEvent = new_leaveEvent