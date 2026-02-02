"""
Licitaciones List View - Vista de tabla de licitaciones.
Muestra la tabla de licitaciones con filtros y controles, usando los widgets modernos.
"""
from __future__ import annotations
from typing import Optional, Any

from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableView, QTabWidget, QHeaderView,
    QFrame, QGroupBox, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QFont

from app.core.db_adapter import DatabaseAdapter
from app.core.logic.status_engine import StatusEngine, DefaultStatusEngine
from app.ui.models.licitaciones_table_model import LicitacionesTableModel
from app.ui.models.status_proxy_model import StatusFilterProxyModel
from app.ui.delegates.row_color_delegate import RowColorDelegate
from app.ui.delegates.progress_bar_delegate import ProgressBarDelegate
from app.ui.delegates.heatmap_delegate import HeatmapDelegate

# Roles del modelo
DOCS_PROGRESS_ROLE = Qt.ItemDataRole.UserRole + 1012
DIFERENCIA_PCT_ROLE = Qt.ItemDataRole.UserRole + 1013


class LicitacionesListView(QWidget):
    """
    Vista de lista de licitaciones con tabla, filtros y estadísticas.
    Migra la funcionalidad de la tabla desde el antiguo main_window.
    """
    
    # Señales
    detail_requested = pyqtSignal(object)  # Emite licitación seleccionada
    
    def __init__(
        self,
        model: LicitacionesTableModel,
        db: Optional[DatabaseAdapter] = None,
        status_engine: Optional[StatusEngine] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Inicializa la vista de lista de licitaciones.
        
        Args:
            model: Modelo de tabla de licitaciones
            db: Adaptador de base de datos
            status_engine: Motor de estados para las licitaciones
            parent: Widget padre
        """
        super().__init__(parent)
        self._model = model
        self.db = db
        self._status = status_engine or DefaultStatusEngine()
        
        self._settings = QSettings("Zoeccivil", "Licitaciones")
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(220)
        
        self._setup_ui()
        self._setup_models()
        self._wire_signals()
        self._populate_filter_values()
        self._apply_filters()
        self._update_tab_counts()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de la vista."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Barra de herramientas superior
        toolbar = self._create_toolbar()
        main_layout.addLayout(toolbar)
        
        # Panel de filtros
        filters_panel = self._create_filters_panel()
        main_layout.addWidget(filters_panel)
        
        # Tabs de tabla
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
        
        # Crear tablas
        self.table_activas = self._create_table_view()
        self.table_finalizadas = self._create_table_view()
        
        self.tabs.addTab(self.table_activas, "Licitaciones Activas (0)")
        self.tabs.addTab(self.table_finalizadas, "Licitaciones Finalizadas (0)")
        
        main_layout.addWidget(self.tabs, 1)
        
        # Footer con estadísticas
        footer = self._create_footer()
        main_layout.addLayout(footer)
    
    def _create_toolbar(self) -> QHBoxLayout:
        """
        Crea la barra de herramientas superior.
        
        Returns:
            Layout con los botones de acción
        """
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # Botón Nueva Licitación
        self.btn_nueva = QPushButton("➕  Nueva Licitación")
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
        
        # Botón Editar
        self.btn_editar = QPushButton("✏️  Editar Seleccionada")
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
        
        toolbar.addWidget(self.btn_nueva)
        toolbar.addWidget(self.btn_editar)
        toolbar.addStretch()
        
        return toolbar
    
    def _create_filters_panel(self) -> QFrame:
        """
        Crea el panel de filtros y búsqueda.
        
        Returns:
            Frame con los controles de filtrado
        """
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
        
        layout = QGridLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Campo de búsqueda de proceso
        label_buscar = QLabel("Buscar Proceso")
        label_buscar.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ej: DGAP-CCC...")
        self.search_edit.setFixedHeight(35)
        
        # Campo de búsqueda de lote
        label_lote = QLabel("Contiene Lote")
        label_lote.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.lote_edit = QLineEdit()
        self.lote_edit.setPlaceholderText("Descripción...")
        self.lote_edit.setFixedHeight(35)
        
        # Combo estado
        label_estado = QLabel("Estado")
        label_estado.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.estado_combo = QComboBox()
        self.estado_combo.addItem("Todos")
        self.estado_combo.setFixedHeight(35)
        
        # Combo empresa
        label_empresa = QLabel("Empresa")
        label_empresa.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.empresa_combo = QComboBox()
        self.empresa_combo.addItem("Todas")
        self.empresa_combo.setFixedHeight(35)
        
        # Botón limpiar
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
        
        # Añadir al layout
        layout.addWidget(label_buscar, 0, 0)
        layout.addWidget(self.search_edit, 1, 0)
        layout.addWidget(label_lote, 0, 1)
        layout.addWidget(self.lote_edit, 1, 1)
        layout.addWidget(label_estado, 0, 2)
        layout.addWidget(self.estado_combo, 1, 2)
        layout.addWidget(label_empresa, 0, 3)
        layout.addWidget(self.empresa_combo, 1, 3)
        layout.addWidget(self.btn_limpiar, 1, 4)
        
        # Configurar tamaños de columna
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 2)
        layout.setColumnStretch(4, 0)
        
        return panel
    
    def _create_table_view(self) -> QTableView:
        """
        Crea una vista de tabla configurada.
        
        Returns:
            Vista de tabla lista para usar
        """
        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.setIconSize(QSize(16, 16))
        
        # Aplicar delegados para estilos especiales
        table.setItemDelegate(RowColorDelegate(table))
        
        return table
    
    def _create_footer(self) -> QHBoxLayout:
        """
        Crea el footer con estadísticas.
        
        Returns:
            Layout con las etiquetas de estadísticas
        """
        footer = QHBoxLayout()
        footer.setSpacing(20)
        
        # Labels de estadísticas
        self.lbl_activas = QLabel("Activas: 0")
        self.lbl_ganadas = QLabel("Ganadas: 0")
        self.lbl_lotes = QLabel("Lotes Ganados: 0")
        self.lbl_perdidas = QLabel("Perdidas: 0")
        
        # Aplicar estilos
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
    
    def _setup_models(self) -> None:
        """Configura los modelos proxy para las tablas."""
        # Proxy para activas
        self._proxy_activas = StatusFilterProxyModel(
            show_finalizadas=False, 
            status_engine=self._status
        )
        self._proxy_activas.setSourceModel(self._model)
        self.table_activas.setModel(self._proxy_activas)
        
        # Proxy para finalizadas
        self._proxy_finalizadas = StatusFilterProxyModel(
            show_finalizadas=True, 
            status_engine=self._status
        )
        self._proxy_finalizadas.setSourceModel(self._model)
        self.table_finalizadas.setModel(self._proxy_finalizadas)
        
        # Configurar delegados para progress bar y heatmap
        self._apply_delegates()
        
        # Ocultar columna de lotes (si existe)
        try:
            self.table_activas.hideColumn(8)
            self.table_finalizadas.hideColumn(8)
        except:
            pass
    
    def _apply_delegates(self) -> None:
        """Aplica delegados personalizados a las columnas específicas."""
        # Progress bar para columna de documentos (col 4)
        progress_delegate = ProgressBarDelegate(
            column=4,
            role=DOCS_PROGRESS_ROLE,
            parent=self
        )
        self.table_activas.setItemDelegateForColumn(4, progress_delegate)
        self.table_finalizadas.setItemDelegateForColumn(4, progress_delegate)
        
        # Heatmap para columna de diferencia (col 5)
        heatmap_delegate = HeatmapDelegate(
            column=5,
            role=DIFERENCIA_PCT_ROLE,
            parent=self
        )
        self.table_activas.setItemDelegateForColumn(5, heatmap_delegate)
        self.table_finalizadas.setItemDelegateForColumn(5, heatmap_delegate)
    
    def _wire_signals(self) -> None:
        """Conecta las señales de los controles."""
        # Filtros
        self.search_edit.textChanged.connect(self._debounce.start)
        self.lote_edit.textChanged.connect(self._debounce.start)
        self.estado_combo.currentIndexChanged.connect(self._apply_filters)
        self.empresa_combo.currentIndexChanged.connect(self._apply_filters)
        self.btn_limpiar.clicked.connect(self._clear_filters)
        self._debounce.timeout.connect(self._apply_filters)
        
        # Tabs
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Doble clic en tabla
        self.table_activas.doubleClicked.connect(self._on_double_click)
        self.table_finalizadas.doubleClicked.connect(self._on_double_click)
    
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
        
        # Aplicar a cada proxy
        for proxy in [self._proxy_activas, self._proxy_finalizadas]:
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
        count_activas = self._proxy_activas.rowCount()
        count_finalizadas = self._proxy_finalizadas.rowCount()
        
        self.tabs.setTabText(0, f"Licitaciones Activas ({count_activas})")
        self.tabs.setTabText(1, f"Licitaciones Finalizadas ({count_finalizadas})")
    
    def _update_footer_stats(self) -> None:
        """Actualiza las estadísticas del footer."""
        if not self._model:
            return
        
        # Contar según el tab activo
        current_tab = self.tabs.currentIndex()
        proxy = self._proxy_activas if current_tab == 0 else self._proxy_finalizadas
        
        total = proxy.rowCount()
        ganadas = 0
        perdidas = 0
        lotes = 0
        
        for row in range(proxy.rowCount()):
            estado_idx = proxy.index(row, 7)
            estado = proxy.data(estado_idx, Qt.ItemDataRole.DisplayRole)
            if estado:
                estado_lower = str(estado).lower()
                if 'ganada' in estado_lower:
                    ganadas += 1
                elif 'perdida' in estado_lower:
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
        
        Args:
            index: Índice de la celda clickeada
        """
        if not index.isValid():
            return
        
        # Obtener el objeto licitación del modelo
        source_index = index.model().mapToSource(index)
        licitacion = self._model.data(
            source_index, 
            Qt.ItemDataRole.UserRole + 1002  # ROLE_RECORD_ROLE
        )
        
        if licitacion:
            self.detail_requested.emit(licitacion)
    
    def refresh(self) -> None:
        """Refresca la vista actualizando filtros y estadísticas."""
        self._populate_filter_values()
        self._apply_filters()
