"""
Sistema de carga de temas y configuración de iconos.
"""

from PyQt6.QtWidgets import QApplication
from typing import Dict, Optional


# Tema actual (Titanium Construct v2)
THEMES = {
    "titanium_construct_v2": {
        "name": "Titanium Construct v2",
        "colors": {
            "accent": "#7c4dff",
            "text": "#ffffff",
            "text_sec": "#b0b0b0",
            "window": "#1e1e1e",
            "base": "#2D2D30",
            "alt": "#252526",
            "border": "#5E5E62",
            "success": "#00C853",
            "danger": "#FF5252",
            "warning": "#FFA726",
            "info": "#448AFF",
        }
    }
}


def get_theme_colors(theme_name: str = "titanium_construct_v2") -> Dict[str, str]:
    """
    Obtiene los colores del tema especificado.
    
    Args:
        theme_name: Nombre del tema
    
    Returns:
        Diccionario con los colores del tema
    """
    return THEMES.get(theme_name, {}).get("colors", {})


def apply_theme_with_icons(app: Optional[QApplication] = None, theme_name: str = "titanium_construct_v2"):
    """
    Aplica un tema Y configura los iconos SVG.
    
    Args:
        app: QApplication (opcional)
        theme_name: Nombre del tema a aplicar
    """
    # Configurar iconos con los colores del tema
    from app.ui.components.icon_manager import get_icon_manager
    
    colors = get_theme_colors(theme_name)
    icon_manager = get_icon_manager()
    icon_manager.set_theme_colors(colors)
    
    print(f"[INFO] ✓ Iconos SVG configurados con tema {theme_name}")
    
    return colors