"""
Dashboard View - Vista principal con estadísticas.
Muestra tarjetas de métricas clave y un placeholder para gráficos.
"""
from __future__ import annotations
from typing import Optional, List, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QFrame, QSizePolicy
)

from app.ui.widgets.modern_widgets import StatCard
from app.core.db_adapter import DatabaseAdapter
from app.core.models import Licitacion


class DashboardView(QWidget):
    """
    Vista de dashboard con estadísticas clave.
    Muestra métricas como licitaciones activas, ganadas, por vencer y ratio de éxito.
    """
    
    def __init__(
        self, 
        db: Optional[DatabaseAdapter] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Inicializa la vista de dashboard.
        
        Args:
            db: Adaptador de base de datos para cargar estadísticas
            parent: Widget padre
        """
        super().__init__(parent)
        self.db = db
        self._stat_cards: dict[str, StatCard] = {}
        self._setup_ui()
        if self.db:
            self.refresh_stats()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz del dashboard."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Grid de tarjetas de estadísticas
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        
        # Crear tarjetas de estadísticas
        self._stat_cards['activas'] = StatCard(
            title="Total Activas",
            value="0",
            accent_color="#7C4DFF",  # Purple
            icon_text="📋"
        )
        
        self._stat_cards['ganadas'] = StatCard(
            title="Ganadas (YTD)",
            value="0",
            accent_color="#00C853",  # Green
            icon_text="✓"
        )
        
        self._stat_cards['por_vencer'] = StatCard(
            title="Por Vencer (7d)",
            value="0",
            accent_color="#FFAB00",  # Orange
            icon_text="⚠"
        )
        
        self._stat_cards['ratio'] = StatCard(
            title="Ratio Éxito",
            value="0%",
            accent_color="#448AFF",  # Blue
            icon_text="📊"
        )
        
        # Añadir tarjetas al grid (2x2)
        stats_grid.addWidget(self._stat_cards['activas'], 0, 0)
        stats_grid.addWidget(self._stat_cards['ganadas'], 0, 1)
        stats_grid.addWidget(self._stat_cards['por_vencer'], 0, 2)
        stats_grid.addWidget(self._stat_cards['ratio'], 0, 3)
        
        main_layout.addLayout(stats_grid)
        
        # Placeholder para gráfico
        chart_placeholder = self._create_chart_placeholder()
        main_layout.addWidget(chart_placeholder, 1)
    
    def _create_chart_placeholder(self) -> QFrame:
        """
        Crea un placeholder para el gráfico de tendencias.
        
        Returns:
            Frame con el placeholder del gráfico
        """
        placeholder = QFrame()
        placeholder.setObjectName("ChartPlaceholder")
        placeholder.setStyleSheet("""
            #ChartPlaceholder {
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 12px;
            }
        """)
        placeholder.setMinimumHeight(300)
        
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ícono
        icon_label = QLabel("📈")
        icon_label.setStyleSheet("""
            font-size: 48px;
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Texto
        text_label = QLabel("Gráfico de Licitaciones por Mes")
        text_label.setStyleSheet("""
            font-size: 16px;
            color: #B0B0B0;
            margin-top: 15px;
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("(Placeholder - Integrar Matplotlib/PyQtGraph)")
        subtitle_label.setStyleSheet("""
            font-size: 12px;
            color: #6B7280;
            margin-top: 5px;
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(subtitle_label)
        
        return placeholder
    
    def refresh_stats(self) -> None:
        """Actualiza las estadísticas del dashboard cargando datos de la base de datos."""
        if not self.db:
            return
        
        try:
            # Cargar todas las licitaciones
            licitaciones: List[Any] = self.db.load_all_licitaciones() or []
            
            # Calcular estadísticas
            activas = self._count_activas(licitaciones)
            ganadas = self._count_ganadas(licitaciones)
            por_vencer = self._count_por_vencer(licitaciones)
            ratio = self._calculate_ratio(licitaciones)
            
            # Actualizar tarjetas
            self._stat_cards['activas'].update_value(str(activas))
            self._stat_cards['ganadas'].update_value(str(ganadas))
            self._stat_cards['por_vencer'].update_value(str(por_vencer))
            self._stat_cards['ratio'].update_value(f"{ratio}%")
            
        except Exception as e:
            print(f"[Dashboard] Error al refrescar estadísticas: {e}")
    
    def _count_activas(self, licitaciones: List[Any]) -> int:
        """
        Cuenta licitaciones activas (no finalizadas).
        
        Args:
            licitaciones: Lista de licitaciones
            
        Returns:
            Número de licitaciones activas
        """
        count = 0
        for lic in licitaciones:
            if hasattr(lic, 'estado_actual'):
                estado = getattr(lic, 'estado_actual', '')
                # Considerar activas las que no están finalizadas
                if estado and estado.lower() not in ['ganada', 'perdida', 'descalificada', 'cancelada']:
                    count += 1
            elif not hasattr(lic, 'fecha_finalizacion'):
                count += 1
        return count
    
    def _count_ganadas(self, licitaciones: List[Any]) -> int:
        """
        Cuenta licitaciones ganadas.
        
        Args:
            licitaciones: Lista de licitaciones
            
        Returns:
            Número de licitaciones ganadas
        """
        count = 0
        for lic in licitaciones:
            estado = getattr(lic, 'estado_actual', '')
            if estado and 'ganada' in estado.lower():
                count += 1
        return count
    
    def _count_por_vencer(self, licitaciones: List[Any]) -> int:
        """
        Cuenta licitaciones que vencen en los próximos 7 días.
        
        Args:
            licitaciones: Lista de licitaciones
            
        Returns:
            Número de licitaciones por vencer
        """
        from datetime import datetime, timedelta
        
        count = 0
        hoy = datetime.now().date()
        limite = hoy + timedelta(days=7)
        
        for lic in licitaciones:
            fecha_cierre = getattr(lic, 'fecha_cierre_sobre_b', None)
            if fecha_cierre:
                # Convertir fecha a date si es datetime
                if isinstance(fecha_cierre, datetime):
                    fecha_cierre = fecha_cierre.date()
                elif isinstance(fecha_cierre, str):
                    try:
                        fecha_cierre = datetime.fromisoformat(fecha_cierre).date()
                    except:
                        continue
                
                if hoy <= fecha_cierre <= limite:
                    count += 1
        
        return count
    
    def _calculate_ratio(self, licitaciones: List[Any]) -> int:
        """
        Calcula el ratio de éxito (ganadas / finalizadas).
        
        Args:
            licitaciones: Lista de licitaciones
            
        Returns:
            Porcentaje de éxito (0-100)
        """
        ganadas = 0
        finalizadas = 0
        
        for lic in licitaciones:
            estado = getattr(lic, 'estado_actual', '')
            if estado:
                estado_lower = estado.lower()
                if estado_lower in ['ganada', 'perdida', 'descalificada']:
                    finalizadas += 1
                    if estado_lower == 'ganada':
                        ganadas += 1
        
        if finalizadas == 0:
            return 0
        
        return int((ganadas / finalizadas) * 100)
    
    def set_database(self, db: DatabaseAdapter) -> None:
        """
        Establece el adaptador de base de datos y refresca las estadísticas.
        
        Args:
            db: Adaptador de base de datos
        """
        self.db = db
        self.refresh_stats()
