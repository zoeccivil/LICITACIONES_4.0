"""
Multi-Filter Proxy Model - Modelo proxy con múltiples filtros.
Permite filtrar por código de proceso, lote, estado y empresa simultáneamente.
"""
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from typing import Optional


class MultiFilterProxyModel(QSortFilterProxyModel):
    """
    Proxy model que soporta filtrado por múltiples campos.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._lote_filter = ""
        self._estado_filter = ""
        self._empresa_filter = ""
        
        # Configurar filtrado case-insensitive
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setRecursiveFilteringEnabled(True)
    
    def set_search_text(self, text: str):
        """
        Filtra por código de proceso (columna 0).
        
        Args:
            text: Texto a buscar en el código de proceso
        """
        self._search_text = text.strip()
        self.invalidateFilter()
    
    def set_lote_filter(self, text: str):
        """
        Filtra por descripción de lote (columna 1).
        
        Args:
            text: Texto a buscar en la descripción del lote
        """
        self._lote_filter = text.strip()
        self.invalidateFilter()
    
    def set_estado_filter(self, estado: str):
        """
        Filtra por estado exacto (columna 7).
        
        Args:
            estado: Estado a filtrar (debe coincidir exactamente)
        """
        self._estado_filter = estado.strip()
        self.invalidateFilter()
    
    def set_empresa_filter(self, empresa: str):
        """
        Filtra por nombre de empresa (columna 2).
        
        Args:
            empresa: Nombre de empresa a buscar
        """
        self._empresa_filter = empresa.strip()
        self.invalidateFilter()
    
    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        """
        Determina si una fila pasa todos los filtros activos.
        
        Args:
            source_row: Índice de la fila en el modelo fuente
            source_parent: Índice padre en el modelo fuente
            
        Returns:
            True si la fila pasa todos los filtros, False en caso contrario
        """
        model = self.sourceModel()
        
        if not model:
            return True
        
        # Filtro de búsqueda de proceso (columna 0 - CODIGO)
        if self._search_text:
            idx = model.index(source_row, 0, source_parent)
            data = model.data(idx, Qt.ItemDataRole.DisplayRole)
            if data:
                if self._search_text.lower() not in str(data).lower():
                    return False
            else:
                # Si no hay datos y hay filtro activo, no pasar la fila
                return False
        
        # Filtro de lote (columna 1 - NOMBRE PROCESO o descripción)
        if self._lote_filter:
            idx = model.index(source_row, 1, source_parent)
            data = model.data(idx, Qt.ItemDataRole.DisplayRole)
            if data:
                if self._lote_filter.lower() not in str(data).lower():
                    return False
            else:
                return False
        
        # Filtro de estado (columna 7 - ESTATUS)
        # Coincidencia exacta (case-insensitive)
        if self._estado_filter:
            idx = model.index(source_row, 7, source_parent)
            data = model.data(idx, Qt.ItemDataRole.DisplayRole)
            if data:
                if self._estado_filter.lower() != str(data).lower():
                    return False
            else:
                return False
        
        # Filtro de empresa (columna 2 - EMPRESA)
        # Búsqueda parcial (case-insensitive)
        if self._empresa_filter:
            idx = model.index(source_row, 2, source_parent)
            data = model.data(idx, Qt.ItemDataRole.DisplayRole)
            if data:
                if self._empresa_filter.lower() not in str(data).lower():
                    return False
            else:
                return False
        
        # Si pasó todos los filtros, aceptar la fila
        return True
    
    def clear_all_filters(self):
        """
        Limpia todos los filtros activos.
        """
        self._search_text = ""
        self._lote_filter = ""
        self._estado_filter = ""
        self._empresa_filter = ""
        self.invalidateFilter()
    
    def get_active_filters(self) -> dict:
        """
        Obtiene un diccionario con los filtros activos.
        
        Returns:
            Diccionario con los filtros activos y sus valores
        """
        return {
            "search_text": self._search_text,
            "lote": self._lote_filter,
            "estado": self._estado_filter,
            "empresa": self._empresa_filter
        }