"""
Dashboard View - Vista principal del dashboard con KPIs y gráficos.
Muestra métricas generales de todas las licitaciones.
"""
from __future__ import annotations
from typing import Optional, Dict, List
from collections import Counter
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QGroupBox, QSplitter
)
from PyQt6.QtGui import QColor, QPalette, QGuiApplication

from app.core.db_adapter import DatabaseAdapter

# Matplotlib (opcional)
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None


class DashboardView(QWidget):
    """
    Vista del dashboard general con KPIs, gráficos y métricas.
    """
    
    def __init__(self, db: Optional[DatabaseAdapter] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db
        
        # Datos en caché
        self._licitaciones = []
        self._stats = {}
        
        # Obtener colores del tema
        self._resolve_theme_colors()
        
        # Configurar UI
        self._setup_ui()
        
        # Cargar datos iniciales
        self.refresh_stats()
    
    def _resolve_theme_colors(self):
        """Obtiene colores del tema activo."""
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
        
        self.colors = {
            "accent": get_color(QPalette.ColorRole.Highlight, "#7C4DFF"),
            "text": get_color(QPalette.ColorRole.Text, "#E6E9EF"),
            "text_sec": get_color(QPalette.ColorRole.PlaceholderText, "#B9C0CC"),
            "window": get_color(QPalette.ColorRole.Window, "#1E1E1E"),
            "base": get_color(QPalette.ColorRole.Base, "#252526"),
            "alt": get_color(QPalette.ColorRole.AlternateBase, "#2D2D30"),
            "border": get_color(QPalette.ColorRole.Mid, "#3A4152"),
            "success": "#00C853",
            "danger": "#FF5252",
            "warning": "#FFA726",
            "info": "#448AFF",
        }
    
    def _setup_ui(self):
        """Configura la interfaz del dashboard."""
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Scroll area para contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # Título
        title = QLabel("Dashboard General")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 28pt;
                font-weight: bold;
                color: {self.colors['accent']};
                padding: 10px 0;
            }}
        """)
        content_layout.addWidget(title)
        
        # KPIs superiores
        kpis_widget = self._create_kpis_section()
        content_layout.addWidget(kpis_widget)
        
        # Splitter para gráficos
        graphs_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Gráfico de pastel (Estados)
        if MATPLOTLIB_AVAILABLE:
            self.pie_chart_widget = self._create_pie_chart_widget()
            graphs_splitter.addWidget(self.pie_chart_widget)
            
            # Gráfico de líneas (Tendencias)
            self.line_chart_widget = self._create_line_chart_widget()
            graphs_splitter.addWidget(self.line_chart_widget)
        
        content_layout.addWidget(graphs_splitter)
        
        # Splitter inferior para tablas
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Top instituciones
        self.institutions_table = self._create_institutions_table()
        bottom_splitter.addWidget(self.institutions_table)
        
        # Métricas financieras
        self.financial_widget = self._create_financial_widget()
        bottom_splitter.addWidget(self.financial_widget)
        
        content_layout.addWidget(bottom_splitter)
        
        # Añadir scroll
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def _create_kpis_section(self) -> QWidget:
        """Crea la sección de KPIs superiores."""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)
        
        # Crear cards de KPI
        self.card_activas = self._create_kpi_card("Licitaciones Activas", "0", self.colors["info"], "📋")
        self.card_ganadas = self._create_kpi_card("Ganadas", "0", self.colors["success"], "🏆")
        self.card_perdidas = self._create_kpi_card("Perdidas", "0", self.colors["danger"], "❌")
        self.card_total = self._create_kpi_card("Total Procesos", "0", self.colors["accent"], "📊")
        
        layout.addWidget(self.card_activas)
        layout.addWidget(self.card_ganadas)
        layout.addWidget(self.card_perdidas)
        layout.addWidget(self.card_total)
        
        return widget
    
    def _create_kpi_card(self, title: str, value: str, color: str, icon: str) -> QFrame:
        """Crea una card de KPI con gradiente."""
        card = QFrame()
        
        # Crear gradiente de color
        # Convertir color hex a RGB para gradiente
        from PyQt6.QtGui import QColor
        qcolor = QColor(color)
        r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
        
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.colors['base']},
                    stop:1 rgba({r}, {g}, {b}, 30)
                );
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)
        card.setMinimumHeight(140)
        card.setMinimumWidth(200)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header con icono
        header = QHBoxLayout()
        header.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32pt;
                color: {color};
                background: transparent;
            }}
        """)
        icon_label.setFixedSize(50, 50)
        header.addWidget(icon_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text']};
                font-size: 10pt;
                font-weight: 600;
                background: transparent;
            }}
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 36pt;
                font-weight: bold;
                background: transparent;
            }}
        """)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        # Guardar referencia
        card._value_label = value_label
        
        return card
    
    def _resolve_theme_colors(self):
        """Obtiene colores del tema activo."""
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
        
        # ✅ CORRECCIÓN: Usar colores más claros para mejor contraste
        self.colors = {
            "accent": get_color(QPalette.ColorRole.Highlight, "#7C4DFF"),
            "text": get_color(QPalette.ColorRole.Text, "#E6E9EF"),
            "text_sec": get_color(QPalette.ColorRole.PlaceholderText, "#B9C0CC"),
            "window": get_color(QPalette.ColorRole.Window, "#1E1E1E"),
            "base": "#2D2D30",  # ✅ Forzar color más claro para las cards
            "alt": get_color(QPalette.ColorRole.AlternateBase, "#2D2D30"),
            "border": "#5E5E62",  # ✅ Borde más visible
            "success": "#00C853",
            "danger": "#FF5252",
            "warning": "#FFA726",
            "info": "#448AFF",
        }
        
        # ✅ DEBUG: Imprimir colores para verificar
        print("[DEBUG] Colores del dashboard:")
        for key, value in self.colors.items():
            print(f"  {key}: {value}")


    def _create_pie_chart_widget(self) -> QGroupBox:
        """Crea widget con gráfico de pastel."""
        box = QGroupBox("Distribución por Estado")
        box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.colors['base']};
                border: 1px solid {self.colors['border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                color: {self.colors['accent']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout(box)
        
        # Canvas matplotlib
        self.pie_canvas = FigureCanvas(Figure(figsize=(5, 4), facecolor=self.colors['base']))
        layout.addWidget(self.pie_canvas)
        
        return box
    
    def _create_line_chart_widget(self) -> QGroupBox:
        """Crea widget con gráfico de líneas."""
        box = QGroupBox("Tendencia de Licitaciones")
        box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.colors['base']};
                border: 1px solid {self.colors['border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                color: {self.colors['accent']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }}
        """)
        
        layout = QVBoxLayout(box)
        
        # Canvas matplotlib
        self.line_canvas = FigureCanvas(Figure(figsize=(6, 4), facecolor=self.colors['base']))
        layout.addWidget(self.line_canvas)
        
        return box
    
    def _create_institutions_table(self) -> QGroupBox:
        """Crea tabla de top instituciones."""
        box = QGroupBox("Top Instituciones (por cantidad)")
        box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.colors['base']};
                border: 1px solid {self.colors['border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout(box)
        
        self.table_institutions = QTableWidget(0, 2)
        self.table_institutions.setHorizontalHeaderLabels(["Institución", "Cantidad"])
        self.table_institutions.setAlternatingRowColors(True)
        self.table_institutions.verticalHeader().setVisible(False)
        self.table_institutions.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_institutions.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.table_institutions.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table_institutions.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {self.colors['border']};
                background-color: {self.colors['base']};
            }}
        """)
        
        layout.addWidget(self.table_institutions)
        
        return box
    
    def _create_financial_widget(self) -> QGroupBox:
        """Crea widget de métricas financieras."""
        box = QGroupBox("Métricas Financieras")
        box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {self.colors['base']};
                border: 1px solid {self.colors['border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout(box)
        
        # Grid con métricas
        grid = QGridLayout()
        grid.setSpacing(15)
        
        self.lbl_monto_base = self._create_metric_label("Monto Base Total:", "RD$ 0.00")
        self.lbl_monto_ofertado = self._create_metric_label("Monto Ofertado:", "RD$ 0.00")
        self.lbl_diferencia = self._create_metric_label("Diferencia:", "RD$ 0.00")
        self.lbl_tasa_exito = self._create_metric_label("Tasa de Éxito:", "0.0%")
        
        grid.addWidget(self.lbl_monto_base[0], 0, 0)
        grid.addWidget(self.lbl_monto_base[1], 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_monto_ofertado[0], 1, 0)
        grid.addWidget(self.lbl_monto_ofertado[1], 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_diferencia[0], 2, 0)
        grid.addWidget(self.lbl_diferencia[1], 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_tasa_exito[0], 3, 0)
        grid.addWidget(self.lbl_tasa_exito[1], 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return box
    
    def _create_metric_label(self, title: str, value: str) -> tuple:
        """Crea par de labels para métrica."""
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text_sec']};
                font-size: 10pt;
                font-weight: 600;
            }}
        """)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text']};
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        
        return (title_label, value_label)
    
    # ==================== DATOS ====================
    
    def refresh_stats(self):
        """Refresca todas las estadísticas del dashboard."""
        if not self.db:
            return
        
        try:
            # Cargar licitaciones
            self._licitaciones = self.db.load_all_licitaciones() or []
            
            # Calcular estadísticas
            self._calculate_stats()
            
            # Actualizar UI
            self._update_kpis()
            self._update_pie_chart()
            self._update_line_chart()
            self._update_institutions_table()
            self._update_financial_metrics()
            
        except Exception as e:
            print(f"[ERROR] Error refrescando dashboard: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_stats(self):
        """Calcula estadísticas de las licitaciones."""
        total = len(self._licitaciones)
        
        # Contar por estado
        activas = 0
        ganadas = 0
        perdidas = 0
        
        estados_count = Counter()
        instituciones_count = Counter()
        
        monto_base_total = 0.0
        monto_ofertado_total = 0.0
        
        # ✅ CORRECCIÓN: Definir estados finalizados explícitamente
        estados_finalizados = {
            'adjudicada', 'ganada', 'perdida', 'cancelada', 'desierta',
            'descalificado', 'descalificada', 'anulada', 'archivada',
            'desistida', 'rechazada', 'no adjudicada'
        }
        
        for lic in self._licitaciones:
            estado_raw = getattr(lic, 'estado', '') or ''
            estado = estado_raw.lower().strip()
            
            # Registrar estado en contador
            if estado:
                estados_count[estado] += 1
            
            # ✅ CORRECCIÓN: Contar activas (todo lo que NO esté finalizado)
            es_finalizada = False
            for estado_fin in estados_finalizados:
                if estado_fin in estado:
                    es_finalizada = True
                    break
            
            if not es_finalizada and estado:
                activas += 1
            
            # Contar ganadas
            if any(x in estado for x in ['ganada', 'adjudicada']):
                ganadas += 1
            
            # Contar perdidas
            if any(x in estado for x in ['perdida', 'descalificad', 'rechazad']):
                perdidas += 1
            
            # Instituciones
            inst = getattr(lic, 'institucion', '') or ''
            if inst:
                instituciones_count[inst] += 1
            
            # Montos
            try:
                if hasattr(lic, 'get_monto_base_total'):
                    base = lic.get_monto_base_total()
                    if base is not None:
                        monto_base_total += float(base)
                
                if hasattr(lic, 'get_oferta_total'):
                    oferta = lic.get_oferta_total()
                    if oferta is not None:
                        monto_ofertado_total += float(oferta)
            except Exception as e:
                print(f"[WARNING] Error calculando montos para {getattr(lic, 'numero_proceso', 'N/A')}: {e}")
        
        # Tasa de éxito
        tasa_exito = (ganadas / (ganadas + perdidas) * 100) if (ganadas + perdidas) > 0 else 0.0
        
        self._stats = {
            'total': total,
            'activas': activas,
            'ganadas': ganadas,
            'perdidas': perdidas,
            'estados': dict(estados_count),
            'instituciones': dict(instituciones_count.most_common(10)),
            'monto_base': monto_base_total,
            'monto_ofertado': monto_ofertado_total,
            'diferencia': monto_ofertado_total - monto_base_total,
            'tasa_exito': tasa_exito,
        }
        
        # ✅ DEBUG: Imprimir estadísticas calculadas
        print("\n" + "="*60)
        print("[DEBUG] Estadísticas del Dashboard:")
        print("="*60)
        print(f"Total licitaciones: {total}")
        print(f"Activas: {activas}")
        print(f"Ganadas: {ganadas}")
        print(f"Perdidas: {perdidas}")
        print(f"Estados únicos: {list(estados_count.keys())}")
        print("="*60 + "\n")
        
    def _update_kpis(self):
        """Actualiza las cards de KPI."""
        self.card_activas._value_label.setText(str(self._stats.get('activas', 0)))
        self.card_ganadas._value_label.setText(str(self._stats.get('ganadas', 0)))
        self.card_perdidas._value_label.setText(str(self._stats.get('perdidas', 0)))
        self.card_total._value_label.setText(str(self._stats.get('total', 0)))
    
    def _update_pie_chart(self):
        """Actualiza gráfico de pastel."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        estados = self._stats.get('estados', {})
        if not estados:
            return
        
        # Limpiar figura
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)
        
        # Configurar colores del tema
        ax.set_facecolor(self.colors['base'])
        
        # Datos
        labels = list(estados.keys())
        sizes = list(estados.values())
        
        # Colores
        colors_map = {
            'ganada': self.colors['success'],
            'perdida': self.colors['danger'],
            'activa': self.colors['info'],
            'proceso': self.colors['warning'],
        }
        
        pie_colors = []
        for label in labels:
            for key, color in colors_map.items():
                if key in label.lower():
                    pie_colors.append(color)
                    break
            else:
                pie_colors.append(self.colors['accent'])
        
        # Dibujar
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=pie_colors, textprops={'color': self.colors['text']})
        
        self.pie_canvas.figure.tight_layout()
        self.pie_canvas.draw()
    
    def _update_line_chart(self):
        """Actualiza gráfico de líneas con datos reales por mes (mejorado)."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        from collections import defaultdict
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        # Limpiar figura
        self.line_canvas.figure.clear()
        ax = self.line_canvas.figure.add_subplot(111)
        
        # Configurar tema
        ax.set_facecolor(self.colors['base'])
        ax.tick_params(colors=self.colors['text'], labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(self.colors['border'])
        
        # ✅ AGRUPAR LICITACIONES POR MES
        por_mes = defaultdict(int)
        fechas_encontradas = 0
        
        for lic in self._licitaciones:
            fecha = None
            
            # Intentar obtener fecha de apertura
            if hasattr(lic, 'fecha_apertura') and getattr(lic, 'fecha_apertura', None):
                fecha = getattr(lic, 'fecha_apertura')
            
            # Si no, buscar en cronograma
            elif hasattr(lic, 'cronograma') and getattr(lic, 'cronograma', None):
                cron = getattr(lic, 'cronograma', {})
                if isinstance(cron, dict):
                    # Buscar fecha de apertura en cronograma
                    for evento in ['Apertura de Ofertas', 'Apertura de Oferta Economica', 
                                'apertura_ofertas', 'apertura']:
                        if evento in cron:
                            fecha_data = cron[evento]
                            if isinstance(fecha_data, dict):
                                fecha_str = fecha_data.get('fecha_limite') or fecha_data.get('fecha')
                                if fecha_str:
                                    try:
                                        # Intentar varios formatos
                                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                                            try:
                                                fecha = datetime.strptime(str(fecha_str), fmt).date()
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        print(f"[WARNING] Error parseando fecha '{fecha_str}': {e}")
                            break
            
            # Si no, intentar fecha de creación
            if not fecha and hasattr(lic, 'fecha_creacion') and getattr(lic, 'fecha_creacion', None):
                fecha = getattr(lic, 'fecha_creacion')
            
            # Convertir a date si es datetime
            if fecha:
                if isinstance(fecha, datetime):
                    fecha = fecha.date()
                
                # Validar que sea un objeto date válido
                if hasattr(fecha, 'strftime'):
                    try:
                        mes_key = fecha.strftime('%Y-%m')
                        por_mes[mes_key] += 1
                        fechas_encontradas += 1
                    except Exception as e:
                        print(f"[WARNING] Error procesando fecha {fecha}: {e}")
        
        print(f"[INFO] Fechas encontradas: {fechas_encontradas} de {len(self._licitaciones)}")
        
        # ✅ SI NO HAY FECHAS, USAR DATOS DUMMY
        if fechas_encontradas == 0 or len(por_mes) == 0:
            print("[INFO] No se encontraron fechas válidas, usando datos de ejemplo")
            months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
            values = [5, 8, 12, 10, 15, len(self._licitaciones) or 1]
            
            ax.plot(months, values, marker='o', color=self.colors['accent'], 
                    linewidth=2.5, markersize=8)
            
            ax.set_xlabel('Mes (Datos de ejemplo)', color=self.colors['text'], fontsize=10)
            ax.set_ylabel('Licitaciones', color=self.colors['text'], fontsize=10)
            ax.set_title('Tendencia de Licitaciones', color=self.colors['accent'], 
                        fontsize=11, fontweight='bold', pad=10)
            ax.grid(True, alpha=0.15, color=self.colors['border'], linestyle='--')
            
            self.line_canvas.figure.tight_layout()
            self.line_canvas.draw()
            return
        
        # ✅ GENERAR RANGO DE ÚLTIMOS 12 MESES
        hoy = datetime.now().date()
        primer_mes = (hoy.replace(day=1) - relativedelta(months=11))  # 12 meses atrás
        
        # Crear lista de todos los meses en el rango
        meses_completos = []
        mes_actual = primer_mes
        
        for _ in range(12):
            mes_key = mes_actual.strftime('%Y-%m')
            meses_completos.append(mes_key)
            mes_actual = mes_actual + relativedelta(months=1)
        
        # ✅ LLENAR VALORES (0 si no hay datos para ese mes)
        months_labels = []
        values = []
        
        for mes_key in meses_completos:
            count = por_mes.get(mes_key, 0)
            values.append(count)
            
            # Formato de etiqueta
            try:
                fecha_obj = datetime.strptime(mes_key, '%Y-%m')
                # Mostrar "Ene 24" para meses de 2024, "Ene 25" para 2025
                label = fecha_obj.strftime('%b %y')
                months_labels.append(label)
            except:
                months_labels.append(mes_key)
        
        # ✅ DIBUJAR GRÁFICO
        line = ax.plot(range(len(months_labels)), values, 
                    marker='o', 
                    color=self.colors['accent'], 
                    linewidth=2.5, 
                    markersize=8,
                    markerfacecolor=self.colors['accent'],
                    markeredgecolor=self.colors['base'],
                    markeredgewidth=2,
                    label=f'Total: {sum(values)} licitaciones')[0]
        
        # Añadir área sombreada bajo la línea
        ax.fill_between(range(len(months_labels)), values, alpha=0.2, color=self.colors['accent'])
        
        # Añadir valores solo en puntos con datos
        for i, (month, value) in enumerate(zip(months_labels, values)):
            if value > 0:  # Solo mostrar si hay valor
                ax.annotate(str(value), 
                        xy=(i, value), 
                        xytext=(0, 8), 
                        textcoords='offset points',
                        ha='center',
                        fontsize=9,
                        color=self.colors['text'],
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', 
                                    facecolor=self.colors['base'], 
                                    edgecolor=self.colors['accent'], 
                                    alpha=0.8))
        
        # Configurar ejes X
        ax.set_xticks(range(len(months_labels)))
        ax.set_xticklabels(months_labels, rotation=45, ha='right', fontsize=9)
        
        # Configurar ejes Y
        ax.set_xlabel('Mes', color=self.colors['text'], fontsize=10, fontweight='600')
        ax.set_ylabel('Cantidad de Licitaciones', color=self.colors['text'], fontsize=10, fontweight='600')
        
        # Título con rango de fechas
        titulo = f'Tendencia de Licitaciones ({months_labels[0]} - {months_labels[-1]})'
        ax.set_title(titulo, color=self.colors['accent'], fontsize=11, fontweight='bold', pad=15)
        
        # Grid horizontal
        ax.grid(True, alpha=0.15, color=self.colors['border'], linestyle='--', linewidth=0.8, axis='y')
        
        # Leyenda
        ax.legend(loc='upper left', framealpha=0.9, facecolor=self.colors['base'], 
                edgecolor=self.colors['border'], fontsize=9)
        
        # Ajustar límites del eje Y
        max_val = max(values) if max(values) > 0 else 1
        ax.set_ylim(-0.5, max_val * 1.2)
        
        # Establecer límites del eje X
        ax.set_xlim(-0.5, len(months_labels) - 0.5)
        
        self.line_canvas.figure.tight_layout()
        self.line_canvas.draw()


    def _update_institutions_table(self):
        """Actualiza tabla de instituciones."""
        instituciones = self._stats.get('instituciones', {})
        
        self.table_institutions.setRowCount(0)
        
        for inst, count in instituciones.items():
            row = self.table_institutions.rowCount()
            self.table_institutions.insertRow(row)
            self.table_institutions.setItem(row, 0, QTableWidgetItem(inst))
            self.table_institutions.setItem(row, 1, QTableWidgetItem(str(count)))
    
    def _update_financial_metrics(self):
        """Actualiza métricas financieras."""
        monto_base = self._stats.get('monto_base', 0.0)
        monto_ofertado = self._stats.get('monto_ofertado', 0.0)
        diferencia = self._stats.get('diferencia', 0.0)
        tasa_exito = self._stats.get('tasa_exito', 0.0)
        
        self.lbl_monto_base[1].setText(f"RD$ {monto_base:,.2f}")
        self.lbl_monto_ofertado[1].setText(f"RD$ {monto_ofertado:,.2f}")
        self.lbl_diferencia[1].setText(f"RD$ {diferencia:,.2f}")
        self.lbl_diferencia[1].setStyleSheet(f"""
            QLabel {{
                color: {self.colors['success'] if diferencia < 0 else self.colors['danger']};
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        self.lbl_tasa_exito[1].setText(f"{tasa_exito:.1f}%")