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
    Barra lateral de navegación con botones estilizados.
    Incluye iconos, efectos hover y gestión de estado activo.
    """
    
    navigation_changed = pyqtSignal(str)  # Emite el nombre de la vista seleccionada
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa la barra lateral de navegación.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._active_button: Optional[QPushButton] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de la sidebar."""
        self.setObjectName("ModernSidebar")
        self.setFixedWidth(250)
        self.setStyleSheet("""
            #ModernSidebar {
                background-color: #2D2D30;
                border-right: 1px solid #3E3E42;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 20, 10, 20)
        
        # Brand/Logo
        brand_widget = self._create_brand()
        layout.addWidget(brand_widget)
        layout.addSpacing(20)
        
        # Los botones se añadirán dinámicamente con add_navigation_item
        
        layout.addStretch()
    
    def _create_brand(self) -> QWidget:
        """
        Crea el widget del logo/marca de la aplicación.
        
        Returns:
            Widget con el logo y nombre de la aplicación
        """
        brand = QWidget()
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(15, 0, 15, 30)
        brand_layout.setSpacing(10)
        
        # Ícono (usando símbolo Unicode)
        icon_label = QLabel("📊")
        icon_label.setStyleSheet("""
            font-size: 24px;
        """)
        
        # Nombre de la aplicación
        name_label = QLabel("LICITA MANAGER")
        name_label.setStyleSheet("""
            font-weight: 800;
            font-size: 16px;
            letter-spacing: 1px;
            color: #FFFFFF;
        """)
        
        brand_layout.addWidget(icon_label)
        brand_layout.addWidget(name_label)
        brand_layout.addStretch()
        
        return brand
    
    def add_navigation_item(
        self, 
        view_id: str, 
        text: str, 
        icon_text: str = "•",
        is_active: bool = False
    ) -> None:
        """
        Añade un item de navegación a la sidebar.
        
        Args:
            view_id: Identificador único de la vista
            text: Texto a mostrar en el botón
            icon_text: Carácter o emoji para usar como ícono
            is_active: Si este item debe estar activo por defecto
        """
        button = QPushButton(f"{icon_text}  {text}")
        button.setObjectName(f"nav_btn_{view_id}")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setCheckable(True)
        button.setFixedHeight(44)
        
        # Estilo base del botón
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #B0B0B0;
                border: none;
                border-radius: 8px;
                padding: 12px 15px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3E3E42;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: rgba(124, 77, 255, 0.15);
                color: #7C4DFF;
                font-weight: 600;
            }
        """)
        
        # Conectar señal
        button.clicked.connect(lambda: self._on_navigation_click(view_id, button))
        
        # Añadir al layout
        layout = self.layout()
        if layout:
            # Insertar antes del stretch
            layout.insertWidget(layout.count() - 1, button)
        
        self._buttons[view_id] = button
        
        if is_active:
            button.setChecked(True)
            self._active_button = button
    
    def _on_navigation_click(self, view_id: str, button: QPushButton) -> None:
        """
        Maneja el clic en un botón de navegación.
        
        Args:
            view_id: ID de la vista seleccionada
            button: Botón que fue clickeado
        """
        # Desactivar botón anterior
        if self._active_button and self._active_button != button:
            self._active_button.setChecked(False)
        
        # Activar nuevo botón
        button.setChecked(True)
        self._active_button = button
        
        # Emitir señal
        self.navigation_changed.emit(view_id)
    
    def set_active_view(self, view_id: str) -> None:
        """
        Establece la vista activa programáticamente.
        
        Args:
            view_id: ID de la vista a activar
        """
        if view_id in self._buttons:
            button = self._buttons[view_id]
            self._on_navigation_click(view_id, button)
