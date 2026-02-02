"""
Simple Progress Bar Delegate - Barra de progreso simple de 0% a 100%.
"""
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class SimpleProgressBarDelegate(QStyledItemDelegate):
    """
    Delegate que dibuja una barra de progreso simple de izquierda a derecha (0-100%).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar_color = QColor("#7C4DFF")       # Morado
        self._bg_color = QColor("#3E3E42")        # Gris oscuro
        self._text_color = QColor("#FFFFFF")      # Blanco
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        Dibuja la barra de progreso de 0% a 100%.
        """
        # Obtener valor
        value = index.data(Qt.ItemDataRole.DisplayRole)
        
        # Convertir a porcentaje (0-100)
        try:
            if isinstance(value, str):
                value_clean = value.replace('%', '').replace('+', '').strip()
                percentage = float(value_clean)
            elif isinstance(value, (int, float)):
                percentage = float(value) * 100 if 0 <= value <= 1 else float(value)
            else:
                percentage = 0.0
        except (ValueError, AttributeError):
            percentage = 0.0
        
        # Limitar entre 0-100
        percentage = max(0.0, min(100.0, percentage))
        
        # Área de la celda
        rect = option.rect
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar fondo gris
        painter.fillRect(rect, self._bg_color)
        
        # Calcular ancho de la barra (de izquierda a derecha)
        bar_margin = 4
        max_bar_width = rect.width() - (bar_margin * 2)
        bar_width = int(max_bar_width * (percentage / 100.0))
        
        # Dibujar barra de progreso
        bar_rect = QRect(
            rect.x() + bar_margin,
            rect.y() + bar_margin,
            bar_width,
            rect.height() - (bar_margin * 2)
        )
        
        painter.setBrush(QBrush(self._bar_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, 3, 3)
        
        # Dibujar texto del porcentaje centrado
        painter.setPen(QPen(self._text_color))
        text = f"{percentage:.1f}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.restore()
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """Sugiere altura mínima."""
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 28))
        return size