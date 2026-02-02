"""
Progress Bar Delegate - Barra de progreso centrada para valores positivos/negativos.
"""
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class ProgressBarDelegate(QStyledItemDelegate):
    """
    Delegate que dibuja una barra de progreso centrada.
    - Valores positivos: barra morada hacia la derecha
    - Valores negativos: barra roja hacia la izquierda
    - Línea central como referencia del 0%
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar_color_positive = QColor("#00C853")  # Verde para positivos
        self._bar_color_negative = QColor("#FF5252")  # Rojo para negativos
        self._bg_color = QColor("#3E3E42")            # Gris oscuro
        self._text_color = QColor("#FFFFFF")          # Blanco
        self._center_line_color = QColor("#5E5E62")   # Gris claro para línea central
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        Dibuja la barra de progreso centrada.
        """
        # Obtener valor
        value = index.data(Qt.ItemDataRole.DisplayRole)
        
        # Convertir a porcentaje numérico
        try:
            if isinstance(value, str):
                value_clean = value.replace('%', '').strip()
                percentage = float(value_clean)
            elif isinstance(value, (int, float)):
                if -1 <= value <= 1:
                    percentage = float(value) * 100
                else:
                    percentage = float(value)
            else:
                percentage = 0.0
        except (ValueError, AttributeError):
            percentage = 0.0
        
        # Área de la celda
        rect = option.rect
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar fondo gris
        painter.fillRect(rect, self._bg_color)
        
        # Calcular posiciones
        bar_margin = 4
        max_bar_width = (rect.width() - (bar_margin * 2)) // 2  # Mitad del espacio
        center_x = rect.x() + (rect.width() // 2)
        bar_y = rect.y() + bar_margin
        bar_height = rect.height() - (bar_margin * 2)
        
        # Limitar porcentaje a -100% / +100%
        clamped_percentage = max(-100.0, min(100.0, percentage))
        
        # Calcular ancho de barra según porcentaje
        bar_width = int(max_bar_width * abs(clamped_percentage) / 100.0)
        
        # Determinar color y posición según signo
        if clamped_percentage >= 0:
            bar_color = self._bar_color_positive
            bar_rect = QRect(center_x, bar_y, bar_width, bar_height)
        else:
            bar_color = self._bar_color_negative
            bar_rect = QRect(center_x - bar_width, bar_y, bar_width, bar_height)
        
        # Dibujar barra
        painter.setBrush(QBrush(bar_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, 3, 3)
        
        # Dibujar línea central (referencia 0%)
        painter.setPen(QPen(self._center_line_color, 1, Qt.PenStyle.DashLine))
        painter.drawLine(center_x, rect.y() + 2, center_x, rect.y() + rect.height() - 2)
        
        # Dibujar texto del porcentaje centrado
        painter.setPen(QPen(self._text_color))
        if percentage > 0:
            text = f"+{percentage:.1f}%"
        elif percentage < 0:
            text = f"{percentage:.1f}%"
        else:
            text = "0.0%"
        
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.restore()
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """Sugiere altura mínima."""
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 28))
        return size