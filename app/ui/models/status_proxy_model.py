from PyQt6.QtCore import QSortFilterProxyModel, Qt

ROLE_RECORD_ROLE = Qt.ItemDataRole.UserRole + 1002


class StatusFilterProxyModel(QSortFilterProxyModel):
    """
    Proxy con filtros tolerantes:
    - _filter_estado puede ser str o colección (set/list/tuple) de cadenas.
    - Filtros de empresa y lote robustos a datos faltantes.
    - Evita llamar .lower() sobre tipos no cadena.
    """

    def __init__(self, show_finalizadas: bool = False, status_engine=None, parent=None):
        super().__init__(parent)
        self.show_finalizadas = show_finalizadas
        self.status_engine = status_engine
        self._search_text = ""
        self._filter_estado = "Todos"      # str | Iterable[str]
        self._filter_empresa = "Todas"     # str | Iterable[str]
        self._filter_lote = ""
        self._filter_lote_contains = ""

    # ---------- Setters de filtros ----------
    def set_search_text(self, text):
        self._search_text = text or ""
        self.invalidateFilter()

    def set_filter_estado(self, estado):
        """
        estado: str o colección de cadenas. 'Todos' desactiva el filtro.
        """
        self._filter_estado = estado if estado not in (None, "") else "Todos"
        self.invalidateFilter()

    def set_filter_empresa(self, empresa):
        """
        empresa: str (nombre) o colección; 'Todas' desactiva el filtro.
        """
        self._filter_empresa = empresa if empresa not in (None, "") else "Todas"
        self.invalidateFilter()

    def set_filter_lote(self, lote: str):
        self._filter_lote = (lote or "").strip()
        self.invalidateFilter()

    def set_filter_lote_contains(self, text: str):
        self._filter_lote_contains = (text or "").strip()
        self.invalidateFilter()

    # ---------- Utilidades internas ----------
    @staticmethod
    def _to_text(val) -> str:
        return ("" if val is None else str(val)).strip()

    @staticmethod
    def _to_lower(val) -> str:
        return StatusFilterProxyModel._to_text(val).lower()

    @staticmethod
    def _iter_lower(it) -> list[str]:
        try:
            return [StatusFilterProxyModel._to_lower(v) for v in it]
        except TypeError:
            # no iterable
            return [StatusFilterProxyModel._to_lower(it)]

    # ---------- Filtro principal ----------
    def filterAcceptsRow(self, source_row, source_parent):
        """
        Filtra filas según si la licitación está finalizada o activa.
        
        Returns:
            True si la fila debe mostrarse, False en caso contrario.
        """
        model = self.sourceModel()
        if model is None:
            return True
        
        index = model.index(source_row, 0, source_parent)
        lic = model.data(index, role=ROLE_RECORD_ROLE)
        
        if lic is None:
            return False
        
        # ✅ Filtrado por activas/finalizadas (si hay engine)
        if self.status_engine is not None:
            try:
                es_finalizada = self.status_engine.is_finalizada(lic)
                
                # Si queremos finalizadas, solo mostrar finalizadas
                if self.show_finalizadas:
                    if not es_finalizada:
                        return False
                # Si queremos activas, solo mostrar activas
                else:
                    if es_finalizada:
                        return False
            
            except Exception as e:
                # Si el engine falla, mostrar la fila por defecto
                print(f"[WARNING] Error en status_engine.is_finalizada(): {e}")
                pass
        
        # ✅ CRÍTICO: Si llegamos aquí, la fila pasa el filtro
        return True