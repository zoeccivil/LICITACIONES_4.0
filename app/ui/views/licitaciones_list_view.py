"""
Licitaciones List View - Vista de tabla de licitaciones.
Muestra la tabla de licitaciones con filtros y controles, usando los widgets modernos.
ACTUALIZADO: Badge de vencimiento + Persistencia de columnas.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, date

from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableView, QTabWidget, QHeaderView,
    QFrame, QGroupBox, QGridLayout, QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QFont

from app.core.db_adapter import DatabaseAdapter
from app.core.logic.status_engine import StatusEngine, DefaultStatusEngine
from app.ui.models.licitaciones_table_model import LicitacionesTableModel
from app.ui.models.status_proxy_model import StatusFilterProxyModel
from app.ui.delegates.row_color_delegate import RowColorDelegate
from app.ui.delegates.progress_bar_delegate import ProgressBarDelegate
from app.ui.delegates.simple_progress_bar_delegate import SimpleProgressBarDelegate
from app.ui.delegates.progress_bar_delegate import ProgressBarDelegate
from app.ui.delegates.heatmap_delegate import HeatmapDelegate

# Imports de iconos SVG
from app.ui.utils.icon_utils import (
    add_icon, edit_icon, refresh_icon, eye_icon, 
    chart_icon, list_icon
)

# Proxy de filtros múltiples
try:
    from app.ui.models.multi_filter_proxy_model import MultiFilterProxyModel
except ImportError:
    MultiFilterProxyModel = None

# Roles del modelo
DOCS_PROGRESS_ROLE = Qt.ItemDataRole.UserRole + 1012
DIFERENCIA_PCT_ROLE = Qt.ItemDataRole.UserRole + 1013
ROLE_RECORD_ROLE = Qt.ItemDataRole.UserRole + 1002


class LicitacionesListView(QWidget):
    """
    Vista de lista de licitaciones con tabla, filtros, badge y persistencia.
    """
    
    detail_requested = pyqtSignal(object)
    
    def __init__(
        self,
        model: LicitacionesTableModel,
        db: Optional[DatabaseAdapter] = None,
        status_engine: Optional[StatusEngine] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._model = model
        self.db = db
        self._status = status_engine or DefaultStatusEngine()
        
        # ✅ Settings para persistencia
        self._settings = QSettings("Zoeccivil", "Licitaciones")
        
        # ✅ Timer para debounce de filtros
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(220)
        
        # ✅ Timer para guardar columnas
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_column_widths)
        
        # ✅ AÑADIR ESTO: Obtener colores del tema
        self._resolve_theme_colors()
        
        self._setup_ui()
        self._setup_models()
        self._wire_signals()
        self._populate_filter_values()
        self._apply_filters()
        self._update_tab_counts()
        
        # ✅ IMPORTANTE: Restaurar DESPUÉS de setup
        self._restore_column_widths()
        
        self.btn_nueva.clicked.connect(self._on_nueva_licitacion)
        self.btn_editar.clicked.connect(self._on_editar_licitacion)

    def _resolve_theme_colors(self):
        """
        Obtiene colores dinámicos del tema de la aplicación.
        Crea el diccionario self.colors usado por los widgets.
        """
        from PyQt6.QtGui import QGuiApplication, QPalette
        
        app = QGuiApplication.instance()
        pal: QPalette = app.palette() if app else QPalette()
        
        def get_color(role: QPalette.ColorRole, fallback: str) -> str:
            try:
                color = pal.color(role)
                if color.isValid():
                    return color.name()
            except Exception:
                pass
            return fallback
        
        # ✅ Diccionario de colores del tema Titanium Construct v2
        self.colors = {
            "accent": get_color(QPalette.ColorRole.Highlight, "#7C4DFF"),
            "text": get_color(QPalette.ColorRole.Text, "#E6E9EF"),
            "text_sec": get_color(QPalette.ColorRole.PlaceholderText, "#B9C0CC"),
            "window": get_color(QPalette.ColorRole.Window, "#1E1E1E"),
            "base": "#2D2D30",
            "alt": get_color(QPalette.ColorRole.AlternateBase, "#2D2D30"),
            "border": "#5E5E62",
            "success": "#00C853",
            "danger": "#FF5252",
            "warning": "#FFA726",
            "info": "#448AFF",
        }
        
        print(f"[DEBUG] ✓ Colores del tema cargados: {len(self.colors)} colores")


    def _setup_ui(self) -> None:
        """Configura la interfaz de la vista."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        
        # Panel de filtros CON BADGE
        filters_panel = self._create_filters_panel()
        main_layout.addWidget(filters_panel)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                background-color: #2D2D30;
                border-radius: 0 12px 12px 12px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #B0B0B0;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 5px;
                font-weight: 600;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3E3E42;
                border-bottom: none;
            }
        """)
        
        self.table_activas = self._create_table_view()
        self.table_finalizadas = self._create_table_view()
        
        self.tabs.addTab(self.table_activas, "Licitaciones Activas (0)")
        self.tabs.addTab(self.table_finalizadas, "Licitaciones Finalizadas (0)")
        
        main_layout.addWidget(self.tabs, 1)
        
        # Footer
        footer = self._create_footer()
        main_layout.addLayout(footer)
    
    def _create_toolbar(self) -> QHBoxLayout:
        """Crea la barra de herramientas superior."""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        self.btn_nueva = QPushButton("Nueva Licitación")
        self.btn_nueva.setIcon(add_icon())
        self.btn_nueva.setStyleSheet("""
            QPushButton {
                background-color: #7C4DFF;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #651FFF;
            }
        """)
        self.btn_nueva.setFixedHeight(40)
        
        self.btn_editar = QPushButton("Editar Seleccionada")
        self.btn_editar.setIcon(edit_icon())
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #3E3E42;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                border-color: #B0B0B0;
                background-color: #3E3E42;
            }
        """)
        self.btn_editar.setFixedHeight(40)
        
        # ✅ NUEVO: Botón de refresh
        self.btn_refresh = QPushButton("Actualizar Datos")
        self.btn_refresh.setIcon(refresh_icon())
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #3E3E42;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                border-color: #7C4DFF;
                background-color: #3E3E42;
            }
            QPushButton:pressed {
                background-color: #7C4DFF;
            }
        """)
        self.btn_refresh.setFixedHeight(40)
        self.btn_refresh.setToolTip("Recargar datos desde Firestore (ignora caché local)")
        
        toolbar.addWidget(self.btn_nueva)
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        
        return toolbar
    
    def _create_filters_panel(self) -> QFrame:
        """Crea el panel de filtros CON BADGE de vencimiento."""
        panel = QFrame()
        panel.setObjectName("FiltersPanel")
        panel.setStyleSheet("""
            #FiltersPanel {
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        main_layout = QVBoxLayout(panel)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ==================== FILA 1: FILTROS ====================
        filters_grid = QGridLayout()
        filters_grid.setSpacing(15)
        
        # Buscar Proceso
        label_buscar = QLabel("Buscar Proceso")
        label_buscar.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ej: DGAP-CCC...")
        self.search_edit.setFixedHeight(35)
        
        # Contiene Lote
        label_lote = QLabel("Contiene Lote")
        label_lote.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.lote_edit = QLineEdit()
        self.lote_edit.setPlaceholderText("Descripción...")
        self.lote_edit.setFixedHeight(35)
        
        # Estado
        label_estado = QLabel("Estado")
        label_estado.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItem("Todos")
        self.estado_combo.setFixedHeight(35)
        
        # Empresa
        label_empresa = QLabel("Empresa")
        label_empresa.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.empresa_combo = QComboBox()
        self.empresa_combo.addItem("Todas")
        self.empresa_combo.setFixedHeight(35)
        
        # Botón Limpiar
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #3E3E42;
                color: #FFFFFF;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                border-color: #B0B0B0;
            }
        """)
        self.btn_limpiar.setFixedHeight(35)
        
        # Añadir a grid
        filters_grid.addWidget(label_buscar, 0, 0)
        filters_grid.addWidget(self.search_edit, 1, 0)
        filters_grid.addWidget(label_lote, 0, 1)
        filters_grid.addWidget(self.lote_edit, 1, 1)
        filters_grid.addWidget(label_estado, 0, 2)
        filters_grid.addWidget(self.estado_combo, 1, 2)
        filters_grid.addWidget(label_empresa, 0, 3)
        filters_grid.addWidget(self.empresa_combo, 1, 3)
        filters_grid.addWidget(self.btn_limpiar, 1, 4)
        
        filters_grid.setColumnStretch(0, 2)
        filters_grid.setColumnStretch(1, 2)
        filters_grid.setColumnStretch(2, 1)
        filters_grid.setColumnStretch(3, 2)
        filters_grid.setColumnStretch(4, 0)
        
        main_layout.addLayout(filters_grid)
        
        # ==================== FILA 2: BADGE DE VENCIMIENTO ====================
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(10)
        
        badge_title = QLabel("Próximo Vencimiento:")
        badge_title.setStyleSheet("""
            QLabel {
                color: #B0B0B0;
                font-size: 11pt;
                font-weight: 600;
            }
        """)
        badge_layout.addWidget(badge_title)
        
        # ✅ Badge de vencimiento
        self.nextDueArea = QLabel("-- Selecciona una Fila --")
        self.nextDueArea.setWordWrap(True)
        self.nextDueArea.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.nextDueArea.setTextFormat(Qt.TextFormat.RichText)
        self.nextDueArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.nextDueArea.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                color: #E6E9EF;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 11pt;
                border: 1px solid #3E3E42;
                min-height: 45px;
            }
        """)
        badge_layout.addWidget(self.nextDueArea, 1)
        
        main_layout.addLayout(badge_layout)
        
        return panel
    
    def _create_table_view(self) -> QTableView:
        """Crea una vista de tabla configurada."""
        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.setIconSize(QSize(16, 16))
        table.setItemDelegate(RowColorDelegate(table))
        
        return table
    
    def _create_footer(self) -> QHBoxLayout:
        """Crea el footer con estadísticas."""
        footer = QHBoxLayout()
        footer.setSpacing(20)
        
        self.lbl_activas = QLabel("Activas: 0")
        self.lbl_ganadas = QLabel("Ganadas: 0")
        self.lbl_lotes = QLabel("Lotes Ganados: 0")
        self.lbl_perdidas = QLabel("Perdidas: 0")
        
        for lbl in [self.lbl_activas, self.lbl_ganadas, self.lbl_lotes, self.lbl_perdidas]:
            font = lbl.font()
            font.setPointSize(11)
            font.setBold(True)
            lbl.setFont(font)
        
        self.lbl_activas.setStyleSheet("color: #FFFFFF;")
        self.lbl_ganadas.setStyleSheet("color: #00C853;")
        self.lbl_lotes.setStyleSheet("color: #448AFF;")
        self.lbl_perdidas.setStyleSheet("color: #FF5252;")
        
        footer.addWidget(self.lbl_activas)
        footer.addWidget(self.lbl_ganadas)
        footer.addWidget(self.lbl_lotes)
        footer.addWidget(self.lbl_perdidas)
        footer.addStretch()
        
        return footer

    def apply_delegates(
        self,
        docs_col: int = 4,
        dif_col: int = 5,
        docs_role: int = None,
        dif_role: int = None,
        heat_neg_range: float = 30.0,
        heat_pos_range: float = 30.0,
        heat_alpha: int = 90,
        heat_invert: bool = False
    ):
        """
        Aplica los delegates de progress bar y heatmap a las columnas correspondientes.
        
        NOTA: Los delegates actuales (SimpleProgressBarDelegate y HeatmapDelegate)
        solo aceptan parent= en su constructor. No usan column= ni role=.
        """
        from app.ui.delegates.simple_progress_bar_delegate import SimpleProgressBarDelegate
        from app.ui.delegates.heatmap_delegate import HeatmapDelegate
        
        print(f"[DEBUG] Aplicando delegates:")
        print(f"  - % Docs (col {docs_col})")
        print(f"  - % Dif. (col {dif_col})")
        
        # ✅ APLICAR A AMBAS TABLAS
        for idx, table in enumerate([self.table_activas, self.table_finalizadas]):
            tabla_nombre = "Activas" if idx == 0 else "Finalizadas"
            
            try:
                # ✅ SimpleProgressBarDelegate solo necesita parent
                progress_delegate = SimpleProgressBarDelegate(parent=table)
                table.setItemDelegateForColumn(docs_col, progress_delegate)
                print(f"[DEBUG] ✓ Progress bar aplicado a {tabla_nombre} columna {docs_col}")
                
            except Exception as e:
                print(f"[ERROR] No se pudo aplicar ProgressBarDelegate a {tabla_nombre}: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                # ✅ HeatmapDelegate solo necesita parent
                heatmap_delegate = HeatmapDelegate(parent=table)
                table.setItemDelegateForColumn(dif_col, heatmap_delegate)
                print(f"[DEBUG] ✓ Heatmap aplicado a {tabla_nombre} columna {dif_col}")
                
            except Exception as e:
                print(f"[ERROR] No se pudo aplicar HeatmapDelegate a {tabla_nombre}: {e}")
                import traceback
                traceback.print_exc()
        
        print("[DEBUG] ✓ Delegates aplicados correctamente\n")

    def _setup_models(self):
        """
        Configura los modelos, proxies, delegates y conecta señales de persistencia.
        Se ejecuta DESPUÉS de _setup_ui() para que las tablas ya existan.
        """
        # ==================== CONFIGURAR PROXIES ====================
        self._proxyActivas = StatusFilterProxyModel(
            show_finalizadas=False, 
            status_engine=self._status
        )
        self._proxyActivas.setSourceModel(self._model)
        self.table_activas.setModel(self._proxyActivas)

        self._proxyFinalizadas = StatusFilterProxyModel(
            show_finalizadas=True, 
            status_engine=self._status
        )
        self._proxyFinalizadas.setSourceModel(self._model)
        self.table_finalizadas.setModel(self._proxyFinalizadas)

        # ==================== CONFIGURAR HEADERS Y COLUMNAS ====================
        for tv in (self.table_activas, self.table_finalizadas):
            try:
                tv.hideColumn(8)
            except Exception:
                pass
            
            hh = tv.horizontalHeader()
            try:
                hh.setHighlightSections(False)
                hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                hh.setMinimumSectionSize(60)
            except Exception:
                pass

        # ==================== ✅ APLICAR DELEGATES ====================
        self.apply_delegates(
            docs_col=4, 
            dif_col=5,
            docs_role=DOCS_PROGRESS_ROLE,
            dif_role=DIFERENCIA_PCT_ROLE,
            heat_neg_range=30.0,
            heat_pos_range=30.0,
            heat_alpha=90,
            heat_invert=False
        )

        # ==================== ORDEN INICIAL ====================
        self.table_activas.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table_finalizadas.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # ==================== CONECTAR SEÑALES DE PERSISTENCIA ====================
        header_activas = self.table_activas.horizontalHeader()
        header_activas.sectionResized.connect(self._schedule_save_column_widths)
        header_activas.sortIndicatorChanged.connect(self._schedule_save_column_widths)
        
        header_finalizadas = self.table_finalizadas.horizontalHeader()
        header_finalizadas.sectionResized.connect(self._schedule_save_column_widths)
        header_finalizadas.sortIndicatorChanged.connect(self._schedule_save_column_widths)
        
        print("[DEBUG] ✓ Modelos configurados correctamente")

        # Usar QModelIndex() vacío para obtener el conteo correcto del proxy
        from PyQt6.QtCore import QModelIndex
        activas_count = self._proxyActivas.rowCount(QModelIndex())
        finalizadas_count = self._proxyFinalizadas.rowCount(QModelIndex())

        print(f"[DEBUG]   - Activas: {activas_count} filas")
        print(f"[DEBUG]   - Finalizadas: {finalizadas_count} filas")
        print("[DEBUG] ✓ Señales de persistencia conectadas para ambas tablas")
    
        print("\n[DEBUG] ========== DIAGNÓSTICO DE DELEGATES ==========")
        
        # Verificar que los delegates están instalados
        for table_name, table in [("Activas", self.table_activas), ("Finalizadas", self.table_finalizadas)]:
            print(f"\n{table_name}:")
            for col in range(table.model().columnCount()):
                delegate = table.itemDelegateForColumn(col)
                if delegate and delegate != table.itemDelegate():
                    print(f"  Columna {col}: {type(delegate).__name__}")
        
        # Probar si el modelo devuelve datos para los roles
        if self._model.rowCount() > 0:
            print("\n[DEBUG] Probando roles en primera fila:")
            test_idx = self._model.index(0, 4)  # Columna % Docs
            docs_value = self._model.data(test_idx, DOCS_PROGRESS_ROLE)
            display_value = self._model.data(test_idx, Qt.ItemDataRole.DisplayRole)
            print(f"  % Docs (col 4):")
            print(f"    - DisplayRole: {display_value}")
            print(f"    - DOCS_PROGRESS_ROLE ({DOCS_PROGRESS_ROLE}): {docs_value}")
            
            test_idx2 = self._model.index(0, 5)  # Columna % Dif
            dif_value = self._model.data(test_idx2, DIFERENCIA_PCT_ROLE)
            display_value2 = self._model.data(test_idx2, Qt.ItemDataRole.DisplayRole)
            print(f"  % Dif. (col 5):")
            print(f"    - DisplayRole: {display_value2}")
            print(f"    - DIFERENCIA_PCT_ROLE ({DIFERENCIA_PCT_ROLE}): {dif_value}")
        
        print("\n[DEBUG] ================================================\n")

    def _wire_signals(self) -> None:
        """Conecta las señales de los controles."""
        print("[DEBUG] Conectando señales...")
        
        # ==================== FILTROS ====================
        self.search_edit.textChanged.connect(self._debounce.start)
        self.lote_edit.textChanged.connect(self._debounce.start)
        self.estado_combo.currentIndexChanged.connect(self._apply_filters)
        self.empresa_combo.currentIndexChanged.connect(self._apply_filters)
        self.btn_limpiar.clicked.connect(self._clear_filters)
        self._debounce.timeout.connect(self._apply_filters)
        
        # ==================== TABS ====================
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.currentChanged.connect(self._schedule_save_column_widths)
        
        # ✅ Actualizar badge al cambiar tab
        if hasattr(self, 'nextDueArea'):
            self.tabs.currentChanged.connect(self._sync_badge)
        
        # ==================== SELECCIÓN (para badge) ====================
        # Verificar que selectionModel() exista antes de conectar
        if hasattr(self, 'nextDueArea'):
            sm_activas = self.table_activas.selectionModel()
            if sm_activas:
                sm_activas.selectionChanged.connect(self._sync_badge)
                print("[DEBUG] ✓ Badge conectado a tabla activas")
            
            sm_finalizadas = self.table_finalizadas.selectionModel()
            if sm_finalizadas:
                sm_finalizadas.selectionChanged.connect(self._sync_badge)
                print("[DEBUG] ✓ Badge conectado a tabla finalizadas")
        
        # ==================== DOBLE CLIC ====================
        self.table_activas.doubleClicked.connect(self._on_double_click)
        self.table_finalizadas.doubleClicked.connect(self._on_double_click)
        
        # ==================== MENÚ CONTEXTUAL ====================
        self.table_activas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_activas.customContextMenuRequested.connect(self._show_context_menu)
        
        self.table_finalizadas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_finalizadas.customContextMenuRequested.connect(self._show_context_menu)
        # ✅ NUEVO: Conectar botón de refresh
        self.btn_refresh.clicked.connect(self._on_refresh_data)
        
        print("[DEBUG] ✓ Todas las señales conectadas correctamente")
    
    # ==================== BADGE DE VENCIMIENTO ====================
    
    def _sync_badge(self):
        """
        Actualiza el badge de próximo vencimiento.
        USA LA MISMA LÓGICA QUE get_dias_restantes() DEL MODELO.
        """
        # Determinar qué tabla está activa
        view = self.table_activas if self.tabs.currentIndex() == 0 else self.table_finalizadas
        
        if not view.selectionModel():
            self.nextDueArea.setText("-- Selecciona una Fila --")
            return

        # Obtener fila seleccionada
        sel = view.selectionModel().selectedRows()
        if not sel:
            idx = view.currentIndex()
            if not idx.isValid():
                self.nextDueArea.setText("-- Selecciona una Fila --")
                return
        else:
            idx = sel[0]

        # Obtener modelo (proxy)
        proxy_model = view.model()
        if not proxy_model:
            self.nextDueArea.setText("-- Sin modelo --")
            return

        # Mapear a source para obtener objeto licitación
        if hasattr(proxy_model, "mapToSource"):
            src_idx = proxy_model.mapToSource(idx)
            source_model = proxy_model.sourceModel()
        else:
            src_idx = idx
            source_model = proxy_model
        
        # Obtener objeto licitación
        lic = src_idx.siblingAtColumn(0).data(ROLE_RECORD_ROLE)
        if lic is None:
            self.nextDueArea.setText("-- Sin licitación --")
            return
        
        # ✅ USAR EL MISMO MÉTODO QUE USA LA TABLA
        dias = source_model.get_dias_restantes(lic)
        
        # Obtener nombre de la licitación
        lic_nombre = getattr(lic, "nombre_proceso", None) or getattr(lic, "nombre", None) or "Licitación"
        if len(lic_nombre) > 80:
            lic_nombre = lic_nombre[:77] + "..."
        
        # Obtener nombre del próximo hito
        from datetime import datetime, date
        cronograma = getattr(lic, "cronograma", None) or {}
        nombre_hito = "Próximo hito"
        
        if dias is not None:
            # Buscar el hito más próximo pendiente
            hoy = date.today()
            eventos_pendientes = []
            
            for nombre, datos in cronograma.items():
                if not isinstance(datos, dict):
                    continue
                fecha_str = datos.get("fecha_limite")
                estado = (datos.get("estado") or "").strip().lower()
                
                if not fecha_str or "pendiente" not in estado:
                    continue
                
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                    try:
                        fecha = datetime.strptime(str(fecha_str).strip()[:10], fmt).date()
                        eventos_pendientes.append((fecha, nombre))
                        break
                    except Exception:
                        continue
            
            if eventos_pendientes:
                eventos_pendientes.sort(key=lambda x: x[0])
                nombre_hito = eventos_pendientes[0][1]
        
        # ✅ FORMATO DEL BADGE SEGÚN EL VALOR DE DÍAS (MISMA LÓGICA QUE LA TABLA)
        if dias is None:
            # Sin cronograma
            self.nextDueArea.setText(
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["text_sec"]};">Sin cronograma</span>'
            )
        elif dias < 0:
            # ✅ VENCIDA (dias negativo)
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["danger"]};font-weight:bold;font-size:12pt;">'
                f'⚠️ Vencida hace {abs(dias)} día{"s" if abs(dias)!=1 else ""}</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
        elif dias == 0:
            # ✅ HOY
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["info"]};font-weight:bold;font-size:12pt;">'
                f'⏰ ¡Hoy!</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
        elif dias == 1:
            # ✅ FALTA 1 DÍA
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["warning"]};font-weight:bold;font-size:12pt;">'
                f'🟠 Falta 1 día</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
        elif dias <= 5:
            # ✅ CRÍTICO (2-5 días) - Mismo color que usa la tabla (#B45309)
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:#B45309;font-weight:bold;font-size:12pt;">'
                f'🔴 Faltan {dias} días</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
        elif dias <= 30:
            # ✅ PRÓXIMO (6-30 días)
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["info"]};font-weight:bold;font-size:11pt;">'
                f'🔵 Faltan {dias} días</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
        else:
            # ✅ NORMAL (>30 días)
            texto = (
                f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                f'<span style="color:{self.colors["success"]};font-weight:bold;font-size:11pt;">'
                f'✅ Faltan {dias} días</span><br>'
                f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
            )
            self.nextDueArea.setText(texto)
    
    def _map_to_source(self, proxy_index):
        """Mapea índice proxy al modelo fuente."""
        current_index = proxy_index
        current_model = proxy_index.model()
        
        while hasattr(current_model, 'mapToSource'):
            current_index = current_model.mapToSource(current_index)
            current_model = current_model.sourceModel()
            if current_model is None:
                break
        
        return current_index
    
    # ==================== PERSISTENCIA DE COLUMNAS ====================
    
    def _schedule_save_column_widths(self):
        """
        Programa el guardado de anchos de columnas con debounce.
        Evita guardar múltiples veces al redimensionar rápidamente.
        """
        self._save_timer.start()
    
    def _save_column_widths(self):
        """
        Guarda anchos de columnas, ordenamiento y tab activo.
        Corregido para usar los nombres correctos de atributos.
        """
        try:
            # ==================== TABLA ACTIVAS ====================
            if hasattr(self, 'table_activas') and self.table_activas:  # ✅ Nombre corregido
                header = self.table_activas.horizontalHeader()
                
                # Guardar anchos
                widths_activas = [header.sectionSize(i) for i in range(header.count())]
                self._settings.setValue("licitaciones_list/column_widths_activas", widths_activas)
                
                # Guardar ordenamiento
                sort_col = header.sortIndicatorSection()
                sort_order_enum = header.sortIndicatorOrder()
                
                if hasattr(sort_order_enum, 'value'):
                    sort_order = sort_order_enum.value
                elif isinstance(sort_order_enum, int):
                    sort_order = sort_order_enum
                else:
                    sort_order = 0
                
                self._settings.setValue("licitaciones_list/sort_col_activas", int(sort_col))
                self._settings.setValue("licitaciones_list/sort_order_activas", int(sort_order))
            
            # ==================== TABLA FINALIZADAS ====================
            if hasattr(self, 'table_finalizadas') and self.table_finalizadas:  # ✅ Nombre corregido
                header = self.table_finalizadas.horizontalHeader()
                
                # Guardar anchos
                widths_finalizadas = [header.sectionSize(i) for i in range(header.count())]
                self._settings.setValue("licitaciones_list/column_widths_finalizadas", widths_finalizadas)
                
                # Guardar ordenamiento
                sort_col = header.sortIndicatorSection()
                sort_order_enum = header.sortIndicatorOrder()
                
                if hasattr(sort_order_enum, 'value'):
                    sort_order = sort_order_enum.value
                elif isinstance(sort_order_enum, int):
                    sort_order = sort_order_enum
                else:
                    sort_order = 0
                
                self._settings.setValue("licitaciones_list/sort_col_finalizadas", int(sort_col))
                self._settings.setValue("licitaciones_list/sort_order_finalizadas", int(sort_order))
            
            # ==================== TAB ACTUAL ====================
            if hasattr(self, 'tabs') and self.tabs:
                self._settings.setValue("licitaciones_list/current_tab", self.tabs.currentIndex())
            
            # ==================== SINCRONIZAR ====================
            self._settings.sync()
            
        except Exception as e:
            print(f"[ERROR] Guardando columnas: {e}")
    
    def _restore_column_widths(self):
        """Restaura anchos de columnas y ordenamiento."""
        try:
            # ==================== TABLA ACTIVAS ====================
            if hasattr(self, 'table_activas'):  # ✅ Nombre corregido
                widths = self._settings.value("licitaciones_list/column_widths_activas")
                if widths and isinstance(widths, list):
                    header = self.table_activas.horizontalHeader()
                    for col, width in enumerate(widths):
                        if col < header.count():
                            try:
                                self.table_activas.setColumnWidth(col, int(width))
                            except (ValueError, TypeError):
                                pass
                
                sort_col = self._settings.value("licitaciones_list/sort_col_activas", 0)
                sort_order = self._settings.value("licitaciones_list/sort_order_activas", 0)
                try:
                    sort_col = int(sort_col)
                    sort_order = Qt.SortOrder(int(sort_order))
                    self.table_activas.sortByColumn(sort_col, sort_order)
                except (ValueError, TypeError):
                    pass
            
            # ==================== TABLA FINALIZADAS ====================
            if hasattr(self, 'table_finalizadas'):  # ✅ Nombre corregido
                widths = self._settings.value("licitaciones_list/column_widths_finalizadas")
                if widths and isinstance(widths, list):
                    header = self.table_finalizadas.horizontalHeader()
                    for col, width in enumerate(widths):
                        if col < header.count():
                            try:
                                self.table_finalizadas.setColumnWidth(col, int(width))
                            except (ValueError, TypeError):
                                pass
                
                sort_col = self._settings.value("licitaciones_list/sort_col_finalizadas", 0)
                sort_order = self._settings.value("licitaciones_list/sort_order_finalizadas", 0)
                try:
                    sort_col = int(sort_col)
                    sort_order = Qt.SortOrder(int(sort_order))
                    self.table_finalizadas.sortByColumn(sort_col, sort_order)
                except (ValueError, TypeError):
                    pass
            
            # ==================== TAB ACTUAL ====================
            if hasattr(self, 'tabs'):
                tab_index = self._settings.value("licitaciones_list/current_tab", 0)
                try:
                    tab_index = int(tab_index)
                    if 0 <= tab_index < self.tabs.count():
                        self.tabs.setCurrentIndex(tab_index)
                except (ValueError, TypeError):
                    pass
            
        except Exception as e:
            print(f"[ERROR] Restaurando columnas: {e}")


    def _sync_right_panel_with_selection(self):
        """
        Actualiza el badge de próximo vencimiento cuando cambia la selección.
        Muestra el próximo evento pendiente del cronograma de la licitación seleccionada.
        """
        # Determinar qué tabla está activa
        view = self.table_activas if self.tabs.currentIndex() == 0 else self.table_finalizadas
        
        if not view.selectionModel():
            self.nextDueArea.setText("-- Selecciona una Fila --")
            return

        # Obtener fila seleccionada
        sel = view.selectionModel().selectedRows()
        if not sel:
            idx = view.currentIndex()
            if not idx.isValid():
                self.nextDueArea.setText("-- Selecciona una Fila --")
                return
        else:
            idx = sel[0]

        # Obtener modelo y mapear a source
        model = view.model()
        if hasattr(model, "mapToSource"):
            src_idx = model.mapToSource(idx)
        else:
            src_idx = idx

        # Obtener objeto licitación
        lic = src_idx.siblingAtColumn(0).data(ROLE_RECORD_ROLE)
        if lic is None:
            self.nextDueArea.setText("-- Selecciona una Fila --")
            return

        # ==================== CALCULAR PRÓXIMO VENCIMIENTO ====================
        from datetime import datetime, date
        
        hoy = date.today()
        cronograma = getattr(lic, "cronograma", None) or {}

        eventos_futuros = []
        
        # Buscar eventos pendientes en el cronograma
        for nombre_hito, datos_hito in cronograma.items():
            if not isinstance(datos_hito, dict):
                continue
            
            fecha_str = datos_hito.get("fecha_limite")
            estado = (datos_hito.get("estado") or "").strip().lower()
            
            # Solo considerar eventos pendientes
            if not fecha_str or "pendiente" not in estado:
                continue
            
            # Intentar parsear la fecha
            fecha_parseada = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    fecha_parseada = datetime.strptime(str(fecha_str).strip()[:10], fmt).date()
                    break
                except Exception:
                    continue
            
            if fecha_parseada:
                eventos_futuros.append((fecha_parseada, nombre_hito, fecha_str))

        # ==================== RENDERIZAR BADGE ====================
        if eventos_futuros:
            # Ordenar por fecha (más próximo primero)
            eventos_futuros.sort(key=lambda x: x[0])
            fecha, nombre_hito, fecha_str = eventos_futuros[0]
            diferencia = (fecha - hoy).days
            
            # Obtener nombre de la licitación
            lic_nombre = getattr(lic, "nombre_proceso", None) or getattr(lic, "nombre", None) or "Licitación"
            
            # Truncar nombre si es muy largo
            if len(lic_nombre) > 80:
                lic_nombre = lic_nombre[:77] + "..."
            
            # ✅ FORMATO DEL BADGE SEGÚN URGENCIA
            if diferencia < 0:
                # Vencida (pasó la fecha)
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["danger"]};font-weight:bold;font-size:12pt;">'
                    f'⚠️ Vencida hace {abs(diferencia)} día{"s" if abs(diferencia)!=1 else ""}</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            elif diferencia == 0:
                # Vence hoy
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["warning"]};font-weight:bold;font-size:12pt;">'
                    f'⏰ ¡Vence HOY!</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            elif diferencia <= 3:
                # Crítico (1-3 días)
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["danger"]};font-weight:bold;font-size:12pt;">'
                    f'🔴 Faltan {diferencia} día{"s" if diferencia!=1 else ""}</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            elif diferencia <= 7:
                # Urgente (4-7 días)
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["warning"]};font-weight:bold;font-size:12pt;">'
                    f'🟠 Faltan {diferencia} días</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            elif diferencia <= 30:
                # Próximo (8-30 días)
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["info"]};font-weight:bold;font-size:11pt;">'
                    f'🔵 Faltan {diferencia} días</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            else:
                # Normal (más de 30 días)
                texto = (
                    f'<b style="color:{self.colors["text"]};">{lic_nombre}</b><br>'
                    f'<span style="color:{self.colors["success"]};font-weight:bold;font-size:11pt;">'
                    f'✅ Faltan {diferencia} días</span><br>'
                    f'<span style="color:{self.colors["text_sec"]};font-size:9pt;">Hito: {nombre_hito}</span>'
                )
            
            self.nextDueArea.setText(texto)
        else:
            # No hay eventos pendientes
            nombre = getattr(lic, 'nombre_proceso', 'Licitación')
            if len(nombre) > 80:
                nombre = nombre[:77] + "..."
            
            self.nextDueArea.setText(
                f'<b style="color:{self.colors["text"]};">{nombre}</b><br>'
                f'<span style="color:{self.colors["text_sec"]};">Sin cronograma pendiente</span>'
            )


    def closeEvent(self, event):
        """Guardar al cerrar."""
        try:
            self._save_column_widths()
        except:
            pass
        super().closeEvent(event)
    
    def _populate_filter_values(self) -> None:
        """Puebla los valores de los combos de filtros."""
        if not self._model:
            return
        
        # Estados únicos
        estados = set()
        empresas = set()
        
        for row in range(self._model.rowCount()):
            # Estado
            estado_idx = self._model.index(row, 7)  # Columna de estado
            estado = self._model.data(estado_idx, Qt.ItemDataRole.DisplayRole)
            if estado:
                estados.add(str(estado))
            
            # Empresa
            empresa_idx = self._model.index(row, 2)  # Columna de empresa
            empresa = self._model.data(empresa_idx, Qt.ItemDataRole.DisplayRole)
            if empresa:
                empresas.add(str(empresa))
        
        # Actualizar combos
        current_estado = self.estado_combo.currentText()
        current_empresa = self.empresa_combo.currentText()
        
        self.estado_combo.clear()
        self.estado_combo.addItem("Todos")
        self.estado_combo.addItems(sorted(estados))
        
        self.empresa_combo.clear()
        self.empresa_combo.addItem("Todas")
        self.empresa_combo.addItems(sorted(empresas))
        
        # Restaurar selección si existe
        idx = self.estado_combo.findText(current_estado)
        if idx >= 0:
            self.estado_combo.setCurrentIndex(idx)
        
        idx = self.empresa_combo.findText(current_empresa)
        if idx >= 0:
            self.empresa_combo.setCurrentIndex(idx)
    
    def _apply_filters(self) -> None:
        """Aplica los filtros a ambas tablas."""
        search_text = self.search_edit.text()
        lote_text = self.lote_edit.text()
        estado_text = self.estado_combo.currentText()
        empresa_text = self.empresa_combo.currentText()
        
        # Aplicar a cada proxy (si tiene los métodos)
        for proxy in [self._proxyActivas, self._proxyFinalizadas]:
            if hasattr(proxy, 'set_search_text'):
                proxy.set_search_text(search_text)
            if hasattr(proxy, 'set_lote_filter'):
                proxy.set_lote_filter(lote_text)
            if hasattr(proxy, 'set_estado_filter'):
                if estado_text != "Todos":
                    proxy.set_estado_filter(estado_text)
                else:
                    proxy.set_estado_filter("")
            if hasattr(proxy, 'set_empresa_filter'):
                if empresa_text != "Todas":
                    proxy.set_empresa_filter(empresa_text)
                else:
                    proxy.set_empresa_filter("")
        
        self._update_tab_counts()
        self._update_footer_stats()
    
    def _clear_filters(self) -> None:
        """Limpia todos los filtros."""
        self.search_edit.clear()
        self.lote_edit.clear()
        self.estado_combo.setCurrentIndex(0)
        self.empresa_combo.setCurrentIndex(0)
    
    def _update_tab_counts(self) -> None:
        """Actualiza los contadores en los tabs."""
        count_activas = self._proxyActivas.rowCount()
        count_finalizadas = self._proxyFinalizadas.rowCount()
        
        self.tabs.setTabText(0, f"Licitaciones Activas ({count_activas})")
        self.tabs.setTabText(1, f"Licitaciones Finalizadas ({count_finalizadas})")
    
    def _update_footer_stats(self) -> None:
        """Actualiza las estadísticas del footer."""
        if not self._model:
            return
        
        # Contar según el tab activo
        current_tab = self.tabs.currentIndex()
        proxy = self._proxyActivas if current_tab == 0 else self._proxyFinalizadas
        
        total = proxy.rowCount()
        ganadas = 0
        perdidas = 0
        lotes = 0
        
        for row in range(proxy.rowCount()):
            estado_idx = proxy.index(row, 7)
            estado = proxy.data(estado_idx, Qt.ItemDataRole.DisplayRole)
            if estado:
                estado_lower = str(estado).lower()
                if 'ganada' in estado_lower or 'adjudicada' in estado_lower:
                    ganadas += 1
                elif 'perdida' in estado_lower or 'descalificad' in estado_lower:
                    perdidas += 1
        
        # Actualizar labels
        if current_tab == 0:
            self.lbl_activas.setText(f"Activas: {total}")
        else:
            self.lbl_activas.setText(f"Finalizadas: {total}")
        
        self.lbl_ganadas.setText(f"Ganadas: {ganadas}")
        self.lbl_lotes.setText(f"Lotes Ganados: {lotes}")
        self.lbl_perdidas.setText(f"Perdidas: {perdidas}")
    
    def _on_tab_changed(self, index: int) -> None:
        """
        Maneja el cambio de tab.
        
        Args:
            index: Índice del tab seleccionado
        """
        self._update_footer_stats()
    
    def _on_double_click(self, index) -> None:
        """
        Maneja el doble clic en una fila de la tabla.
        Abre la ventana de detalles de la licitación.
        
        Args:
            index: Índice de la celda clickeada
        """
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        if not index.isValid():
            return
        
        # ✅ CORRECCIÓN: Mapear correctamente a través de múltiples proxies
        # Obtener el modelo proxy actual (puede ser MultiFilterProxyModel o StatusFilterProxyModel)
        proxy_model = index.model()
        
        # Mapear al modelo fuente (puede haber múltiples niveles de proxy)
        source_index = index
        current_model = proxy_model
        
        # Iterar hasta llegar al modelo fuente real
        while hasattr(current_model, 'mapToSource'):
            source_index = current_model.mapToSource(source_index)
            current_model = current_model.sourceModel()
            if current_model is None:
                break
        
        # Verificar que llegamos al modelo base
        if current_model is None or source_index is None or not source_index.isValid():
            print("[ERROR] No se pudo mapear al modelo fuente")
            return
        
        # Obtener licitación del modelo base
        licitacion = current_model.data(
            source_index, 
            Qt.ItemDataRole.UserRole + 1002  # ROLE_RECORD_ROLE
        )
        
        if not licitacion:
            print(f"[ERROR] No se pudo obtener licitación desde índice (row={source_index.row()})")
            return
        
        print(f"[DEBUG] Doble clic en: {licitacion.numero_proceso} (ID: {getattr(licitacion, 'id', 'N/A')})")
        
        # Abrir ventana de detalles
        dialog = LicitationDetailsWindow(
            parent=self,
            licitacion=licitacion,
            db_adapter=self.db,
            refresh_callback=self.refresh
        )
        
        dialog.exec()
        
        # Refrescar después de cerrar
        self.refresh()    
    # ==================== ACCIONES DE BOTONES ====================
    
    def _on_nueva_licitacion(self) -> None:
        """Abre el diálogo para crear una nueva licitación."""
        from app.core.models import Licitacion
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        print("[DEBUG] Abriendo ventana para nueva licitación...")
        
        # Crear objeto licitación vacío
        nueva_lic = Licitacion()
        
        # Abrir ventana de detalles
        dialog = LicitationDetailsWindow(
            parent=self,
            licitacion=nueva_lic,
            db_adapter=self.db,
            refresh_callback=self.refresh
        )
        
        # Mostrar modal
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            print("[DEBUG] Nueva licitación guardada correctamente")
            # Refrescar la tabla
            self.refresh()
    
    def _on_editar_licitacion(self) -> None:
        """Abre el diálogo para editar la licitación seleccionada."""
        from app.ui.windows.licitation_details_window import LicitationDetailsWindow
        
        # Obtener tabla activa según el tab
        current_tab = self.tabs.currentIndex()
        table = self.table_activas if current_tab == 0 else self.table_finalizadas
        
        # Obtener fila seleccionada
        selection = table.selectionModel().selectedRows()
        
        if not selection:
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, seleccione una licitación de la tabla para editar."
            )
            return
        
        # Obtener objeto licitación desde el modelo
        proxy_index = selection[0]
        source_index = proxy_index.model().mapToSource(proxy_index)
        
        licitacion = self._model.data(
            source_index,
            Qt.ItemDataRole.UserRole + 1002  # ROLE_RECORD_ROLE
        )
        
        if not licitacion:
            print("[ERROR] No se pudo obtener objeto licitación desde el modelo")
            return
        
        print(f"[DEBUG] Abriendo ventana de edición para: {licitacion.numero_proceso}")
        
        # Abrir ventana de detalles
        dialog = LicitationDetailsWindow(
            parent=self,
            licitacion=licitacion,
            db_adapter=self.db,
            refresh_callback=self.refresh
        )
        
        result = dialog.exec()
        
        if result == dialog.DialogCode.Accepted:
            print("[DEBUG] Licitación editada correctamente")
            self.refresh()


    def _show_context_menu(self, pos) -> None:
        """
        Muestra menú contextual al hacer clic derecho en la tabla.
        
        Args:
            pos: Posición del clic
        """
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        # Obtener tabla que generó el evento
        sender = self.sender()
        if not isinstance(sender, QTableView):
            return
        
        # Verificar si hay selección
        selection = sender.selectionModel().selectedRows()
        if not selection:
            return
        
        # Crear menú
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #7C4DFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3E3E42;
                margin: 5px 0px;
            }
        """)
        
        # Acciones
        action_editar = QAction(edit_icon(), "Editar", self)
        action_editar.triggered.connect(self._on_editar_licitacion)
        menu.addAction(action_editar)
        
        action_ver_detalles = QAction(eye_icon(), "Ver Detalles", self)
        action_ver_detalles.triggered.connect(lambda: self._on_double_click(selection[0]))
        menu.addAction(action_ver_detalles)
        
        menu.addSeparator()
        
        action_reporte = QAction(chart_icon(), "Generar Reporte", self)
        action_reporte.triggered.connect(self._on_generar_reporte_seleccionada)
        menu.addAction(action_reporte)
        
        menu.addSeparator()
        
        action_copiar_codigo = QAction(list_icon(), "Copiar Código", self)
        action_copiar_codigo.triggered.connect(lambda: self._copiar_codigo_seleccionada(sender))
        menu.addAction(action_copiar_codigo)
        
        # Mostrar menú en la posición del cursor
        menu.exec(sender.viewport().mapToGlobal(pos))

    def _on_generar_reporte_seleccionada(self) -> None:
        """Genera reporte de la licitación seleccionada desde el menú contextual."""
        # Obtener ventana principal
        main_window = self.window()
        if hasattr(main_window, '_abrir_reporte_de_seleccionada'):
            main_window._abrir_reporte_de_seleccionada()
        else:
            QMessageBox.warning(self, "No Disponible", "La función de reportes no está disponible.")

    def _copiar_codigo_seleccionada(self, table: QTableView) -> None:
        """Copia el código de proceso de la licitación seleccionada al portapapeles."""
        from PyQt6.QtWidgets import QApplication
        
        selection = table.selectionModel().selectedRows()
        if not selection:
            return
        
        # Obtener código de la columna 0
        codigo_index = selection[0].model().index(selection[0].row(), 0)
        codigo = selection[0].model().data(codigo_index, Qt.ItemDataRole.DisplayRole)
        
        if codigo:
            clipboard = QApplication.clipboard()
            clipboard.setText(str(codigo))
            self.statusBar().showMessage(f"✓ Código '{codigo}' copiado al portapapeles", 2000) if hasattr(self, 'statusBar') else None
    # ==================== REFRESH ====================
    def _on_refresh_data(self):
        """
        Recarga los datos desde Firestore ignorando el caché.
        Muestra un diálogo de confirmación y progreso.
        """
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
        from PyQt6.QtCore import Qt
        
        # Confirmar acción
        reply = QMessageBox.question(
            self,
            "Actualizar Datos",
            "¿Recargar todos los datos desde Firestore?\n\n"
            "Esto invalidará el caché local y puede tomar unos segundos.\n"
            "Se incrementará el uso de cuota de Firestore.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Deshabilitar botón temporalmente
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("Actualizando...")
        
        # Crear diálogo de progreso
        progress = QProgressDialog(
            "Recargando datos desde Firestore...",
            None,  # Sin botón de cancelar
            0, 0,  # Indeterminado
            self
        )
        progress.setWindowTitle("Actualizando")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            print("[INFO] Recargando datos desde Firestore (refresh manual)...")
            QApplication.processEvents()
            
            if self.db:
                # ❌ ELIMINAR ESTA LÍNEA (duplicada):
                # self.db.invalidate_cache()
                
                # ✅ SOLO ESTA LÍNEA (ya invalida internamente):
                licitaciones = self.db.load_all_licitaciones(force_refresh=True)
                print(f"[INFO] ✓ {len(licitaciones)} licitaciones recargadas desde Firestore")
                
                # ✅ USAR set_rows() del modelo
                self._model.set_rows(licitaciones)
                print("[DEBUG] Modelo actualizado con nuevos datos")
                
                # Refrescar vista
                self.refresh()
                
                # Actualizar contadores si existen estos métodos
                if hasattr(self, '_update_tab_counts'):
                    self._update_tab_counts()
                if hasattr(self, '_update_footer_stats'):
                    self._update_footer_stats()
            
            # Cerrar diálogo de progreso
            progress.close()
            
            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "Actualización Completa",
                f"Se recargaron {len(licitaciones)} licitaciones desde Firestore.\n\n"
                f"El caché local ha sido actualizado."
            )
            
        except Exception as e:
            progress.close()
            
            print(f"[ERROR] Error al recargar datos: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self,
                "Error al Actualizar",
                f"No se pudieron recargar los datos desde Firestore:\n\n{e}"
            )
        
        finally:
            # Rehabilitar botón
            self.btn_refresh.setEnabled(True)
            self.btn_refresh.setText("Actualizar Datos")
            
    def refresh(self) -> None:
        """Refresca la vista actualizando filtros y estadísticas."""
        # print("[DEBUG] Refrescando LicitacionesListView...")
        self._populate_filter_values()
        self._apply_filters()