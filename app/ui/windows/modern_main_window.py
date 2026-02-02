"""
Modern Main Window - Ventana principal con sidebar y navegación moderna.
Migración completa de funcionalidad desde MainWindow antigua.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QGuiApplication
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QMessageBox, QDialog, QInputDialog
)

from app.core.db_adapter import DatabaseAdapter
from app.core.models import Licitacion
from app.core.logic.status_engine import DefaultStatusEngine
from app.ui.models.licitaciones_table_model import LicitacionesTableModel
from app.ui.widgets.modern_widgets import ModernSidebar
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.licitaciones_list_view import LicitacionesListView

# Importaciones condicionales
def safe_import(module_path: str, class_name: str):
    """Importa una clase de forma segura, retorna None si falla."""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except Exception:
        return None

# Diálogos
DialogoGestionarInstituciones = safe_import('app.ui.dialogs.dialogo_gestionar_instituciones', 'DialogoGestionarInstituciones')
DialogoGestionarEmpresas = safe_import('app.ui.dialogs.dialogo_gestionar_empresas', 'DialogoGestionarEmpresas')
DialogoGestionarDocumentos = safe_import('app.ui.dialogs.dialogo_gestionar_documentos_maestros', 'DialogoGestionarDocumentos')
DialogoGestionarCompetidores = safe_import('app.ui.dialogs.dialogo_gestionar_competidores', 'DialogoGestionarCompetidores')
DialogoGestionarResponsables = safe_import('app.ui.dialogs.dialogo_gestionar_responsables', 'DialogoGestionarResponsables')
DialogoHistorialCompleto = safe_import('app.ui.dialogs.dialogo_historial', 'DialogoHistorialCompleto')
DialogoGestionarTareas = safe_import('app.ui.dialogs.dialogo_tareas', 'DialogoGestionarTareas')
DialogoReportes = safe_import('app.ui.dialogs.dialogo_reportes', 'DialogoReportes')
DialogoPlantillas = safe_import('app.ui.dialogs.dialogo_plantillas', 'DialogoPlantillas')
DialogoImportarDatos = safe_import('app.ui.dialogs.dialogo_importar', 'DialogoImportarDatos')

# Ventanas/Widgets
DashboardWidget = safe_import('app.ui.views.dashboard_widget', 'DashboardWidget')
ReportWindow = safe_import('app.ui.windows.reporte_window', 'ReportWindow')


class ModernMainWindow(QMainWindow):
    """
    Ventana principal moderna con sidebar de navegación.
    Migra toda la funcionalidad de MainWindow antigua.
    """
    
    def __init__(self, db: DatabaseAdapter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Core
        self.db = db
        self.status_engine = DefaultStatusEngine()
        self._settings = QSettings("Zoeccivil", "Licitaciones")
        
        # Modelo de tabla
        self.table_model = LicitacionesTableModel(
            parent=self,
            status_engine=self.status_engine
        )
        
        # UI
        self.setWindowTitle("Gestor de Licitaciones - Modern UI")
        self.resize(1400, 900)
        
        self._setup_ui()
        self._create_menu_bar()
        self._register_shortcuts()
        self._initialize_data()
        self._setup_realtime_sync()
        self._restore_geometry()
        
        # Mostrar dashboard por defecto
        self.sidebar.select_item("dashboard")
    
    def _setup_ui(self) -> None:
        """Configura la interfaz principal."""
        # Widget central con layout horizontal
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ModernSidebar()
        
        # ✅ Añadir items de navegación
        self.sidebar.add_navigation_item("dashboard", "Dashboard General", "📊")
        self.sidebar.add_navigation_item("licitaciones", "Gestión Licitaciones", "📋")
        self.sidebar.add_navigation_item("reportes", "Reportes", "📈")
        
        self.sidebar.item_selected.connect(self._on_sidebar_navigation)
        
        main_layout.addWidget(self.sidebar)
        
        # Stack de vistas
        self.content_stack = QStackedWidget()
        
        # ==================== VISTA 1: DASHBOARD ====================
        from app.ui.views.dashboard_view import DashboardView
        self.dashboard_view = DashboardView(db=self.db)
        self.content_stack.addWidget(self.dashboard_view)
        
        # ==================== VISTA 2: LICITACIONES ====================
        self.licitaciones_view = LicitacionesListView(
            model=self.table_model,
            db=self.db,
            status_engine=self.status_engine
        )
        # Conectar señales
        self.licitaciones_view.btn_nueva.clicked.connect(self._on_nueva_licitacion)
        self.licitaciones_view.btn_editar.clicked.connect(self._on_editar_licitacion)
        
        self.content_stack.addWidget(self.licitaciones_view)
        
        # ==================== VISTA 3: REPORTES ====================
        from app.ui.views.reportes_view import ReportesView
        self.reportes_view = ReportesView(db=self.db, parent=self)
        self.content_stack.addWidget(self.reportes_view)
        
        # ==================== AÑADIR STACK AL LAYOUT ====================
        main_layout.addWidget(self.content_stack, 1)
        
        # Status bar
        self.setStatusBar(self.statusBar())
        self._update_statusbar_kpis()    


        
    def _create_reportes_placeholder(self) -> QWidget:
        """Crea un placeholder para la vista de reportes."""
        from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("📈 Módulo de Reportes")
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #7C4DFF;")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sublabel = QLabel("Accede a los reportes desde el menú superior")
        sublabel.setStyleSheet("font-size: 14px; color: #B0B0B0;")
        layout.addWidget(sublabel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn = QPushButton("📊 Abrir KPIs y Reportes Avanzados")
        btn.setFixedWidth(300)
        btn.clicked.connect(self._abrir_reportes_kpis)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return widget
    
    def _create_menu_bar(self) -> None:
        """Crea la barra de menú completa."""
        menubar = self.menuBar()
        
        # --- Menú Archivo ---
        menu_archivo = menubar.addMenu("&Archivo")
        
        self.act_config_firebase = QAction("⚙️  Configurar Firebase...", self)
        self.act_config_firebase.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.act_config_firebase.triggered.connect(self._abrir_configuracion_firebase)
        menu_archivo.addAction(self.act_config_firebase)
        
        menu_archivo.addSeparator()
        
        self.act_backup = QAction("Copia de Seguridad...", self)
        self.act_backup.triggered.connect(self._accion_backup_db)
        menu_archivo.addAction(self.act_backup)
        
        self.act_restore = QAction("Restaurar...", self)
        self.act_restore.triggered.connect(self._accion_restore_db)
        menu_archivo.addAction(self.act_restore)
        
        menu_archivo.addSeparator()
        
        act_salir = QAction("Salir", self)
        act_salir.setShortcut(QKeySequence("Ctrl+Q"))
        act_salir.triggered.connect(self.close)
        menu_archivo.addAction(act_salir)
        
        # --- Menú Dashboards ---
        menu_dashboards = menubar.addMenu("&Dashboards")
        
        self.act_dashboard_global = QAction("📊 Dashboard Global (Analítico)", self)
        self.act_dashboard_global.triggered.connect(self._abrir_dashboard_global)
        menu_dashboards.addAction(self.act_dashboard_global)
        
        # --- Menú Reportes ---
        menu_reportes = menubar.addMenu("&Reportes")
        
        self.act_reporte_global = QAction("Reporte Global...", self)
        self.act_reporte_global.triggered.connect(self._abrir_reporte_global)
        menu_reportes.addAction(self.act_reporte_global)
        
        self.act_reporte_sel = QAction("Reporte de Selección...", self)
        self.act_reporte_sel.triggered.connect(self._abrir_reporte_de_seleccionada)
        menu_reportes.addAction(self.act_reporte_sel)
        
        menu_reportes.addSeparator()
        
        self.act_reportes_kpis = QAction("📊 KPIs y Reportes Avanzados", self)
        self.act_reportes_kpis.triggered.connect(self._abrir_reportes_kpis)
        menu_reportes.addAction(self.act_reportes_kpis)
        
        # --- Menú Gestión ---
        menu_gestion = menubar.addMenu("&Gestión")
        
        self.act_tareas = QAction("📋 Gestionar Tareas", self)
        self.act_tareas.triggered.connect(self._abrir_gestion_tareas)
        menu_gestion.addAction(self.act_tareas)
        
        self.act_historial = QAction("📜 Historial de Auditoría", self)
        self.act_historial.triggered.connect(self._abrir_historial_completo)
        menu_gestion.addAction(self.act_historial)
        
        menu_gestion.addSeparator()
        
        self.act_plantillas = QAction("📝 Gestionar Plantillas", self)
        self.act_plantillas.triggered.connect(self._abrir_plantillas)
        menu_gestion.addAction(self.act_plantillas)
        
        self.act_importar = QAction("📂 Importar Datos", self)
        self.act_importar.triggered.connect(self._abrir_importar_datos)
        menu_gestion.addAction(self.act_importar)
        
        # --- Menú Catálogos ---
        menu_catalogos = menubar.addMenu("&Catálogos")
        
        self.act_instituciones = QAction("Instituciones", self)
        self.act_instituciones.triggered.connect(self._abrir_gestor_instituciones)
        menu_catalogos.addAction(self.act_instituciones)
        
        self.act_empresas = QAction("Empresas", self)
        self.act_empresas.triggered.connect(self._abrir_gestor_empresas)
        menu_catalogos.addAction(self.act_empresas)
        
        self.act_documentos = QAction("Documentos", self)
        self.act_documentos.triggered.connect(self._abrir_gestor_documentos)
        menu_catalogos.addAction(self.act_documentos)
        
        self.act_competidores = QAction("Competidores", self)
        self.act_competidores.triggered.connect(self._abrir_gestor_competidores)
        menu_catalogos.addAction(self.act_competidores)
        
        self.act_responsables = QAction("Responsables", self)
        self.act_responsables.triggered.connect(self._abrir_gestor_responsables)
        menu_catalogos.addAction(self.act_responsables)
        
        # --- Menú Ayuda ---
        menu_ayuda = menubar.addMenu("&Ayuda")
        
        act_acerca_de = QAction("Acerca de...", self)
        act_acerca_de.triggered.connect(self._on_acerca_de)
        menu_ayuda.addAction(act_acerca_de)
    
    def _register_shortcuts(self) -> None:
        """Registra atajos de teclado globales."""
        from PyQt6.QtGui import QShortcut
        
        # Ctrl+N: Nueva licitación
        shortcut_nueva = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_nueva.activated.connect(self._shortcut_nueva_licitacion)
        
        # F5: Refrescar
        shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        shortcut_refresh.activated.connect(self._refresh_all)
        
        # Ctrl+1/2/3: Navegación rápida
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(
            lambda: self.sidebar.select_item("dashboard")
        )
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(
            lambda: self.sidebar.select_item("licitaciones")
        )
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(
            lambda: self.sidebar.select_item("reportes")
        )
    
    def _initialize_data(self) -> None:
        """Carga datos iniciales desde la base de datos."""
        if not self.db:
            return
        
        try:
            licitaciones = self.db.load_all_licitaciones() or []
            self.table_model.set_rows(licitaciones)
            
            import os
            backend = os.getenv("APP_DB_BACKEND", "firestore")
            backend_names = {
                "firestore": "Firebase Firestore",
                "sqlite": "SQLite Local",
                "mysql": "MySQL"
            }
            self.statusBar().showMessage(
                f"✓ Conectado a {backend_names.get(backend, backend)}",
                5000
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error de Carga",
                f"No se pudieron cargar las licitaciones:\n{e}"
            )
    
    def _setup_realtime_sync(self) -> None:
        """Configura sincronización en tiempo real con Firestore."""
        if not hasattr(self.db, 'subscribe_to_licitaciones'):
            print("[INFO] Base de datos no soporta suscripciones en tiempo real")
            return
        
        def on_change(licitaciones):
            """Callback cuando cambian datos en Firestore."""
            QTimer.singleShot(0, lambda: self._on_data_changed(licitaciones))
        
        try:
            self.db.subscribe_to_licitaciones(on_change)
            print("[DEBUG] Sincronización en tiempo real activada")
        except Exception as e:
            print(f"[WARNING] No se pudo activar sincronización: {e}")
    
    def _on_data_changed(self, licitaciones) -> None:
        """Maneja cambios de datos en tiempo real."""
        try:
            self.table_model.set_rows(licitaciones)
            self.licitaciones_view.refresh()
            self.dashboard_view.refresh_stats()
            self._update_statusbar_kpis()
        except Exception as e:
            print(f"[ERROR] Error actualizando datos: {e}")
    
    # ==================== NAVEGACIÓN ====================
    
    def _on_sidebar_navigation(self, item_id: str) -> None:
        """Maneja la navegación del sidebar."""
        if item_id == "dashboard":
            self.content_stack.setCurrentWidget(self.dashboard_view)
            self.dashboard_view.refresh_stats()
        elif item_id == "licitaciones":
            self.content_stack.setCurrentWidget(self.licitaciones_view)
            self.licitaciones_view.refresh()
        elif item_id == "reportes":
            self.content_stack.setCurrentWidget(self.reportes_view)
    
    # ==================== ACCIONES LICITACIONES ====================
    
    def _on_nueva_licitacion(self) -> None:
        """Abre diálogo para crear nueva licitación."""
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        nueva = Licitacion()
        
        dialog = LicitationDetailsWindow(
            parent=self,
            licitacion=nueva,
            db_adapter=self.db,
            refresh_callback=self._refresh_all
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_all()
    
    def _on_editar_licitacion(self) -> None:
        """Abre diálogo para editar licitación seleccionada."""
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        # Obtener tabla activa
        current_tab = self.licitaciones_view.tabs.currentIndex()
        table = (self.licitaciones_view.table_activas if current_tab == 0 
                else self.licitaciones_view.table_finalizadas)
        
        selection = table.selectionModel().selectedRows()
        
        if not selection:
            QMessageBox.information(
                self,
                "Sin Selección",
                "Seleccione una licitación para editar."
            )
            return
        
        # Obtener licitación del modelo
        proxy_index = selection[0]
        source_index = proxy_index.model().mapToSource(proxy_index)
        licitacion = self.table_model.data(
            source_index,
            Qt.ItemDataRole.UserRole + 1002
        )
        
        if not licitacion:
            return
        
        dialog = LicitationDetailsWindow(
            parent=self,
            licitacion=licitacion,
            db_adapter=self.db,
            refresh_callback=self._refresh_all
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_all()
    
    # ==================== MENÚ ARCHIVO ====================
    
    def _abrir_configuracion_firebase(self) -> None:
        """Abre configuración de Firebase."""
        try:
            from app.ui.dialogs.firebase_config_dialog import FirebaseConfigDialog
            
            dialog = FirebaseConfigDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(
                    self,
                    "Configuración Guardada",
                    "Reinicie la aplicación para aplicar los cambios."
                )
        except ImportError:
            QMessageBox.warning(
                self,
                "No Disponible",
                "Edite manualmente 'lic_config.json'."
            )
    
    def _accion_backup_db(self) -> None:
        """Backup de base de datos."""
        QMessageBox.information(
            self,
            "Copia de Seguridad",
            "Use las herramientas de Firebase Console para exportar datos."
        )
    
    def _accion_restore_db(self) -> None:
        """Restaurar base de datos."""
        QMessageBox.information(
            self,
            "Restaurar",
            "Use las herramientas de Firebase Console para importar datos."
        )
    
    # ==================== MENÚ DASHBOARDS ====================
    
    def _abrir_dashboard_global(self) -> None:
        """Abre dashboard global analítico."""
        if DashboardWidget is None:
            QMessageBox.warning(self, "No Disponible", "DashboardWidget no está disponible.")
            return
        
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Dashboard Global - Análisis General")
            dlg.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowMinimizeButtonHint |
                Qt.WindowType.WindowMaximizeButtonHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(5, 5, 5, 5)
            
            dashboard_widget = DashboardWidget(db=self.db, parent=dlg)
            layout.addWidget(dashboard_widget)
            
            # Conectar señal de edición
            if hasattr(dashboard_widget, 'edit_licitacion_requested'):
                dashboard_widget.edit_licitacion_requested.connect(
                    self._accion_abrir_licitacion_por_id
                )
            
            # Tamaño
            try:
                screen = self.screen().availableGeometry()
                dlg.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
            except:
                dlg.resize(1200, 800)
            
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Dashboard Global:\n{e}")
    
    def _accion_abrir_licitacion_por_id(self, licitacion_id: int) -> None:
        """Abre licitación por ID."""
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        try:
            lic = self.db.load_licitacion_by_id(licitacion_id)
            if not lic:
                QMessageBox.warning(self, "No Encontrado", f"Licitación ID {licitacion_id} no existe.")
                return
            
            dialog = LicitationDetailsWindow(
                parent=self,
                licitacion=lic,
                db_adapter=self.db,
                refresh_callback=self._refresh_all
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir licitación:\n{e}")
    
    # ==================== MENÚ REPORTES ====================
    
    def _abrir_reporte_global(self) -> None:
        """Abre reporte global (reutiliza dashboard)."""
        self._abrir_dashboard_global()
    
    def _abrir_reporte_de_seleccionada(self) -> None:
        """Abre reporte de licitación seleccionada."""
        if ReportWindow is None:
            QMessageBox.warning(self, "No Disponible", "ReportWindow no está disponible.")
            return
        
        # Verificar que estemos en vista de licitaciones
        if self.content_stack.currentWidget() != self.licitaciones_view:
            QMessageBox.information(
                self,
                "Vista Incorrecta",
                "Vaya a 'Gestión Licitaciones' y seleccione una licitación."
            )
            return
        
        # Obtener tabla activa según el tab
        current_tab = self.licitaciones_view.tabs.currentIndex()
        table = (self.licitaciones_view.table_activas if current_tab == 0 
                else self.licitaciones_view.table_finalizadas)
        
        # Obtener selección
        selection = table.selectionModel().selectedRows()
        
        if not selection:
            QMessageBox.information(self, "Sin Selección", "Seleccione una licitación.")
            return
        
        # ✅ CORRECCIÓN: Mapear correctamente a través de proxies
        proxy_index = selection[0]
        
        # Obtener número de proceso de la columna 0
        codigo_index = proxy_index.model().index(proxy_index.row(), 0)
        numero_proceso = proxy_index.model().data(codigo_index, Qt.ItemDataRole.DisplayRole)
        
        print(f"[DEBUG] Abriendo reporte para: {numero_proceso}")
        
        # Buscar licitación en el modelo base por número de proceso
        licitacion = None
        for row in range(self.table_model.rowCount()):
            model_index = self.table_model.index(row, 0)
            codigo = self.table_model.data(model_index, Qt.ItemDataRole.DisplayRole)
            if codigo == numero_proceso:
                licitacion = self.table_model.data(
                    self.table_model.index(row, 0),
                    Qt.ItemDataRole.UserRole + 1002
                )
                break
        
        if not licitacion:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo encontrar la licitación '{numero_proceso}' en el modelo."
            )
            return
        
        print(f"[DEBUG] Licitación encontrada: {licitacion.nombre_proceso}")
        
        try:
            win = ReportWindow(licitacion, self, start_maximized=True)
            win.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir reporte:\n{e}")
            import traceback
            traceback.print_exc()
    
    def _abrir_reportes_kpis(self) -> None:
        """Abre dashboard de KPIs avanzados."""
        if DialogoReportes is None:
            QMessageBox.warning(self, "No Disponible", "Módulo de reportes no disponible.")
            return
        
        try:
            dlg = DialogoReportes(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir reportes:\n{e}")
    
    # ==================== MENÚ GESTIÓN ====================
    
    def _abrir_gestion_tareas(self) -> None:
        """Abre gestor de tareas."""
        if DialogoGestionarTareas is None:
            QMessageBox.warning(self, "No Disponible", "Módulo de tareas no disponible.")
            return
        
        try:
            dlg = DialogoGestionarTareas(self)
            dlg.exec()
            self._refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir tareas:\n{e}")
    
    def _abrir_historial_completo(self) -> None:
        """Abre historial de auditoría."""
        if DialogoHistorialCompleto is None:
            QMessageBox.warning(self, "No Disponible", "Módulo de auditoría no disponible.")
            return
        
        try:
            dlg = DialogoHistorialCompleto(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir historial:\n{e}")
    
    def _abrir_plantillas(self) -> None:
        """Abre gestor de plantillas."""
        if DialogoPlantillas is None:
            QMessageBox.warning(self, "No Disponible", "Módulo de plantillas no disponible.")
            return
        
        try:
            dlg = DialogoPlantillas(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir plantillas:\n{e}")
    
    def _abrir_importar_datos(self) -> None:
        """Abre asistente de importación."""
        if DialogoImportarDatos is None:
            QMessageBox.warning(self, "No Disponible", "Módulo de importación no disponible.")
            return
        
        tipos = ["lotes", "documentos"]
        tipo, ok = QInputDialog.getItem(
            self,
            "Importar Datos",
            "Tipo de datos a importar:",
            tipos, 0, False
        )
        
        if not ok:
            return
        
        try:
            dlg = DialogoImportarDatos(self, self.db, entity_type=tipo)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "Éxito", "Datos importados correctamente.")
                self._refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar:\n{e}")
    
    # ==================== MENÚ CATÁLOGOS ====================
    
    def _abrir_gestor_instituciones(self) -> None:
        """Abre gestor de instituciones."""
        if DialogoGestionarInstituciones is None:
            QMessageBox.warning(self, "No Disponible", "Gestor de instituciones no disponible.")
            return
        
        try:
            dlg = DialogoGestionarInstituciones(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
    
    def _abrir_gestor_empresas(self) -> None:
        """Abre gestor de empresas."""
        if DialogoGestionarEmpresas is None:
            QMessageBox.warning(self, "No Disponible", "Gestor de empresas no disponible.")
            return
        
        try:
            dlg = DialogoGestionarEmpresas(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
    
    def _abrir_gestor_documentos(self) -> None:
        """Abre gestor de documentos."""
        if DialogoGestionarDocumentos is None:
            QMessageBox.warning(self, "No Disponible", "Gestor de documentos no disponible.")
            return
        
        try:
            dlg = DialogoGestionarDocumentos(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
    
    def _abrir_gestor_competidores(self) -> None:
        """Abre gestor de competidores."""
        if DialogoGestionarCompetidores is None:
            QMessageBox.warning(self, "No Disponible", "Gestor de competidores no disponible.")
            return
        
        try:
            dlg = DialogoGestionarCompetidores(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
    
    def _abrir_gestor_responsables(self) -> None:
        """Abre gestor de responsables."""
        if DialogoGestionarResponsables is None:
            QMessageBox.warning(self, "No Disponible", "Gestor de responsables no disponible.")
            return
        
        try:
            dlg = DialogoGestionarResponsables(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")
    
    # ==================== UTILIDADES ====================
    
    def _refresh_all(self) -> None:
        """Refresca todas las vistas."""
        try:
            licitaciones = self.db.load_all_licitaciones() or []
            self.table_model.set_rows(licitaciones)
            self.licitaciones_view.refresh()
            self.dashboard_view.refresh_stats()
            self._update_statusbar_kpis()
            self.statusBar().showMessage("✓ Datos actualizados", 2000)
        except Exception as e:
            print(f"[ERROR] Error refrescando: {e}")
    
    def _shortcut_nueva_licitacion(self) -> None:
        """Atajo Ctrl+N para nueva licitación."""
        # Cambiar a vista de licitaciones y crear
        self.sidebar.select_item("licitaciones")
        QTimer.singleShot(100, self._on_nueva_licitacion)
    
    def _update_statusbar_kpis(self) -> None:
        """Actualiza KPIs en la barra de estado."""
        try:
            if DashboardWidget is None:
                return
            
            dash = DashboardWidget(db=self.db)
            dash.reload_data()
            kpis = dash.get_global_kpis_summary()
            
            msg = (f"Ganadas: {kpis['ganadas']} | "
                   f"Perdidas: {kpis['perdidas']} | "
                   f"Éxito: {kpis['tasa_exito']:.1f}%")
            
            self.statusBar().showMessage(msg)
        except Exception:
            pass
    
    def _on_acerca_de(self) -> None:
        """Muestra información de la aplicación."""
        QMessageBox.about(
            self,
            "Gestor de Licitaciones",
            "<h2>Gestor de Licitaciones v4.0</h2>"
            "<p><b>Modern UI Edition</b></p>"
            "<p>Sistema profesional de gestión de licitaciones públicas.</p>"
            "<hr>"
            "<p><b>Características:</b></p>"
            "<ul>"
            "<li>Dashboard con métricas en tiempo real</li>"
            "<li>Gestión completa de licitaciones y lotes</li>"
            "<li>Sincronización con Firebase Firestore</li>"
            "<li>Tema oscuro Titanium Construct v2</li>"
            "</ul>"
            "<p><small>© 2026 - Zoeccivil</small></p>"
        )
    
    # ==================== GEOMETRÍA ====================
    
    def _restore_geometry(self) -> None:
        """Restaura geometría de la ventana."""
        try:
            geom = self._settings.value("ModernMainWindow/geometry")
            if geom:
                self.restoreGeometry(geom)
        except Exception:
            pass
    
    def closeEvent(self, event) -> None:
        """Guarda estado al cerrar."""
        try:
            self._settings.setValue("ModernMainWindow/geometry", self.saveGeometry())
        except Exception:
            pass
        
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass
        
        super().closeEvent(event)