"""
Gestor centralizado de iconos con soporte de temas (sin dependencia de QtSvg).
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF
from typing import Dict, Optional
import math


class IconManager:
    """
    Gestor de iconos con soporte de temas.
    Renderiza iconos usando QPainter en lugar de QSvgRenderer.
    """
    
    def __init__(self):
        self._cache: Dict[str, QIcon] = {}
        self._current_theme_colors = {}
    
    def set_theme_colors(self, colors: Dict[str, str]):
        """Actualiza los colores del tema y limpia el caché."""
        self._current_theme_colors = colors
        self._cache.clear()
        print(f"[DEBUG] IconManager: Colores de tema actualizados, caché limpiado")
    
    def get_icon(self, name: str, color: Optional[str] = None, size: int = 24) -> QIcon:
        """
        Obtiene un icono con el color especificado.
        
        Args:
            name: Nombre del icono
            color: Color hexadecimal o nombre de color del tema
            size: Tamaño del icono en píxeles
        
        Returns:
            QIcon generado
        """
        # Resolver color
        if color is None:
            color = self._current_theme_colors.get('text', '#ffffff')
        elif color in self._current_theme_colors:
            color = self._current_theme_colors[color]
        
        # Clave de caché
        cache_key = f"{name}_{color}_{size}"
        
        # Retornar desde caché si existe
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generar nuevo icono
        icon = self._create_icon(name, color, size)
        
        # Guardar en caché
        self._cache[cache_key] = icon
        return icon
    
    def _create_icon(self, name: str, color_hex: str, size: int) -> QIcon:
        """Crea un icono usando QPainter."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Configurar color y grosor
        color = QColor(color_hex)
        pen = QPen(color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Dibujar el icono según el nombre
        self._draw_icon(painter, name, size, color)
        
        painter.end()
        return QIcon(pixmap)
    
    def _draw_icon(self, painter: QPainter, name: str, size: int, color: QColor):
        """Dibuja el icono específico."""
        center = size / 2
        scale = size / 24  # Escala basada en viewBox 24x24
        
        if name == "plus":
            # Línea vertical
            painter.drawLine(int(center), int(size * 0.2), int(center), int(size * 0.8))
            # Línea horizontal
            painter.drawLine(int(size * 0.2), int(center), int(size * 0.8), int(center))
        
        elif name == "edit":
            # Cuadrado
            painter.drawRect(int(size * 0.15), int(size * 0.15), int(size * 0.5), int(size * 0.7))
            # Lápiz
            painter.drawLine(int(size * 0.5), int(size * 0.5), int(size * 0.85), int(size * 0.15))
        
        elif name == "trash":
            # Cuerpo
            painter.drawRect(int(size * 0.25), int(size * 0.35), int(size * 0.5), int(size * 0.5))
            # Tapa
            painter.drawLine(int(size * 0.2), int(size * 0.35), int(size * 0.8), int(size * 0.35))
            # Líneas verticales
            painter.drawLine(int(size * 0.4), int(size * 0.45), int(size * 0.4), int(size * 0.75))
            painter.drawLine(int(size * 0.6), int(size * 0.45), int(size * 0.6), int(size * 0.75))
        
        elif name == "save":
            # Disquete
            painter.drawRect(int(size * 0.2), int(size * 0.15), int(size * 0.6), int(size * 0.7))
            painter.drawRect(int(size * 0.3), int(size * 0.6), int(size * 0.4), int(size * 0.25))
        
        elif name == "refresh":
            # Flecha circular
            painter.drawArc(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6), 45 * 16, 270 * 16)
            # Punta de flecha
            painter.drawLine(int(size * 0.8), int(size * 0.3), int(size * 0.7), int(size * 0.2))
            painter.drawLine(int(size * 0.8), int(size * 0.3), int(size * 0.9), int(size * 0.2))
        
        elif name == "download":
            # Flecha hacia abajo
            painter.drawLine(int(center), int(size * 0.2), int(center), int(size * 0.65))
            painter.drawLine(int(size * 0.35), int(size * 0.5), int(center), int(size * 0.65))
            painter.drawLine(int(size * 0.65), int(size * 0.5), int(center), int(size * 0.65))
            # Línea base
            painter.drawLine(int(size * 0.2), int(size * 0.8), int(size * 0.8), int(size * 0.8))
        
        elif name == "upload":
            # Flecha hacia arriba
            painter.drawLine(int(center), int(size * 0.35), int(center), int(size * 0.8))
            painter.drawLine(int(size * 0.35), int(size * 0.5), int(center), int(size * 0.35))
            painter.drawLine(int(size * 0.65), int(size * 0.5), int(center), int(size * 0.35))
            # Línea base
            painter.drawLine(int(size * 0.2), int(size * 0.2), int(size * 0.8), int(size * 0.2))
        
        elif name == "search":
            # Círculo
            painter.drawEllipse(int(size * 0.25), int(size * 0.25), int(size * 0.4), int(size * 0.4))
            # Mango
            painter.drawLine(int(size * 0.55), int(size * 0.55), int(size * 0.75), int(size * 0.75))
        
        elif name == "filter":
            # Embudo
            painter.drawLine(int(size * 0.2), int(size * 0.2), int(size * 0.8), int(size * 0.2))
            painter.drawLine(int(size * 0.2), int(size * 0.2), int(size * 0.4), int(size * 0.5))
            painter.drawLine(int(size * 0.8), int(size * 0.2), int(size * 0.6), int(size * 0.5))
            painter.drawLine(int(size * 0.4), int(size * 0.5), int(size * 0.4), int(size * 0.8))
            painter.drawLine(int(size * 0.6), int(size * 0.5), int(size * 0.6), int(size * 0.8))
        
        elif name == "x":
            # X
            painter.drawLine(int(size * 0.25), int(size * 0.25), int(size * 0.75), int(size * 0.75))
            painter.drawLine(int(size * 0.75), int(size * 0.25), int(size * 0.25), int(size * 0.75))
        
        elif name == "check":
            # Checkmark
            painter.drawLine(int(size * 0.2), int(center), int(size * 0.4), int(size * 0.7))
            painter.drawLine(int(size * 0.4), int(size * 0.7), int(size * 0.8), int(size * 0.3))
        
        elif name == "info":
            # Círculo
            painter.drawEllipse(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6))
            # i
            painter.drawLine(int(center), int(size * 0.45), int(center), int(size * 0.65))
            painter.drawPoint(int(center), int(size * 0.35))
        
        elif name == "alert-triangle":
            # Triángulo
            painter.drawLine(int(center), int(size * 0.2), int(size * 0.2), int(size * 0.8))
            painter.drawLine(int(size * 0.2), int(size * 0.8), int(size * 0.8), int(size * 0.8))
            painter.drawLine(int(size * 0.8), int(size * 0.8), int(center), int(size * 0.2))
            # !
            painter.drawLine(int(center), int(size * 0.4), int(center), int(size * 0.6))
            painter.drawPoint(int(center), int(size * 0.7))
        
        elif name == "help-circle":
            # Círculo
            painter.drawEllipse(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6))
            # ?
            painter.drawArc(int(size * 0.4), int(size * 0.35), int(size * 0.2), int(size * 0.2), 0, 180 * 16)
            painter.drawLine(int(center), int(size * 0.55), int(center), int(size * 0.6))
            painter.drawPoint(int(center), int(size * 0.7))
        
        elif name == "file":
            # Documento
            painter.drawRect(int(size * 0.3), int(size * 0.2), int(size * 0.4), int(size * 0.6))
            painter.drawLine(int(size * 0.7), int(size * 0.2), int(size * 0.5), int(size * 0.4))
        
        elif name == "file-text":
            # Documento
            painter.drawRect(int(size * 0.3), int(size * 0.2), int(size * 0.4), int(size * 0.6))
            # Líneas de texto
            painter.drawLine(int(size * 0.4), int(size * 0.5), int(size * 0.6), int(size * 0.5))
            painter.drawLine(int(size * 0.4), int(size * 0.6), int(size * 0.6), int(size * 0.6))
        
        elif name == "folder":
            # Carpeta
            painter.drawRect(int(size * 0.2), int(size * 0.4), int(size * 0.6), int(size * 0.4))
            painter.drawLine(int(size * 0.2), int(size * 0.4), int(size * 0.4), int(size * 0.3))
            painter.drawLine(int(size * 0.4), int(size * 0.3), int(size * 0.5), int(size * 0.3))
        
        elif name == "calendar":
            # Calendario
            painter.drawRect(int(size * 0.2), int(size * 0.3), int(size * 0.6), int(size * 0.5))
            painter.drawLine(int(size * 0.2), int(size * 0.45), int(size * 0.8), int(size * 0.45))
            painter.drawLine(int(size * 0.4), int(size * 0.2), int(size * 0.4), int(size * 0.35))
            painter.drawLine(int(size * 0.6), int(size * 0.2), int(size * 0.6), int(size * 0.35))
        
        elif name == "clock":
            # Reloj
            painter.drawEllipse(int(size * 0.2), int(size * 0.2), int(size * 0.6), int(size * 0.6))
            painter.drawLine(int(center), int(center), int(center), int(size * 0.35))
            painter.drawLine(int(center), int(center), int(size * 0.6), int(center))
        
        elif name == "star":
            # Estrella (simplificada)
            painter.drawLine(int(center), int(size * 0.2), int(size * 0.55), int(size * 0.4))
            painter.drawLine(int(size * 0.55), int(size * 0.4), int(size * 0.75), int(size * 0.4))
            painter.drawLine(int(size * 0.75), int(size * 0.4), int(size * 0.6), int(size * 0.6))
            painter.drawLine(int(size * 0.6), int(size * 0.6), int(size * 0.7), int(size * 0.8))
            painter.drawLine(int(size * 0.7), int(size * 0.8), int(center), int(size * 0.7))
            painter.drawLine(int(center), int(size * 0.7), int(size * 0.3), int(size * 0.8))
            painter.drawLine(int(size * 0.3), int(size * 0.8), int(size * 0.4), int(size * 0.6))
            painter.drawLine(int(size * 0.4), int(size * 0.6), int(size * 0.25), int(size * 0.4))
            painter.drawLine(int(size * 0.25), int(size * 0.4), int(size * 0.45), int(size * 0.4))
            painter.drawLine(int(size * 0.45), int(size * 0.4), int(center), int(size * 0.2))
        
        elif name == "eye":
            # Ojo
            painter.drawEllipse(int(size * 0.15), int(size * 0.35), int(size * 0.7), int(size * 0.3))
            painter.drawEllipse(int(size * 0.4), int(size * 0.4), int(size * 0.2), int(size * 0.2))
        
        elif name == "eye-off":
            # Ojo tachado
            painter.drawEllipse(int(size * 0.15), int(size * 0.35), int(size * 0.7), int(size * 0.3))
            painter.drawLine(int(size * 0.2), int(size * 0.2), int(size * 0.8), int(size * 0.8))
        
        elif name == "home":
            # Casa
            painter.drawLine(int(center), int(size * 0.2), int(size * 0.25), int(size * 0.45))
            painter.drawLine(int(center), int(size * 0.2), int(size * 0.75), int(size * 0.45))
            painter.drawRect(int(size * 0.3), int(size * 0.45), int(size * 0.4), int(size * 0.35))
        
        elif name == "list":
            # Lista
            painter.drawLine(int(size * 0.35), int(size * 0.3), int(size * 0.8), int(size * 0.3))
            painter.drawLine(int(size * 0.35), int(center), int(size * 0.8), int(center))
            painter.drawLine(int(size * 0.35), int(size * 0.7), int(size * 0.8), int(size * 0.7))
            painter.drawPoint(int(size * 0.25), int(size * 0.3))
            painter.drawPoint(int(size * 0.25), int(center))
            painter.drawPoint(int(size * 0.25), int(size * 0.7))
        
        elif name == "bar-chart":
            # Gráfico de barras
            painter.drawLine(int(size * 0.3), int(size * 0.8), int(size * 0.3), int(size * 0.6))
            painter.drawLine(int(center), int(size * 0.8), int(center), int(size * 0.4))
            painter.drawLine(int(size * 0.7), int(size * 0.8), int(size * 0.7), int(size * 0.5))
        
        elif name == "settings":
            # Engranaje (simplificado)
            painter.drawEllipse(int(size * 0.35), int(size * 0.35), int(size * 0.3), int(size * 0.3))
            # Dientes
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x = center + math.cos(rad) * size * 0.3
                y = center + math.sin(rad) * size * 0.3
                painter.drawLine(int(center), int(center), int(x), int(y))
        
        else:
            # Icono por defecto (cuadrado)
            painter.drawRect(int(size * 0.3), int(size * 0.3), int(size * 0.4), int(size * 0.4))
    
    def clear_cache(self):
        """Limpia el caché de iconos."""
        self._cache.clear()


# Instancia global
_icon_manager = None


def get_icon_manager() -> IconManager:
    """Obtiene la instancia global del IconManager."""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager