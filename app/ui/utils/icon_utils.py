"""
Utilidades para iconos SVG.
Funciones helper para facilitar el uso del IconManager en toda la aplicación.
"""

from PyQt6.QtGui import QIcon
from typing import Optional


def icon(name: str, color: Optional[str] = None, size: int = 20) -> QIcon:
    """
    Atajo para obtener un icono SVG.
    
    Args:
        name: Nombre del icono
        color: Color (nombre del tema o hexadecimal)
        size: Tamaño en píxeles
    
    Returns:
        QIcon
    
    Examples:
        >>> icon("home")  # Icono home con color de texto del tema
        >>> icon("plus", "accent")  # Icono plus con color accent
        >>> icon("trash", "danger", 24)  # Icono trash rojo de 24px
    """
    from app.ui.components.icon_manager import get_icon_manager
    return get_icon_manager().get_icon(name, color, size)


# Atajos para iconos comunes
def home_icon() -> QIcon:
    return icon("home")


def list_icon() -> QIcon:
    return icon("list")


def chart_icon() -> QIcon:
    return icon("bar-chart")


def settings_icon() -> QIcon:
    return icon("settings")


def add_icon(color: str = "accent") -> QIcon:
    return icon("plus", color)


def edit_icon(color: str = "info") -> QIcon:
    return icon("edit", color)


def delete_icon(color: str = "danger") -> QIcon:
    return icon("trash", color)


def save_icon(color: str = "success") -> QIcon:
    return icon("save", color)


def refresh_icon() -> QIcon:
    return icon("refresh", "accent")


def download_icon() -> QIcon:
    return icon("download", "info")


def upload_icon() -> QIcon:
    return icon("upload", "info")


def search_icon() -> QIcon:
    return icon("search")


def filter_icon() -> QIcon:
    return icon("filter")


def close_icon() -> QIcon:
    return icon("x")


def check_icon(color: str = "success") -> QIcon:
    return icon("check", color)


def info_icon(color: str = "info") -> QIcon:
    return icon("info", color)


def warning_icon(color: str = "warning") -> QIcon:
    return icon("alert-triangle", color)


def help_icon() -> QIcon:
    return icon("help-circle")


def file_icon() -> QIcon:
    return icon("file")


def folder_icon() -> QIcon:
    return icon("folder")


def calendar_icon() -> QIcon:
    return icon("calendar")


def clock_icon() -> QIcon:
    return icon("clock")


def star_icon(color: str = "warning") -> QIcon:
    return icon("star", color)


def eye_icon() -> QIcon:
    return icon("eye")