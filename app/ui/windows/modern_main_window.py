"""
Modern Main Window - Ventana principal con arquitectura sidebar + contenido dinámico.
Usa el patrón de navegación moderno con sidebar y vistas intercambiables.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QStatusBar, QMessageBox
)

from app.core.db_adapter import DatabaseAdapter
from app.core.logic.status_engine import DefaultStatusEngine
from app.ui.models.licitaciones_table_model import LicitacionesTableModel
from app.ui.widgets.modern_widgets import ModernSidebar
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.licitaciones_list_view import LicitacionesListView


class ModernMainWindow(QMainWindow):
    """
    Ventana principal moderna con navegación por sidebar.
    
    Características:
    - Sidebar de navegación a la izquierda
    - Área de contenido con QStackedWidget para cambiar entre vistas
    - Tema oscuro Titanium Construct v2
    - Arquitectura limpia y modular
    """
    
    def __init__(self, db_client=None, parent: Optional[QWidget] = None):
        """
        Inicializa la ventana principal moderna.
        
        Args:
            db_client: Cliente de base de datos (Firestore, SQLite, etc.)
            parent: Widget padre
        """
        super().__init__(parent)
        
        # Atributos de la aplicación
        self.db: Optional[DatabaseAdapter] = None
        self.status_engine = DefaultStatusEngine()
        self.licitaciones_model = LicitacionesTableModel(
            parent=self, 
            status_engine=self.status_engine
        )
        
        # Referencias a vistas
        self.dashboard_view: Optional[DashboardView] = None
        self.licitaciones_view: Optional[LicitacionesListView] = None
        
        # Configuración de ventana
        self.setWindowTitle("Gestor de Licitaciones - Modern UI")
        self.resize(1400, 800)
        
        # Construir UI
        self._setup_ui()
        
        # Inicializar base de datos
        self._initialize_database(db_client)
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal (horizontal)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar de navegación
        self.sidebar = ModernSidebar()
        self.sidebar.add_navigation_item(
            "dashboard", 
            "Dashboard General", 
            "📊",
            is_active=True
        )
        self.sidebar.add_navigation_item(
            "licitaciones", 
            "Gestión Licitaciones", 
            "📋"
        )
        self.sidebar.add_navigation_item(
            "reportes", 
            "Reportes", 
            "📄"
        )
        
        # Conectar señal de navegación
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        
        # Área de contenido con QStackedWidget
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #1E1E1E;
            }
        """)
        
        # Añadir al layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_stack, 1)
        
        # Barra de estado
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Inicializando...", 3000)
    
    def _initialize_database(self, db_client) -> None:
        """
        Inicializa la conexión a la base de datos y carga datos iniciales.
        
        Args:
            db_client: Cliente de base de datos
        """
        from app.core.db_adapter_selector import get_database_adapter
        import os
        
        try:
            self.db = get_database_adapter(db_client=db_client)
            self.db.open()
            
            backend = os.getenv("APP_DB_BACKEND", "firestore")
            backend_names = {
                "firestore": "Firebase Firestore",
                "sqlite": "SQLite Local",
                "mysql": "MySQL"
            }
            backend_display = backend_names.get(backend, backend)
            
            # Cargar licitaciones iniciales
            self._load_initial_data()
            
            # Crear vistas
            self._create_views()
            
            # Suscribirse a actualizaciones
            self._subscribe_to_updates()
            
            self.statusBar().showMessage(f"✓ Conectado a {backend_display}", 8000)
            
        except Exception as exc:
            import os
            backend = os.getenv("APP_DB_BACKEND", "firestore")
            QMessageBox.critical(
                self,
                "Error de Base de Datos",
                f"No se pudo inicializar la conexión al backend '{backend}':\n{exc}"
            )
            self.statusBar().showMessage("❌ Error de conexión", 0)
    
    def _load_initial_data(self) -> None:
        """Carga los datos iniciales desde la base de datos."""
        if not self.db or not self.licitaciones_model:
            return
        
        licitaciones = self.db.load_all_licitaciones() or []
        self.licitaciones_model.set_rows(licitaciones)
    
    def _subscribe_to_updates(self) -> None:
        """Suscribe a actualizaciones en tiempo real de la base de datos."""
        if not self.db:
            return
        
        def _apply(licitaciones):
            def _update():
                if not self.licitaciones_model:
                    return
                self.licitaciones_model.set_rows(licitaciones)
                
                # Actualizar vistas
                if self.dashboard_view:
                    self.dashboard_view.refresh_stats()
                if self.licitaciones_view:
                    self.licitaciones_view.refresh()
            
            QTimer.singleShot(0, _update)
        
        self.db.subscribe_to_licitaciones(_apply)
    
    def _create_views(self) -> None:
        """Crea las vistas y las añade al stack."""
        # Vista de Dashboard
        self.dashboard_view = DashboardView(db=self.db)
        self.content_stack.addWidget(self.dashboard_view)
        
        # Vista de Licitaciones
        self.licitaciones_view = LicitacionesListView(
            model=self.licitaciones_model,
            db=self.db,
            status_engine=self.status_engine
        )
        self.licitaciones_view.detail_requested.connect(self._on_licitacion_detail_requested)
        self.content_stack.addWidget(self.licitaciones_view)
        
        # Placeholder para Reportes
        reportes_placeholder = QWidget()
        reportes_placeholder.setStyleSheet("background-color: #1E1E1E;")
        self.content_stack.addWidget(reportes_placeholder)
        
        # Mostrar dashboard por defecto
        self.content_stack.setCurrentIndex(0)
    
    def _on_navigation_changed(self, view_id: str) -> None:
        """
        Maneja el cambio de navegación en el sidebar.
        
        Args:
            view_id: ID de la vista seleccionada ("dashboard", "licitaciones", etc.)
        """
        view_indices = {
            "dashboard": 0,
            "licitaciones": 1,
            "reportes": 2
        }
        
        index = view_indices.get(view_id, 0)
        self.content_stack.setCurrentIndex(index)
        
        # Actualizar título en la barra de estado
        titles = {
            "dashboard": "Dashboard / Vista General",
            "licitaciones": "Gestión / Listado Maestro",
            "reportes": "Reportes / Generales"
        }
        title = titles.get(view_id, "Gestor de Licitaciones")
        self.statusBar().showMessage(title, 3000)
        
        # Refrescar vista si es necesario
        if view_id == "dashboard" and self.dashboard_view:
            self.dashboard_view.refresh_stats()
        elif view_id == "licitaciones" and self.licitaciones_view:
            self.licitaciones_view.refresh()
    
    def _on_licitacion_detail_requested(self, licitacion) -> None:
        """
        Maneja la solicitud de abrir detalles de una licitación.
        
        Args:
            licitacion: Objeto de licitación seleccionado
        """
        # TODO: Implementar apertura de ventana de detalles
        # Por ahora, solo mostrar mensaje
        if hasattr(licitacion, 'numero_proceso'):
            self.statusBar().showMessage(
                f"Detalles de: {licitacion.numero_proceso}", 
                5000
            )
        else:
            self.statusBar().showMessage("Detalles de licitación", 5000)
