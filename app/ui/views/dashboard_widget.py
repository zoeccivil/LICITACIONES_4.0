from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, MAXYEAR
from collections import Counter, defaultdict

from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox, QLineEdit,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QSplitter, QMenu, QSizePolicy, QGridLayout, QTreeWidget, QTreeWidgetItem
)

# Persistencia JSON para splitters y tabs
from app.core.app_settings import (
    get_splitter_sizes, set_splitter_sizes,
    get_tab_index, set_tab_index,
)

# Matplotlib opcional
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib as mpl
    from matplotlib import cm as mpl_cm
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None
    mpl = None
    mpl_cm = None

from app.core.db_adapter import DatabaseAdapter
    #
from app.core.models import Licitacion, Documento


class DashboardWidget(QWidget):
    """
    Dashboard analítico para el tema Titanium Construct.
    """

    # Señal para abrir detalles de licitación por ID (la usa MainWindow)
    edit_licitacion_requested = pyqtSignal(int)

    # --- Columnas de Tablas ---
    # Resumen por Empresa
    COL_RE_EMP = 0
    COL_RE_PART = 1
    COL_RE_GAN = 2
    COL_RE_MONTO = 3

    # Competidores
    COL_COMP_NOM = 0
    COL_COMP_RNC = 1
    COL_COMP_PART = 2
    COL_COMP_PCT = 3

    # Fallas: impacto
    COL_FDOC_NOM = 0
    COL_FDOC_CNT = 1
    COL_FDOC_PCT = 2

    # Fallas: detalle
    COL_FDET_EMP = 0
    COL_FDET_RNC = 1
    COL_FDET_INST = 2
    COL_FDET_TIPO = 3

    # Paleta Titanium Construct (modo claro)
    COLOR_BACKGROUND = "#F3F4F6"        # Neutral-100 (fondo general)
    COLOR_TEXT_PRIMARY = "#111827"      # Neutral-900
    COLOR_TEXT_SECONDARY = "#6B7280"    # Neutral-500

    COLOR_PARTICIPACIONES = "#155E75"   # Primary-500
    COLOR_GANADAS = "#16A34A"           # Verde éxito
    COLOR_PERDIDAS = "#DC2626"          # Rojo error
    COLOR_EN_PROCESO = "#F59E0B"        # Ámbar

    COLOR_BORDER = "#D1D5DB"            # Neutral-300
    COLOR_ALT = "#E5E7EB"               # Neutral-200 (fondos suaves)
    COLOR_BASE = "#FFFFFF"              # Blanco (tarjetas/tablas)

    def __init__(self, db: DatabaseAdapter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db = db

        # Ajustar QSS base para cajas/tarjetas
        self._resolve_theme_colors()

        # Estado datasets
        self._all_licitaciones: List[Licitacion] = []
        self._filtered: List[Licitacion] = []
        self._fallas_dataset: List[Tuple] = []
        self._competidores_maestros: List[Dict[str, Any]] = []
        self._empresas_maestras: List[Dict[str, Any]] = []

        # Estilo MPL (usa colores del tema)
        self._init_mpl_style()

        # UI raíz
        root = QVBoxLayout(self)
        self._build_filters_bar(root)

        # Tabs
        self.tabs = QTabWidget()
        self._style_tabs(self.tabs)
        root.addWidget(self.tabs, 1)

        # Resumen
        self.tab_resumen = QWidget()
        self.v_resumen_layout = QVBoxLayout(self.tab_resumen)
        self._build_resumen_tab()
        self.tabs.addTab(self.tab_resumen, "📊 Resumen General")

        # Competencia
        self.tab_comp = QWidget()
        self.v_comp_layout = QVBoxLayout(self.tab_comp)
        self._build_competencia_tab()
        self.tabs.addTab(self.tab_comp, "🤺 Competencia")

        # Fallas
        self.tab_fallas = QWidget()
        self.v_fallas_layout = QVBoxLayout(self.tab_fallas)
        self._build_fallas_tab()
        self.tabs.addTab(self.tab_fallas, "🔍 Fallas Fase A")

        # Atajos
        QShortcut(QKeySequence("F5"), self, activated=self.reload_data)

        # Cargar datos
        self.reload_data()

        # Restaurar splitters y tab desde JSON
        self._restore_layout_state_json()

        # Guardar cambios al vuelo
        self.tabs.currentChanged.connect(self._on_tabs_changed)
        if hasattr(self, "split_v"):
            self.split_v.splitterMoved.connect(lambda p, i: self._save_splitter_sizes("split_v", self.split_v))
        if hasattr(self, "split_fallas"):
            self.split_fallas.splitterMoved.connect(lambda p, i: self._save_splitter_sizes("split_fallas", self.split_fallas))
        if hasattr(self, "split_h"):
            self.split_h.splitterMoved.connect(lambda p, i: self._save_splitter_sizes("split_h", self.split_h))

    # ----------------- Tema / Colores -----------------
    def _resolve_theme_colors(self):
        """
        Aplica paleta Titanium Construct en modo OSCURO para consistencia
        con el resto de la aplicación moderna.
        """
        # ✅ Colores adaptados al tema oscuro moderno
        self.COLOR_BACKGROUND = "#1E1E1E"       # Fondo general oscuro
        self.COLOR_TEXT_PRIMARY = "#E6E9EF"     # Texto claro principal
        self.COLOR_TEXT_SECONDARY = "#B9C0CC"   # Texto claro secundario

        self.COLOR_PARTICIPACIONES = "#7C4DFF"  # Morado accent (igual que app moderna)
        self.COLOR_GANADAS = "#00C853"          # Verde éxito
        self.COLOR_PERDIDAS = "#FF5252"         # Rojo error
        self.COLOR_EN_PROCESO = "#FFA726"       # Ámbar/naranja

        self.COLOR_BORDER = "#3E3E42"           # Bordes sutiles
        self.COLOR_ALT = "#2D2D30"              # Fondos alternos
        self.COLOR_BASE = "#252526"             # Fondo de cards/tablas

        # ✅ QSS actualizado para modo oscuro
        self._BOX_QSS = (
            "QGroupBox {"
            f"  background-color: {self.COLOR_BASE};"
            f"  border: 1px solid {self.COLOR_BORDER};"
            "  border-radius: 8px;"
            "  margin-top: 1.2em;"
            "  padding: 15px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 8px;"
            f"  color: {self.COLOR_PARTICIPACIONES};"
            "  font-weight: bold;"
            "  font-size: 11pt;"
            "}"
        )
    def _get_input_style(self) -> str:
        """Devuelve QSS para inputs consistente con el tema oscuro."""
        return f"""
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {self.COLOR_ALT};
                border: 2px solid {self.COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {self.COLOR_TEXT_PRIMARY};
                font-size: 10pt;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {self.COLOR_PARTICIPACIONES};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.COLOR_TEXT_PRIMARY};
                margin-right: 5px;
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """
    def _tight_layout_safe(self, fig=None):
        """
        Ajusta el layout de manera segura para evitar excepciones de Matplotlib.
        """
        try:
            if fig is None:
                if hasattr(self, "canvas_rend") and self.canvas_rend:
                    fig = self.canvas_rend.figure
                elif hasattr(self, "canvas_estados") and self.canvas_estados:
                    fig = self.canvas_estados.figure
                elif hasattr(self, "canvas_fallas") and self.canvas_fallas:
                    fig = self.canvas_fallas.figure
            if fig is not None:
                fig.tight_layout()
        except Exception:
            pass

    def _style_tabs(self, tabs: QTabWidget):
        """Aplica estilo moderno oscuro a los tabs."""
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.COLOR_BORDER};
                background: {self.COLOR_BASE};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background: {self.COLOR_ALT};
                color: {self.COLOR_TEXT_SECONDARY};
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {self.COLOR_BASE};
                color: {self.COLOR_PARTICIPACIONES};
                font-weight: bold;
                border-top: 3px solid {self.COLOR_PARTICIPACIONES};
            }}
            QTabBar::tab:hover:!selected {{
                background: {self.COLOR_BORDER};
            }}
        """)

    # ----------------- Matplotlib -----------------
    def _init_mpl_style(self):
        """Configura estilos globales para Matplotlib en modo oscuro."""
        if MATPLOTLIB_AVAILABLE and mpl is not None:
            try:
                mpl.rcParams["font.size"] = 9
                mpl.rcParams["axes.titlepad"] = 12
                mpl.rcParams["axes.labelcolor"] = self.COLOR_TEXT_PRIMARY  # ✅ Cambiado
                mpl.rcParams["axes.titleweight"] = "bold"
                mpl.rcParams["axes.titlesize"] = "11"
                mpl.rcParams["xtick.color"] = self.COLOR_TEXT_PRIMARY       # ✅ Cambiado
                mpl.rcParams["ytick.color"] = self.COLOR_TEXT_PRIMARY       # ✅ Cambiado
                mpl.rcParams["figure.facecolor"] = self.COLOR_BASE
                mpl.rcParams["axes.facecolor"] = self.COLOR_BASE
                mpl.rcParams["savefig.facecolor"] = self.COLOR_BASE
                mpl.rcParams["text.color"] = self.COLOR_TEXT_PRIMARY        # ✅ Añadido
                mpl.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans", "sans-serif"]
                mpl.rcParams["font.family"] = "sans-serif"
            except Exception as e:
                print(f"No se pudo configurar Matplotlib: {e}")

    # ----------------- Barra de filtros -----------------
    def _build_filters_bar(self, parent_layout: QVBoxLayout):
        """Construye la barra de filtros con tema oscuro moderno."""
        box = QGroupBox("Filtros del Dashboard")
        box.setStyleSheet(self._BOX_QSS)
        h = QHBoxLayout(box)
        h.setSpacing(10)

        # ==================== LABELS ====================
        # Estilo para labels
        label_style = f"""
            QLabel {{
                color: {self.COLOR_TEXT_PRIMARY};
                font-size: 10pt;
                font-weight: 600;
            }}
        """

        lbl_inst = QLabel("Institución:")
        lbl_inst.setStyleSheet(label_style)
        h.addWidget(lbl_inst)

        # ==================== COMBO INSTITUCIÓN ====================
        self.cmb_inst = QComboBox()
        self.cmb_inst.setMinimumWidth(220)
        self.cmb_inst.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        h.addWidget(self.cmb_inst, 1)

        lbl_codigo = QLabel("Código Proceso:")
        lbl_codigo.setStyleSheet(label_style)
        h.addWidget(lbl_codigo)

        # ==================== INPUT CÓDIGO ====================
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("ITLA-CCC-CP-2025-0001…")
        self.txt_codigo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        h.addWidget(self.txt_codigo, 1)

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet(label_style)
        h.addWidget(lbl_desde)

        # ==================== DATE DESDE ====================
        self.dt_desde = QDateEdit()
        self.dt_desde.setDisplayFormat("yyyy-MM-dd")
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDate(QDate.currentDate())
        h.addWidget(self.dt_desde)

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet(label_style)
        h.addWidget(lbl_hasta)

        # ==================== DATE HASTA ====================
        self.dt_hasta = QDateEdit()
        self.dt_hasta.setDisplayFormat("yyyy-MM-dd")
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDate(QDate.currentDate())
        h.addWidget(self.dt_hasta)

        # ==================== APLICAR ESTILOS A INPUTS ====================
        input_style = f"""
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {self.COLOR_ALT};
                border: 2px solid {self.COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {self.COLOR_TEXT_PRIMARY};
                font-size: 10pt;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {self.COLOR_PARTICIPACIONES};
            }}
            QLineEdit::placeholder {{
                color: {self.COLOR_TEXT_SECONDARY};
            }}
            QComboBox::drop-down, QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow, QDateEdit::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.COLOR_TEXT_PRIMARY};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.COLOR_BASE};
                color: {self.COLOR_TEXT_PRIMARY};
                selection-background-color: {self.COLOR_PARTICIPACIONES};
                selection-color: white;
                border: 1px solid {self.COLOR_BORDER};
            }}
        """

        self.cmb_inst.setStyleSheet(input_style)
        self.txt_codigo.setStyleSheet(input_style)
        self.dt_desde.setStyleSheet(input_style)
        self.dt_hasta.setStyleSheet(input_style)

        # ==================== BOTONES ====================
        # Estilo para botón primario (Aplicar)
        btn_primary_style = f"""
            QPushButton {{
                background-color: {self.COLOR_PARTICIPACIONES};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #6C3FEF;
            }}
            QPushButton:pressed {{
                background-color: #5C2FDF;
            }}
        """

        # Estilo para botones neutrales (Limpiar, Refrescar)
        btn_neutral_style = f"""
            QPushButton {{
                background-color: {self.COLOR_ALT};
                color: {self.COLOR_TEXT_PRIMARY};
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.COLOR_BORDER};
                border-color: {self.COLOR_PARTICIPACIONES};
            }}
            QPushButton:pressed {{
                background-color: {self.COLOR_BASE};
            }}
        """

        # Botón Aplicar
        self.btn_aplicar = QPushButton("Aplicar")
        self.btn_aplicar.clicked.connect(self._apply_filters_and_render)
        self.btn_aplicar.setStyleSheet(btn_primary_style)
        h.addWidget(self.btn_aplicar)

        # Botón Limpiar
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.clicked.connect(self._clear_filters)
        self.btn_limpiar.setStyleSheet(btn_neutral_style)
        h.addWidget(self.btn_limpiar)

        # Botón Refrescar Datos
        self.btn_refrescar = QPushButton("Refrescar Datos")
        self.btn_refrescar.clicked.connect(self.reload_data)
        self.btn_refrescar.setStyleSheet(btn_neutral_style)
        h.addWidget(self.btn_refrescar)

        parent_layout.addWidget(box)

    # ----------------- Helper para KPIs -----------------
    def _create_kpi_widget(self, label: str, value_object_name: str, money: bool = False) -> QWidget:
        """Crea un widget de KPI estandarizado (Etiqueta + Valor) con estilo Titanium."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(2)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(
            f"font-size:10px; color:{self.COLOR_TEXT_SECONDARY}; font-weight:bold;"
        )
        lbl_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        lbl_value = QLabel("...")
        lbl_value.setObjectName(value_object_name)

        # Colores según semántica
        color = self.COLOR_TEXT_PRIMARY
        if label in ("Ganadas", "Lotes Ganados", "Monto Adjudicado (Nosotros)"):
            color = self.COLOR_GANADAS
        elif label in ("Perdidas",):
            color = self.COLOR_PERDIDAS
        elif label == "Tasa de Éxito":
            color = self.COLOR_PARTICIPACIONES

        size = "22px" if label == "Tasa de Éxito" else ("18px" if not money else "14px")
        lbl_value.setStyleSheet(f"font-size:{size}; color:{color}; font-weight:bold;")
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        v.addWidget(lbl_value)
        v.addWidget(lbl_label)
        return w

    # ----------------- Pestaña Resumen -----------------
    def _build_kpi_bar(self, parent_layout: QVBoxLayout):
        """Construye el panel superior de KPIs y Financieros."""
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        # KPIs Generales
        box_kpis = QGroupBox("Indicadores Clave")
        box_kpis.setStyleSheet(self._BOX_QSS)
        grid_kpis = QGridLayout(box_kpis)
        grid_kpis.setSpacing(10)

        self.w_kpi_tasa = self._create_kpi_widget("Tasa de Éxito", "lbl_kpi_tasa")
        self.w_kpi_ganadas = self._create_kpi_widget("Ganadas", "lbl_kpi_ganadas")
        self.w_kpi_perdidas = self._create_kpi_widget("Perdidas", "lbl_kpi_perdidas")
        self.w_kpi_lotes_ganados = self._create_kpi_widget("Lotes Ganados", "lbl_kpi_lotes_ganados")
        self.w_kpi_lotes_total = self._create_kpi_widget("Lotes Adjudicados", "lbl_kpi_lotes_total")

        grid_kpis.addWidget(self.w_kpi_tasa, 0, 0, 2, 1)
        grid_kpis.addWidget(self.w_kpi_ganadas, 0, 1)
        grid_kpis.addWidget(self.w_kpi_perdidas, 1, 1)
        grid_kpis.addWidget(self.w_kpi_lotes_ganados, 0, 2)
        grid_kpis.addWidget(self.w_kpi_lotes_total, 1, 2)
        grid_kpis.setColumnStretch(0, 1)

        # KPIs Financieros
        box_fin = QGroupBox("Análisis Financiero")
        box_fin.setStyleSheet(self._BOX_QSS)
        grid_fin = QGridLayout(box_fin)

        self.w_fin_base = self._create_kpi_widget("Monto Base Total", "lbl_fin_base", money=True)
        self.w_fin_ofertado = self._create_kpi_widget("Monto Ofertado Total", "lbl_fin_ofertado", money=True)
        self.w_fin_adjudicado = self._create_kpi_widget("Monto Adjudicado (Nosotros)", "lbl_fin_adjudicado", money=True)

        grid_fin.addWidget(self.w_fin_base, 0, 0)
        grid_fin.addWidget(self.w_fin_ofertado, 0, 1)
        grid_fin.addWidget(self.w_fin_adjudicado, 0, 2)

        kpi_row.addWidget(box_kpis, 2)
        kpi_row.addWidget(box_fin, 3)
        parent_layout.addLayout(kpi_row)

    def _build_resumen_tab(self):
        """Construye la pestaña 'Resumen General' con KPIs y splitters."""
        # 1. Panel superior de KPIs
        self._build_kpi_bar(self.v_resumen_layout)

        # 2. Splitter principal (Horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.v_resumen_layout.addWidget(main_splitter, 1)

        # 3. Panel Izquierdo (Vertical Splitter para Gráficos)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        if MATPLOTLIB_AVAILABLE:
            self.canvas_rend = self._new_canvas()
            self.canvas_estados = self._new_canvas()

            left_splitter.addWidget(self._wrap_canvas("Rendimiento por Empresa", self.canvas_rend))
            left_splitter.addWidget(self._wrap_canvas("Distribución de Estados", self.canvas_estados))
            left_splitter.setSizes([300, 200])
        else:
            left_splitter.addWidget(QLabel("Matplotlib no está disponible. No se pueden mostrar gráficos."))

        # 4. Panel Derecho (Tabla Resumen por Empresa)
        right_pane = QGroupBox("Resumen por Empresa")
        right_pane.setStyleSheet(self._BOX_QSS)
        right_layout = QVBoxLayout(right_pane)

        self.tbl_resumen_empresa = QTableWidget(0, 4)
        self.tbl_resumen_empresa.setHorizontalHeaderLabels(["Empresa", "Participa", "Ganadas", "Monto Adjudicado"])
        self._style_table(self.tbl_resumen_empresa)

        right_layout.addWidget(self.tbl_resumen_empresa)

        # 5. Ensamblar Splitter Principal
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_pane)
        main_splitter.setSizes([600, 400])

        # Guardar referencias para persistencia
        self.split_h = main_splitter
        self.split_v = left_splitter

    # ----------------- Pestaña Competencia -----------------
    def _build_competencia_tab(self):
        top = QHBoxLayout()
        top.addWidget(QLabel("🔍 Buscar (Nombre o RNC):"))
        self.txt_comp_search = QLineEdit()
        self.txt_comp_search.textChanged.connect(self._filter_competidores_table)
        top.addWidget(self.txt_comp_search, 1)
        self.v_comp_layout.addLayout(top)

        self.tbl_comp = QTableWidget(0, 4)
        self.tbl_comp.setHorizontalHeaderLabels(["Nombre", "RNC", "# Lotes Ofertados", "% Dif. Promedio"])
        self._style_table(self.tbl_comp)
        self.v_comp_layout.addWidget(self.tbl_comp, 1)

    # ----------------- Pestaña Fallas Fase A -----------------
    def _build_fallas_tab(self):
        self.split_fallas = QSplitter(Qt.Orientation.Horizontal)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("Institución:"))
        self.cmb_fallas_inst = QComboBox()
        self.cmb_fallas_inst.currentIndexChanged.connect(self._render_fallas_tab)
        filt.addWidget(self.cmb_fallas_inst, 1)
        self.v_fallas_layout.addLayout(filt)

        self.v_fallas_layout.addWidget(self.split_fallas, 1)

        left = QSplitter(Qt.Orientation.Vertical)
        self.split_fallas.addWidget(left)

        box_impacto = QGroupBox("Análisis de Impacto por Documento")
        box_impacto.setStyleSheet(self._BOX_QSS)
        vb1 = QVBoxLayout(box_impacto)
        self.tbl_fdoc = QTableWidget(0, 3)
        self.tbl_fdoc.setHorizontalHeaderLabels(["Documento", "N° Fallas", "% del Total"])
        self._style_table(self.tbl_fdoc)
        self.tbl_fdoc.itemSelectionChanged.connect(self._render_fallas_detalle)
        vb1.addWidget(self.tbl_fdoc, 1)
        left.addWidget(box_impacto)

        box_det = QGroupBox("Detalle de Fallas por Empresa (Seleccione un documento)")
        box_det.setStyleSheet(self._BOX_QSS)
        vb2 = QVBoxLayout(box_det)

        actions = QHBoxLayout()
        self.btn_fdel = QPushButton("🗑 Eliminar seleccionadas")
        self.btn_fedit = QPushButton("✏️ Editar comentario…")
        # Botones secundarios, estilo neutro (deja que el tema global mande)
        actions.addWidget(self.btn_fdel)
        actions.addWidget(self.btn_fedit)
        actions.addStretch(1)
        vb2.addLayout(actions)

        self.tbl_fdet = QTableWidget(0, 4)
        self.tbl_fdet.setHorizontalHeaderLabels(["Empresa", "RNC", "Institución", "Tipo"])
        self._style_table(self.tbl_fdet)
        vb2.addWidget(self.tbl_fdet, 1)
        left.addWidget(box_det)

        if MATPLOTLIB_AVAILABLE:
            self.canvas_fallas = self._new_canvas()
            self.split_fallas.addWidget(self._wrap_canvas("Top 10 Documentos con Más Fallas", self.canvas_fallas))
        else:
            lbl = QLabel("Matplotlib no está disponible.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.split_fallas.addWidget(lbl)

        self.split_fallas.setSizes([700, 600])

    # ----------------- Helpers de estilo -----------------
    def _style_table(self, t: QTableWidget):
        """Aplica estilo moderno oscuro a tablas."""
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        t.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {self.COLOR_BORDER};
                background-color: {self.COLOR_BASE};
                alternate-background-color: {self.COLOR_ALT};
                selection-background-color: {self.COLOR_PARTICIPACIONES};
                selection-color: white;
                border: none;
                color: {self.COLOR_TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {self.COLOR_ALT};
                color: {self.COLOR_TEXT_PRIMARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {self.COLOR_PARTICIPACIONES};
                font-weight: bold;
                font-size: 10pt;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {self.COLOR_TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: {self.COLOR_PARTICIPACIONES};
                color: white;
            }}
        """)

    def _style_tree(self, tree: QTreeWidget):
        tree.setAlternatingRowColors(True)
        tree.setStyleSheet(
            "QTreeView {"
            f"  gridline-color: {self.COLOR_BORDER};"
            "}"
        )

    # ----------------- Helpers gráficos -----------------
    def _new_canvas(self):
        fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=self.COLOR_BASE)
        return FigureCanvas(fig)

    def _wrap_canvas(self, title: str, canvas):
        box = QGroupBox(title)
        box.setStyleSheet(self._BOX_QSS)
        v = QVBoxLayout(box)
        v.setContentsMargins(4, 4, 4, 4)
        v.addWidget(canvas, 1)
        return box

    def _clean_ax(self, ax):
        """Limpia los ejes para un look moderno oscuro."""
        ax.set_facecolor(self.COLOR_BASE)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.COLOR_BORDER)
        ax.spines["bottom"].set_color(self.COLOR_BORDER)
        ax.grid(axis="both", color=self.COLOR_BORDER, linestyle="--", alpha=0.3)  # ✅ Mejorado
        ax.set_axisbelow(True)
        ax.tick_params(colors=self.COLOR_TEXT_PRIMARY)  # ✅ Añadido

    # ----------------- Persistencia JSON -----------------
    def _restore_layout_state_json(self):
        idx = get_tab_index("DashboardGlobal", "main", 0)
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)
        for key, ref in (
            ("split_v", getattr(self, "split_v", None)),
            ("split_h", getattr(self, "split_h", None)),
            ("split_fallas", getattr(self, "split_fallas", None)),
        ):
            if ref:
                sizes = get_splitter_sizes("DashboardGlobal", key)
                if sizes and len(sizes) == len(ref.sizes()) and all(isinstance(s, int) and s > 0 for s in sizes):
                    ref.setSizes(sizes)

    def _on_tabs_changed(self, idx: int):
        try:
            set_tab_index("DashboardGlobal", "main", int(idx))
        except Exception:
            pass

    def _save_splitter_sizes(self, key: str, splitter: QSplitter):
        try:
            set_splitter_sizes("DashboardGlobal", key, splitter.sizes())
        except Exception:
            pass

    # ----------------- Datos -----------------
    def reload_data(self):
        """Carga datos desde la BD y repuebla UI respetando filtros actuales."""
        try:
            self._all_licitaciones = self.db.load_all_licitaciones() or []
        except Exception as e:
            self._all_licitaciones = []
            QMessageBox.warning(self, "Datos", f"No se pudieron cargar licitaciones:\n{e}")

        if self._all_licitaciones:
            try:
                min_d = min(
                    (getattr(lic, "fecha_creacion", date(MAXYEAR, 12, 31)) or date(MAXYEAR, 12, 31))
                    for lic in self._all_licitaciones
                )
                self._min_date = min_d if isinstance(min_d, date) and min_d.year != MAXYEAR else date.today()
            except Exception:
                self._min_date = date.today()
        else:
            self._min_date = date.today()

        try:
            self._competidores_maestros = self.db.get_competidores_maestros() or []
        except Exception:
            self._competidores_maestros = []

        try:
            self._empresas_maestras = self.db.get_empresas_maestras() or []
        except Exception:
            self._empresas_maestras = []

        insts = sorted({getattr(b, "institucion", "") or "" for b in self._all_licitaciones if getattr(b, "institucion", "")})
        self.cmb_inst.blockSignals(True)
        self.cmb_inst.clear()
        self.cmb_inst.addItem("Todas")
        self.cmb_inst.addItems(insts)
        self.cmb_inst.blockSignals(False)

        try:
            self._fallas_dataset = self.db.obtener_todas_las_fallas() or []
        except Exception:
            self._fallas_dataset = []

        finsts = sorted(list({row[0] for row in self._fallas_dataset})) if self._fallas_dataset else []
        self.cmb_fallas_inst.blockSignals(True)
        self.cmb_fallas_inst.clear()
        self.cmb_fallas_inst.addItem("Todas")
        self.cmb_fallas_inst.addItems(finsts)
        self.cmb_fallas_inst.blockSignals(False)

        self._clear_filters()
        self._apply_filters_and_render()

    def _apply_filters_and_render(self):
        inst = self.cmb_inst.currentText().strip()
        code = (self.txt_codigo.text() or "").strip().lower()
        d_from: Optional[date] = self.dt_desde.date().toPyDate() if self.dt_desde.date().isValid() and self.dt_desde.text() else None
        d_to: Optional[date] = self.dt_hasta.date().toPyDate() if self.dt_hasta.date().isValid() and self.dt_hasta.text() else None

        lst = self._all_licitaciones[:]
        if inst and inst != "Todas":
            lst = [b for b in lst if (getattr(b, "institucion", "") or "") == inst]
        if code:
            lst = [b for b in lst if code in (getattr(b, "numero_proceso", "") or "").lower()]

        if d_from:
            lst = [b for b in lst if (getattr(b, "fecha_creacion", date(1900, 1, 1)) or date(1900, 1, 1)) >= d_from]
        if d_to:
            lst = [b for b in lst if (getattr(b, "fecha_creacion", date(9999, 12, 31)) or date(9999, 12, 31)) <= d_to]

        self._filtered = lst

        self._render_kpis_and_summaries()
        self._render_resumen_graphs()
        self._render_competencia_tab()
        self._render_fallas_tab()

    def _clear_filters(self):
        self.cmb_inst.setCurrentIndex(0)
        self.txt_codigo.clear()
        self.dt_desde.setDate(self._min_date)
        self.dt_hasta.clear()
        if self.sender() == self.btn_limpiar:
            self._apply_filters_and_render()

    # ----------------- Pestaña Resumen: Lógica de Renderizado -----------------
    def _render_kpis_and_summaries(self):
        """Calcula KPIs y puebla Resumen por Empresa y KPIs financieros."""
        # ---- KPIs de estado ----
        ganadas, perdidas = self._count_win_lose(self._filtered)
        total_finalizadas = ganadas + perdidas
        tasa_exito = (ganadas / total_finalizadas * 100.0) if total_finalizadas > 0 else 0.0

        # ---- KPIs financieros ----
        lotes_ganados_total = 0
        lotes_adjudicados_total = 0
        monto_base_total = 0.0
        monto_ofertado_total = 0.0
        monto_adjudicado_nosotros_total_general = 0.0

        stats_emp = defaultdict(lambda: {"participaciones": 0, "ganadas": 0, "monto_adjudicado": 0.0})

        # set global de nombres de nuestras empresas maestras (sin normalizar, para fallback)
        nuestras_empresas_nombres_crudos = {
            (e.get("nombre", "") or "").strip() for e in (self._empresas_maestras or [])
        }

        for lic in self._filtered:
            empresas_participantes_en_lic = self._our_names_from(lic)
            lic_tiene_nuestras = bool(empresas_participantes_en_lic)

            es_ganada_por_nosotros_lic = False
            monto_adjudicado_esta_lic_para_nosotros = 0.0
            lic_estado_str = getattr(lic, "estado", "")

            # Lotes adjudicados/ganados (a nivel de lote, como en ReportWindow)
            if lic_estado_str == "Adjudicada":
                lotes_adjudicados_total += len(getattr(lic, "lotes", []))
                for lote in getattr(lic, "lotes", []):
                    if self._is_lote_ganado_por_nosotros(lic, lote):
                        lotes_ganados_total += 1
                        es_ganada_por_nosotros_lic = True
                        monto_lote_ganado = float(getattr(lote, "monto_ofertado", 0) or 0.0)
                        monto_adjudicado_esta_lic_para_nosotros += monto_lote_ganado

            # TOTALES FINANCIEROS
            got_any_method_value = False
            try:
                v = float(lic.get_monto_base_total(solo_participados=True) or 0)
                monto_base_total += v
                got_any_method_value = got_any_method_value or (v > 0)
            except Exception:
                pass
            try:
                v = float(lic.get_oferta_total(solo_participados=True) or 0)
                monto_ofertado_total += v
                got_any_method_value = got_any_method_value or (v > 0)
            except Exception:
                pass

            if not got_any_method_value:
                for lote in getattr(lic, "lotes", []) or []:
                    participa = getattr(lote, "participamos", None)
                    if participa is None:
                        emp = (getattr(lote, "empresa_nuestra", "") or "").strip()
                        participa = bool(emp and emp in nuestras_empresas_nombres_crudos) or lic_tiene_nuestras

                    if participa:
                        base = getattr(lote, "monto_base_personal", None)
                        if base in (None, 0):
                            base = getattr(lote, "monto_base", 0)
                        monto_base_total += float(base or 0.0)
                        monto_ofertado_total += float(getattr(lote, "monto_ofertado", 0) or 0.0)

            monto_adjudicado_nosotros_total_general += monto_adjudicado_esta_lic_para_nosotros

            for nombre_empresa in empresas_participantes_en_lic:
                stats_emp[nombre_empresa]["participaciones"] += 1
                if es_ganada_por_nosotros_lic:
                    stats_emp[nombre_empresa]["ganadas"] += 1
                    if empresas_participantes_en_lic:
                        stats_emp[nombre_empresa]["monto_adjudicado"] += (
                            monto_adjudicado_esta_lic_para_nosotros / len(empresas_participantes_en_lic)
                        )

        self._stats_emp = stats_emp

        # ---- Pintar KPIs ----
        lbl = self.findChild(QLabel, "lbl_kpi_tasa")
        if lbl:
            lbl.setText(f"{tasa_exito:.1f}%")
        lbl = self.findChild(QLabel, "lbl_kpi_ganadas")
        if lbl:
            lbl.setText(f"{ganadas}")
        lbl = self.findChild(QLabel, "lbl_kpi_perdidas")
        if lbl:
            lbl.setText(f"{perdidas}")
        lbl = self.findChild(QLabel, "lbl_kpi_lotes_ganados")
        if lbl:
            lbl.setText(f"{lotes_ganados_total}")
        lbl = self.findChild(QLabel, "lbl_kpi_lotes_total")
        if lbl:
            lbl.setText(f"{lotes_adjudicados_total}")

        lbl = self.findChild(QLabel, "lbl_fin_base")
        if lbl:
            lbl.setText(f"RD$ {monto_base_total:,.2f}")
        lbl = self.findChild(QLabel, "lbl_fin_ofertado")
        if lbl:
            lbl.setText(f"RD$ {monto_ofertado_total:,.2f}")
        lbl = self.findChild(QLabel, "lbl_fin_adjudicado")
        if lbl:
            lbl.setText(f"RD$ {monto_adjudicado_nosotros_total_general:,.2f}")

        # ---- Tabla Resumen por Empresa ----
        t = self.tbl_resumen_empresa
        t.setRowCount(0)
        sorted_stats = sorted(
            stats_emp.items(),
            key=lambda item: (-item[1]["participaciones"], -item[1]["ganadas"])
        )
        for nombre, data in sorted_stats:
            row = t.rowCount()
            t.insertRow(row)

            item_emp = QTableWidgetItem(nombre)
            item_part = QTableWidgetItem(str(data["participaciones"]))
            item_part.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_gan = QTableWidgetItem(str(data["ganadas"]))
            item_gan.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_monto = QTableWidgetItem(f"RD$ {data['monto_adjudicado']:,.2f}")
            item_monto.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            t.setItem(row, self.COL_RE_EMP, item_emp)
            t.setItem(row, self.COL_RE_PART, item_part)
            t.setItem(row, self.COL_RE_GAN, item_gan)
            t.setItem(row, self.COL_RE_MONTO, item_monto)

        t.resizeColumnsToContents()
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(self.COL_RE_EMP, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(self.COL_RE_MONTO, QHeaderView.ResizeMode.ResizeToContents)

    def _render_resumen_graphs(self):
        """Renderiza los gráficos de Matplotlib para la pestaña Resumen."""
        if not MATPLOTLIB_AVAILABLE:
            return

        # 1. Rendimiento por empresa
        ax_rend = self.canvas_rend.figure.subplots()
        ax_rend.clear()
        self._clean_ax(ax_rend)

        stats_emp = getattr(self, "_stats_emp", {})
        if stats_emp:
            # Mismo orden que la tabla: participaciones desc, luego ganadas desc
            data = sorted(
                stats_emp.items(),
                key=lambda it: (-it[1]["participaciones"], -it[1]["ganadas"])
            )

            # Si quieres limitar a top N, descomenta:
            # N_TOP = 15
            # data = data[:N_TOP]

            # Invertimos para que la empresa con más participaciones quede arriba
            labels = [k for k, _ in data][::-1]
            y = list(range(len(labels)))
            part = [d["participaciones"] for _, d in data][::-1]
            wins = [d["ganadas"] for _, d in data][::-1]
            height = 0.4

            ax_rend.barh(
                [yy + height / 2 for yy in y],
                part,
                height=height,
                color=self.COLOR_PARTICIPACIONES,
                label="Participaciones",
            )
            ax_rend.barh(
                [yy - height / 2 for yy in y],
                wins,
                height=height,
                color=self.COLOR_GANADAS,
                label="Ganadas",
            )

            ax_rend.set_yticks(y, labels, fontsize=8, color=self.COLOR_TEXT_PRIMARY)
            ax_rend.set_xlabel("Cantidad de Licitaciones", color=self.COLOR_TEXT_SECONDARY)

            for i, (p, w) in enumerate(zip(part, wins)):
                if p > 0:
                    ax_rend.text(
                        p,
                        i + height / 2,
                        f" {p}",
                        va="center",
                        ha="left",
                        color=self.COLOR_PARTICIPACIONES,
                        fontsize=7,
                        weight="bold",
                    )
                if w > 0:
                    ax_rend.text(
                        w,
                        i - height / 2,
                        f" {w}",
                        va="center",
                        ha="left",
                        color=self.COLOR_GANADAS,
                        fontsize=7,
                        weight="bold",
                    )

            if part:
                ax_rend.set_xlim(right=max(part) * 1.15)

            ax_rend.legend(loc="lower right", frameon=False, labelcolor=self.COLOR_TEXT_PRIMARY)
        else:
            ax_rend.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=self.COLOR_TEXT_SECONDARY)
            ax_rend.set_yticks([])

        self._tight_layout_safe(self.canvas_rend.figure)
        self.canvas_rend.draw_idle()

        # 2. Distribución de estados (lo dejamos igual)
        ax_est = self.canvas_estados.figure.subplots()
        ax_est.clear()
        self._clean_ax(ax_est)

        stats = {"Ganada": 0, "Perdida": 0, "En Proceso": 0}
        for lic in self._filtered:
            if not self._our_names_from(lic):
                continue
            estado = getattr(lic, "estado", "")
            if estado == "Adjudicada":
                if any(self._is_lote_ganado_por_nosotros(lic, l) for l in getattr(lic, "lotes", [])):
                    stats["Ganada"] += 1
                else:
                    stats["Perdida"] += 1
            elif estado in ["Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"]:
                stats["Perdida"] += 1
            elif estado not in ["", None, "Borrador"]:
                stats["En Proceso"] += 1

        labels_raw = [k for k, v in stats.items() if v > 0]
        values = [stats[k] for k in labels_raw]

        if values:
            labels_display = [f"{k} ({v})" for k, v in zip(labels_raw, values)]
            colors = [
                self.COLOR_GANADAS if k == "Ganada"
                else self.COLOR_PERDIDAS if k == "Perdida"
                else self.COLOR_EN_PROCESO
                for k in labels_raw
            ]

            bars = ax_est.barh(labels_display, values, color=colors)
            ax_est.bar_label(bars, padding=3, color=self.COLOR_TEXT_PRIMARY, weight="bold")
            ax_est.set_xlabel("Cantidad de Licitaciones", color=self.COLOR_TEXT_SECONDARY)
            ax_est.invert_yaxis()
            if values:
                ax_est.set_xlim(right=max(values) * 1.15)
        else:
            ax_est.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=self.COLOR_TEXT_SECONDARY)
            ax_est.set_yticks([])

        self._tight_layout_safe(self.canvas_estados.figure)
        self.canvas_estados.draw_idle()

    # ----------------- Pestaña Competencia -----------------
    def _render_competencia_tab(self):
        data = self._analizar_competidores_pct(self._filtered)
        self._comp_all = data
        self._filter_competidores_table()

    def _filter_competidores_table(self):
        term = (self.txt_comp_search.text() or "").strip().lower()
        data = self._comp_all if hasattr(self, "_comp_all") else []
        if term:
            data = [c for c in data if term in (c.get("nombre", "").lower()) or term in (c.get("rnc", "").lower())]
        t = self.tbl_comp
        t.setRowCount(0)
        for c in data:
            row = t.rowCount()
            t.insertRow(row)
            vals = (
                c.get("nombre", "") or "",
                c.get("rnc", "") or "",
                str(c.get("participaciones", 0)),
                f"{c.get('pct_promedio', 0.0):.2f}%",
            )
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                t.setItem(row, col, item)
            t.item(row, self.COL_COMP_PART).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            t.item(row, self.COL_COMP_PCT).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(self.COL_COMP_NOM, QHeaderView.ResizeMode.Stretch)

    def _analizar_competidores_pct(self, bids: List[Licitacion]) -> List[Dict[str, Any]]:
        stats: Dict[str, Dict[str, float]] = {}
        base_by_lote: Dict[str, float] = {}
        rnc_map = {c.get("nombre", ""): c.get("rnc", "") for c in (self._competidores_maestros or [])}
        nuestras_empresas_nombres = {e.get("nombre", "").strip() for e in self._empresas_maestras}

        for lic in bids:
            base_by_lote.clear()
            for lote in getattr(lic, "lotes", []):
                base = getattr(lote, "monto_base_personal", 0) or getattr(lote, "monto_base", 0) or 0
                base_by_lote[str(getattr(lote, "numero", ""))] = float(base) if base else 0.0

            for comp in getattr(lic, "oferentes_participantes", []):
                nombre = getattr(comp, "nombre", "").strip() or "—"
                if nombre in nuestras_empresas_nombres:
                    continue
                for o in getattr(comp, "ofertas_por_lote", []):
                    lote_num = str(o.get("lote_numero"))
                    oferta = float(o.get("monto", 0) or 0)
                    base = float(base_by_lote.get(lote_num, 0) or 0)
                    if base > 0 and oferta > 0:
                        pct = (oferta - base) / base * 100.0
                        if nombre not in stats:
                            stats[nombre] = {"sum_pct": 0.0, "count": 0}
                        stats[nombre]["sum_pct"] += pct
                        stats[nombre]["count"] += 1

        salida: List[Dict[str, Any]] = []
        for nombre, agg in stats.items():
            count = agg["count"] or 0
            pct_prom = (agg["sum_pct"] / count) if count else 0.0
            salida.append(
                {
                    "nombre": nombre,
                    "rnc": rnc_map.get(nombre, ""),
                    "participaciones": count,
                    "pct_promedio": pct_prom,
                }
            )
        salida.sort(key=lambda x: (-x["participaciones"], x["pct_promedio"]))
        return salida

    # ----------------- Pestaña Fallas -----------------
    def _render_fallas_tab(self):
        inst = self.cmb_fallas_inst.currentText() if self.cmb_fallas_inst.count() else "Todas"
        if inst == "Todas":
            datos = self._fallas_dataset
        else:
            datos = [f for f in self._fallas_dataset if f[0] == inst]

        counter = Counter(item[2] for item in datos)  # doc_nombre
        total = len(datos)
        self.tbl_fdoc.setRowCount(0)
        for doc, cnt in sorted(counter.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total * 100.0) if total > 0 else 0.0
            row = self.tbl_fdoc.rowCount()
            self.tbl_fdoc.insertRow(row)
            self.tbl_fdoc.setItem(row, self.COL_FDOC_NOM, QTableWidgetItem(doc))
            self.tbl_fdoc.setItem(row, self.COL_FDOC_CNT, QTableWidgetItem(str(cnt)))
            self.tbl_fdoc.setItem(row, self.COL_FDOC_PCT, QTableWidgetItem(f"{pct:.1f}%"))

            self.tbl_fdoc.item(row, self.COL_FDOC_CNT).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_fdoc.item(row, self.COL_FDOC_PCT).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        if MATPLOTLIB_AVAILABLE:
            ax_fallas = self.canvas_fallas.figure.subplots()
            ax_fallas.clear()
            self._clean_ax(ax_fallas)
            top_items = counter.most_common(10)
            if not top_items:
                ax_fallas.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=self.COLOR_TEXT_SECONDARY)
            else:
                labels = [it[0] for it in top_items][::-1]
                counts = [it[1] for it in top_items][::-1]
                if mpl_cm is not None:
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "accent_fade",
                        [self.COLOR_PARTICIPACIONES + "55", self.COLOR_PARTICIPACIONES],
                    )
                    colors = [cmap(i / max(1, len(counts) - 1)) for i in range(len(counts))]
                else:
                    colors = [self.COLOR_PARTICIPACIONES] * len(counts)

                bars = ax_fallas.barh(labels, counts, color=colors)
                ax_fallas.bar_label(bars, padding=3, fontsize=8, color=self.COLOR_TEXT_PRIMARY, fmt="%d")
                ax_fallas.set_xlabel("Cantidad de Fallas Registradas", color=self.COLOR_TEXT_SECONDARY)
                if counts:
                    ax_fallas.set_xlim(right=max(counts) * 1.15)
            self._tight_layout_safe(self.canvas_fallas.figure)
            self.canvas_fallas.draw_idle()

        self.tbl_fdet.setRowCount(0)

    def _render_fallas_detalle(self):
        self.tbl_fdet.setRowCount(0)
        r = self.tbl_fdoc.currentRow()
        if r < 0:
            return
        doc_sel = self.tbl_fdoc.item(r, self.COL_FDOC_NOM).text()
        inst = self.cmb_fallas_inst.currentText()
        datos = self._fallas_dataset or []
        if inst != "Todas":
            datos = [f for f in datos if f[0] == inst]

        rnc_map = {e.get("nombre", ""): e.get("rnc", "N/D") for e in (self._empresas_maestras or [])}
        rnc_map.update({c.get("nombre", ""): c.get("rnc", "N/D") for c in (self._competidores_maestros or [])})

        for insti, participante, doc_nombre, es_nuestro, *_ in datos:
            if doc_nombre == doc_sel and (inst == "Todas" or insti == inst):
                tipo = "Nuestra" if es_nuestro else "Competidor"
                rnc = rnc_map.get(participante, "N/D")
                row = self.tbl_fdet.rowCount()
                self.tbl_fdet.insertRow(row)
                self.tbl_fdet.setItem(row, self.COL_FDET_EMP, QTableWidgetItem(participante))
                self.tbl_fdet.setItem(row, self.COL_FDET_RNC, QTableWidgetItem(rnc))
                self.tbl_fdet.setItem(row, self.COL_FDET_INST, QTableWidgetItem(insti))
                self.tbl_fdet.setItem(row, self.COL_FDET_TIPO, QTableWidgetItem(tipo))

    def _delete_fallas_selected(self):
        rows = sorted({idx.row() for idx in self.tbl_fdet.selectionModel().selectedRows()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Eliminar fallas", "Seleccione una o más filas del detalle.")
            return
        r = self.tbl_fdoc.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Eliminar", "Seleccione primero un documento en la tabla superior.")
            return
        doc_sel = self.tbl_fdoc.item(r, self.COL_FDOC_NOM).text()
        if QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar {len(rows)} falla(s) del documento '{doc_sel}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return

        eliminadas = 0
        errores = 0
        for rr in rows:
            empresa = self.tbl_fdet.item(rr, self.COL_FDET_EMP).text()
            inst = self.tbl_fdet.item(rr, self.COL_FDET_INST).text()
            try:
                eliminadas += int(self.db.eliminar_falla_por_campos(inst, empresa, doc_sel) or 0)
            except Exception:
                errores += 1

        try:
            self._fallas_dataset = self.db.obtener_todas_las_fallas() or []
        except Exception:
            pass
        self._render_fallas_tab()

        items = self.tbl_fdoc.findItems(doc_sel, Qt.MatchFlag.MatchExactly)
        if items:
            self.tbl_fdoc.setCurrentItem(items[0])
            self._render_fallas_detalle()

        if errores:
            QMessageBox.warning(self, "Eliminar", f"Se eliminaron {eliminadas} con {errores} error(es).")
        else:
            QMessageBox.information(self, "Eliminar", f"Se eliminaron {eliminadas} fallas.")

    def _edit_fallas_comment(self):
        rows = sorted({idx.row() for idx in self.tbl_fdet.selectionModel().selectedRows()})
        if not rows:
            QMessageBox.information(self, "Editar comentario", "Seleccione una o más filas del detalle.")
            return
        r = self.tbl_fdoc.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Editar", "Seleccione primero un documento en la tabla superior.")
            return
        doc_sel = self.tbl_fdoc.item(r, self.COL_FDOC_NOM).text()

        from PyQt6.QtWidgets import QInputDialog
        texto, ok = QInputDialog.getText(self, "Editar comentario", f"Nuevo comentario para {len(rows)} falla(s):")
        if not ok or not (texto or "").strip():
            return
        comentario = texto.strip()

        errores = 0
        for rr in rows:
            empresa = self.tbl_fdet.item(rr, self.COL_FDET_EMP).text()
            inst = self.tbl_fdet.item(rr, self.COL_FDET_INST).text()
            try:
                self.db.actualizar_comentario_falla(inst, empresa, doc_sel, comentario)
            except Exception:
                errores += 1

        try:
            self._fallas_dataset = self.db.obtener_todas_las_fallas() or []
        except Exception:
            pass
        self._render_fallas_tab()
        items = self.tbl_fdoc.findItems(doc_sel, Qt.MatchFlag.MatchExactly)
        if items:
            self.tbl_fdoc.setCurrentItem(items[0])
            self._render_fallas_detalle()

        if errores:
            QMessageBox.warning(self, "Editar comentario", f"Actualizado con {errores} error(es).")
        else:
            QMessageBox.information(self, "Editar comentario", "Comentario actualizado.")

    # ----------------- Utilidades -----------------
    def _our_names_from(self, lic: Licitacion) -> List[str]:
        """
        Obtiene los nombres de nuestras empresas que participan en una licitación.
        Usa normalización de nombres y combina:
        - empresas maestras
        - empresas_nuestras declaradas en la propia licitación
        - oferentes_participantes
        - empresa_nuestra en lotes
        """
        names: set[str] = set()

        # 1. Base: empresas maestras (normalizadas)
        maestras_norm = {
            self._norm(e.get("nombre", ""))
            for e in (self._empresas_maestras or [])
            if e.get("nombre")
        }

        # 2. Ampliar maestras con empresas_nuestras definidas en la licitación
        for item in getattr(lic, "empresas_nuestras", []) or []:
            n = ""
            if hasattr(item, "nombre"):
                n = getattr(item, "nombre") or ""
            elif isinstance(item, dict) and item.get("nombre"):
                n = item["nombre"] or ""
            elif isinstance(item, str):
                n = item
            n_norm = self._norm(n)
            if n_norm:
                maestras_norm.add(n_norm)

        # 3. Buscar en oferentes_participantes
        for oferente in getattr(lic, "oferentes_participantes", []):
            nombre_raw = getattr(oferente, "nombre", "") or ""
            nombre_norm = self._norm(nombre_raw)
            if nombre_norm in maestras_norm:
                names.add(nombre_raw.strip())

        # 4. Buscar en empresa_nuestra de los lotes
        if not names:
            for lote in getattr(lic, "lotes", []) or []:
                n_raw = getattr(lote, "empresa_nuestra", None) or ""
                n_norm = self._norm(n_raw)
                if n_norm in maestras_norm:
                    names.add(n_raw.strip())

        # 5. Como último recurso, tomar empresas_nuestras de la licitación
        if not names:
            for item in getattr(lic, "empresas_nuestras", []) or []:
                n = ""
                if hasattr(item, "nombre"):
                    n = getattr(item, "nombre") or ""
                elif isinstance(item, dict) and item.get("nombre"):
                    n = item["nombre"] or ""
                elif isinstance(item, str):
                    n = item
                n_norm = self._norm(n)
                if not maestras_norm or n_norm in maestras_norm:
                    if n.strip():
                        names.add(n.strip())

        return sorted(names)

    def _is_lote_ganado_por_nosotros(self, lic: Licitacion, lote) -> bool:
        """
        Devuelve True si el lote fue ganado por alguna de nuestras empresas.
        Usa tanto:
        - ganador_nombre del lote (fuente principal, como en ReportWindow)
        - flag ganado_por_nosotros (como apoyo)
        """
        # Si ya viene marcado explícitamente, respétalo
        if getattr(lote, "ganado_por_nosotros", False):
            return True

        ganador_real = (getattr(lote, "ganador_nombre", "") or "").strip()
        if not ganador_real:
            return False

        ganador_norm = self._norm(ganador_real)

        # Nombres de nuestras empresas que participan en esta licitación
        nuestras_en_lic = {self._norm(n) for n in self._our_names_from(lic)}

        return bool(ganador_norm in nuestras_en_lic)
    
    # ----------------- Normalización de nombres -----------------
    def _norm(self, s: str) -> str:
        """
        Normaliza nombres de empresas/participantes para compararlos de forma robusta,
        similar a _populate_competidores del ReportWindow.
        """
        s = (s or "").strip()
        s = s.replace("➡️", "").replace("(Nuestra Oferta)", "")
        while "  " in s:
            s = s.replace("  ", " ")
        return s.upper()



    def _count_win_lose(self, arr: List[Licitacion]) -> Tuple[int, int]:
        """
        Cuenta licitaciones ganadas/perdidas solo de aquellas en las que participamos.
        Una licitación se considera 'ganada' si tiene al menos un lote
        adjudicado a nuestras empresas, usando la misma lógica que el reporte.
        """
        gan, per = 0, 0
        perdidas_directas = {"Descalificado Fase A", "Descalificado Fase B", "Desierta", "Cancelada"}

        for lic in arr:
            # Solo considerar licitaciones donde tenemos al menos una empresa participante
            if not self._our_names_from(lic):
                continue

            estado = getattr(lic, "estado", "")

            if estado == "Adjudicada":
                # Ganada si algún lote lo ganamos nosotros
                if any(self._is_lote_ganado_por_nosotros(lic, l) for l in getattr(lic, "lotes", [])):
                    gan += 1
                else:
                    per += 1
            elif estado in perdidas_directas:
                per += 1

        return gan, per
    
    def get_global_kpis_summary(self) -> dict:
        """
        Devuelve un diccionario con KPIs agregados usando la misma lógica interna
        (ganadas, perdidas, lotes ganados, lotes adjudicados, montos, etc.).
        Usa self._filtered como conjunto de licitaciones activo.
        """
        ganadas, perdidas = self._count_win_lose(self._filtered)
        total_finalizadas = ganadas + perdidas
        tasa_exito = (ganadas / total_finalizadas * 100.0) if total_finalizadas > 0 else 0.0

        lotes_ganados_total = 0
        lotes_adjudicados_total = 0
        monto_base_total = 0.0
        monto_ofertado_total = 0.0
        monto_adjudicado_nosotros_total_general = 0.0

        nuestras_empresas_nombres_crudos = {
            (e.get("nombre", "") or "").strip() for e in (self._empresas_maestras or [])
        }

        for lic in self._filtered:
            empresas_participantes_en_lic = self._our_names_from(lic)
            lic_tiene_nuestras = bool(empresas_participantes_en_lic)

            es_ganada_por_nosotros_lic = False
            monto_adjudicado_esta_lic_para_nosotros = 0.0
            lic_estado_str = getattr(lic, "estado", "")

            if lic_estado_str == "Adjudicada":
                lotes_adjudicados_total += len(getattr(lic, "lotes", []))
                for lote in getattr(lic, "lotes", []):
                    if self._is_lote_ganado_por_nosotros(lic, lote):
                        lotes_ganados_total += 1
                        es_ganada_por_nosotros_lic = True
                        monto_lote_ganado = float(getattr(lote, "monto_ofertado", 0) or 0.0)
                        monto_adjudicado_esta_lic_para_nosotros += monto_lote_ganado

            got_any_method_value = False
            try:
                v = float(lic.get_monto_base_total(solo_participados=True) or 0)
                monto_base_total += v
                got_any_method_value = got_any_method_value or (v > 0)
            except Exception:
                pass
            try:
                v = float(lic.get_oferta_total(solo_participados=True) or 0)
                monto_ofertado_total += v
                got_any_method_value = got_any_method_value or (v > 0)
            except Exception:
                pass

            if not got_any_method_value:
                for lote in getattr(lic, "lotes", []) or []:
                    participa = getattr(lote, "participamos", None)
                    if participa is None:
                        emp = (getattr(lote, "empresa_nuestra", "") or "").strip()
                        participa = bool(emp and emp in nuestras_empresas_nombres_crudos) or lic_tiene_nuestras

                    if participa:
                        base = getattr(lote, "monto_base_personal", None)
                        if base in (None, 0):
                            base = getattr(lote, "monto_base", 0)
                        monto_base_total += float(base or 0.0)
                        monto_ofertado_total += float(getattr(lote, "monto_ofertado", 0) or 0.0)

            monto_adjudicado_nosotros_total_general += monto_adjudicado_esta_lic_para_nosotros

        return {
            "ganadas": ganadas,
            "perdidas": perdidas,
            "tasa_exito": tasa_exito,
            "lotes_ganados": lotes_ganados_total,
            "lotes_adjudicados": lotes_adjudicados_total,
            "monto_base_total": monto_base_total,
            "monto_ofertado_total": monto_ofertado_total,
            "monto_adjudicado_nosotros": monto_adjudicado_nosotros_total_general,
            "total_licitaciones_filtradas": len(self._filtered),
        }