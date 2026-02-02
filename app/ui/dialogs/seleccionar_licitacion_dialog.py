"""
Diálogo para seleccionar una licitación de una lista.
Usado para generar reportes individuales.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.core.db_adapter import DatabaseAdapter


class SeleccionarLicitacionDialog(QDialog):
    """
    Diálogo para seleccionar una licitación de la lista completa.
    Incluye búsqueda y filtrado.
    """
    
    def __init__(self, db: Optional[DatabaseAdapter], parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_licitacion = None
        
        self.setWindowTitle("Seleccionar Licitación")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        self._setup_ui()
        self._load_licitaciones()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Seleccione una licitación para generar el reporte:")
        title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #7C4DFF;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        search_label = QLabel("🔍 Buscar:")
        search_label.setStyleSheet("font-size: 11pt; font-weight: 600;")
        search_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar por código, nombre, institución o estado...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 10pt;
                border: 2px solid #3E3E42;
                border-radius: 6px;
                background-color: #2D2D30;
                color: #E6E9EF;
            }
            QLineEdit:focus {
                border-color: #7C4DFF;
            }
        """)
        self.search_box.textChanged.connect(self._filter_table)
        search_layout.addWidget(self.search_box, 1)
        
        layout.addLayout(search_layout)
        
        # Contador
        self.lbl_contador = QLabel("Cargando...")
        self.lbl_contador.setStyleSheet("font-size: 9pt; color: #B9C0CC;")
        layout.addWidget(self.lbl_contador)
        
        # Tabla
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Código", "Nombre", "Institución", "Estado"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.accept)
        
        # Configurar headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Estilos
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #3E3E42;
                background-color: #252526;
                alternate-background-color: #2D2D30;
                selection-background-color: #7C4DFF;
                selection-color: white;
                border: 1px solid #3E3E42;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #2D2D30;
                color: #E6E9EF;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #7C4DFF;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table, 1)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #3E3E42;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4E4E52;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_select = QPushButton("Seleccionar")
        btn_select.setDefault(True)
        btn_select.setStyleSheet("""
            QPushButton {
                background-color: #7C4DFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #6C3FEF;
            }
            QPushButton:pressed {
                background-color: #5C2FDF;
            }
        """)
        btn_select.clicked.connect(self.accept)
        btn_layout.addWidget(btn_select)
        
        layout.addLayout(btn_layout)
    
    def _load_licitaciones(self):
        """Carga todas las licitaciones en la tabla."""
        if not self.db:
            self.lbl_contador.setText("❌ No hay conexión a la base de datos")
            return
        
        try:
            licitaciones = self.db.load_all_licitaciones() or []
            self.table.setRowCount(0)
            
            if not licitaciones:
                self.lbl_contador.setText("⚠️ No hay licitaciones en el sistema")
                return
            
            for lic in licitaciones:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Datos
                codigo = getattr(lic, 'numero_proceso', 'N/A') or 'N/A'
                nombre = getattr(lic, 'nombre_proceso', 'N/A') or 'N/A'
                institucion = getattr(lic, 'institucion', 'N/A') or 'N/A'
                estado = getattr(lic, 'estado', 'N/A') or 'N/A'
                
                # Items
                item_codigo = QTableWidgetItem(codigo)
                item_nombre = QTableWidgetItem(nombre)
                item_institucion = QTableWidgetItem(institucion)
                item_estado = QTableWidgetItem(estado)
                
                # Colorear estado
                estado_lower = estado.lower()
                if 'ganada' in estado_lower or 'adjudicada' in estado_lower:
                    item_estado.setForeground(QColor("#00C853"))
                elif 'perdida' in estado_lower or 'descalificad' in estado_lower:
                    item_estado.setForeground(QColor("#FF5252"))
                elif 'cancelada' in estado_lower or 'desierta' in estado_lower:
                    item_estado.setForeground(QColor("#FFA726"))
                else:
                    item_estado.setForeground(QColor("#448AFF"))
                
                # Centrar estado
                item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Añadir a tabla
                self.table.setItem(row, 0, item_codigo)
                self.table.setItem(row, 1, item_nombre)
                self.table.setItem(row, 2, item_institucion)
                self.table.setItem(row, 3, item_estado)
                
                # Guardar referencia a la licitación en la primera columna
                item_codigo.setData(Qt.ItemDataRole.UserRole, lic)
            
            # Actualizar contador
            self._update_contador()
            
        except Exception as e:
            self.lbl_contador.setText(f"❌ Error cargando licitaciones: {e}")
            import traceback
            traceback.print_exc()
    
    def _filter_table(self, text: str):
        """Filtra la tabla según el texto de búsqueda."""
        text = text.lower().strip()
        visible_count = 0
        
        for row in range(self.table.rowCount()):
            match = False
            
            if not text:
                match = True
            else:
                # Buscar en todas las columnas
                for col in range(4):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        match = True
                        break
            
            self.table.setRowHidden(row, not match)
            if match:
                visible_count += 1
        
        # Actualizar contador
        total = self.table.rowCount()
        if text:
            self.lbl_contador.setText(f"📊 Mostrando {visible_count} de {total} licitaciones")
        else:
            self.lbl_contador.setText(f"📊 Total: {total} licitaciones")
    
    def _update_contador(self):
        """Actualiza el label contador."""
        total = self.table.rowCount()
        self.lbl_contador.setText(f"📊 Total: {total} licitaciones - Haga doble clic para seleccionar")
    
    def get_selected_licitacion(self):
        """
        Obtiene la licitación seleccionada.
        
        Returns:
            Licitacion object o None si no hay selección
        """
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            item_codigo = self.table.item(row, 0)
            if item_codigo:
                return item_codigo.data(Qt.ItemDataRole.UserRole)
        return None