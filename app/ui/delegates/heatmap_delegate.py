"""
Heatmap Delegate - Colorea el fondo según el valor.
"""
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from typing import Optional


class HeatmapDelegate(QStyledItemDelegate):
    """
    Delegate que colorea el fondo según el valor (verde positivo, rojo negativo).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._positive_color = QColor("#00C853")  # Verde
        self._negative_color = QColor("#D50000")  # Rojo
        self._neutral_color = QColor("#3E3E42")   # Gris
        self._text_color = QColor("#FFFFFF")      # Blanco
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        Dibuja la celda con color de fondo según el valor.
        """
        # Obtener valor
        value = index.data(Qt.ItemDataRole.DisplayRole)
        
        # Convertir a float
        try:
            if isinstance(value, str):
                value = value.replace('%', '').strip()
                percentage = float(value)
            elif isinstance(value, (int, float)):
                percentage = float(value)
            else:
                percentage = 0.0
        except:
            percentage = 0.0
        
        # Elegir color según valor
        if percentage > 0:
            bg_color = self._positive_color
        elif percentage < 0:
            bg_color = self._negative_color
        else:
            bg_color = self._neutral_color
        
        # Área de la celda
        rect = option.rect
        
        # Dibujar fondo con transparencia
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Ajustar opacidad según magnitud
        opacity = min(abs(percentage) / 100.0, 0.7)
        bg_color.setAlphaF(opacity)
        
        painter.fillRect(rect, bg_color)
        
        # Dibujar texto
        painter.setPen(QPen(self._text_color))
        text = f"{percentage:+.1f}%" if percentage != 0 else "0.0%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.restore()