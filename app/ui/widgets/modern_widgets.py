"""
Modern UI Widgets for Titanium Construct v2 Theme.
Componentes reutilizables para el dashboard moderno.
"""
from __future__ import annotations
from typing import Optional, Callable

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

class StatCard(QFrame):
    """
    Tarjeta de estadística con título, valor grande, ícono y barra de color decorativa.
    Usada en el dashboard para mostrar métricas clave.
    """
    
    def __init__(
        self, 
        title: str, 
        value: str, 
        accent_color: str = "#7C4DFF",
        icon_text: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Inicializa una tarjeta de estadística.
        
        Args:
            title: Título de la métrica (ej: "Total Activas")
            value: Valor a mostrar (ej: "8" o "47")
            accent_color: Color de la barra decorativa inferior
            icon_text: Texto del ícono (opcional)
            parent: Widget padre
        """
        super().__init__(parent)
        self._title = title
        self._value = value
        self._accent_color = accent_color
        self._icon_text = icon_text
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de la tarjeta."""
        self.setObjectName("StatCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(120)
        
        # Aplicar estilo específico
        self.setStyleSheet(f"""
            #StatCard {{
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 12px;
                border-bottom: 3px solid {self._accent_color};
                padding: 20px;
            }}
            #StatCard:hover {{
                border: 1px solid #4E4E52;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel(self._title)
        title_label.setStyleSheet("""
            font-size: 12px;
            color: #B0B0B0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(self._value)
        value_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF;
        """)
        layout.addWidget(value_label)
        
        layout.addStretch()
    
    def update_value(self, new_value: str) -> None:
        """
        Actualiza el valor mostrado en la tarjeta.
        
        Args:
            new_value: Nuevo valor a mostrar
        """
        self._value = new_value
        # Buscar el label del valor y actualizarlo
        for child in self.findChildren(QLabel):
            if child.font().pointSize() >= 32 or "font-size: 32px" in child.styleSheet():
                child.setText(new_value)
                break


class StatusBadge(QLabel):
    """
    Badge de estado con fondo semitransparente y bordes redondeados.
    Usado para mostrar estados en tablas (ej: "En curso", "Ganada", "Perdida").
    """
    
    # Estilos predefinidos por tipo de estado
    STYLES = {
        "success": {
            "bg": "rgba(0, 200, 83, 0.15)",
            "color": "#00C853",
            "border": "#00C853"
        },
        "warning": {
            "bg": "rgba(255, 171, 0, 0.15)",
            "color": "#FFAB00",
            "border": "#FFAB00"
        },
        "error": {
            "bg": "rgba(213, 0, 0, 0.15)",
            "color": "#D50000",
            "border": "#D50000"
        },
        "info": {
            "bg": "rgba(68, 138, 255, 0.15)",
            "color": "#448AFF",
            "border": "#448AFF"
        },
        "default": {
            "bg": "rgba(176, 176, 176, 0.15)",
            "color": "#B0B0B0",
            "border": "#3E3E42"
        }
    }
    
    def __init__(
        self, 
        text: str, 
        status_type: str = "default",
        parent: Optional[QWidget] = None
    ):
        """
        Inicializa un badge de estado.
        
        Args:
            text: Texto a mostrar
            status_type: Tipo de estado ("success", "warning", "error", "info", "default")
            parent: Widget padre
        """
        super().__init__(text, parent)
        self._status_type = status_type
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Aplica el estilo al badge."""
        style = self.STYLES.get(self._status_type, self.STYLES["default"])
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {style['bg']};
                color: {style['color']};
                border: 1px solid {style['border']};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        self.setMinimumWidth(80)
        self.setMaximumHeight(24)


class ModernProgressBar(QWidget):
    """
    Barra de progreso delgada y estilizada con porcentaje al lado.
    Usado para mostrar progreso de documentos en tablas.
    """
    
    def __init__(
        self, 
        value: int = 0, 
        color: str = "#448AFF",
        parent: Optional[QWidget] = None
    ):
        """
        Inicializa una barra de progreso moderna.
        
        Args:
            value: Valor del progreso (0-100)
            color: Color de la barra de progreso
            parent: Widget padre
        """
        super().__init__(parent)
        self._value = value
        self._color = color
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de la barra de progreso."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self._value)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #121212;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 3px;
            }}
        """)
        
        # Label de porcentaje
        self.percentage_label = QLabel(f"{self._value}%")
        self.percentage_label.setStyleSheet("""
            font-size: 11px;
            color: #FFFFFF;
            min-width: 35px;
        """)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.progress_bar, 1)
        layout.addWidget(self.percentage_label, 0)
    
    def set_value(self, value: int) -> None:
        """
        Actualiza el valor de la barra de progreso.
        
        Args:
            value: Nuevo valor (0-100)
        """
        self._value = max(0, min(100, value))
        self.progress_bar.setValue(self._value)
        self.percentage_label.setText(f"{self._value}%")


class ModernSidebar(QFrame):
    """
    Sidebar de navegación moderno con ítems clicables.
    """
    
    # Señal que emite el ID del item seleccionado
    item_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernSidebar")
        self.setFixedWidth(200)
        self.setStyleSheet("""
            #ModernSidebar {
                background-color: #252526;
                border-right: 1px solid #3E3E42;
            }
        """)
        
        # Layout principal
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 20, 0, 20)
        self._layout.setSpacing(5)
        
        # Header/Logo
        self._create_header()
        
        # Lista de items de navegación
        self._items = {}  # {item_id: QPushButton}
        self._current_item = None
        
        # Spacer al final
        self._layout.addStretch()
    
    def _create_header(self):
        """Crea el header del sidebar con logo/título."""
        header = QLabel("LICITA MANAGE")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: #7C4DFF;
                font-size: 16px;
                font-weight: bold;
                padding: 20px 10px;
                border-bottom: 1px solid #3E3E42;
            }
        """)
        self._layout.addWidget(header)
        self._layout.addSpacing(20)
    
    def add_navigation_item(self, item_id: str, label: str, icon_text: str = ""):
        """
        Añade un item de navegación al sidebar.
        
        Args:
            item_id: ID único del item
            label: Texto a mostrar
            icon_text: Emoji o texto como ícono (opcional)
        """
        from PyQt6.QtGui import QCursor  # ✅ Import local
        
        btn = QPushButton(f"{icon_text}  {label}" if icon_text else label)
        btn.setObjectName(f"nav_item_{item_id}")
        
        # ✅ CORRECCIÓN: Usar QCursor con Qt.CursorShape
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #B0B0B0;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #37373D;
                color: #7C4DFF;
                border-left: 3px solid #7C4DFF;
                padding-left: 17px;
            }
        """)
        btn.setCheckable(True)
        
        # Conectar señal
        btn.clicked.connect(lambda checked, iid=item_id: self._on_item_clicked(iid))
        
        self._items[item_id] = btn
        self._layout.insertWidget(self._layout.count() - 1, btn)
    
    def _on_item_clicked(self, item_id: str):
        """Maneja el clic en un item de navegación."""
        # Desmarcar todos los items
        for btn in self._items.values():
            btn.setChecked(False)
        
        # Marcar el item actual
        if item_id in self._items:
            self._items[item_id].setChecked(True)
            self._current_item = item_id
        
        # Emitir señal
        self.item_selected.emit(item_id)
    
    def select_item(self, item_id: str):
        """
        Selecciona un item programáticamente.
        
        Args:
            item_id: ID del item a seleccionar
        """
        if item_id in self._items:
            self._on_item_clicked(item_id)
    
    def get_current_item(self) -> str:
        """
        Obtiene el ID del item actualmente seleccionado.
        
        Returns:
            ID del item seleccionado o None
        """
        return self._current_item