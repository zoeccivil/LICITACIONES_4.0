from __future__ import annotations
from typing import Optional
from datetime import date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QGuiApplication, QPalette, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QProgressBar,
    QSplitter, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox, QToolBar, QFrame, QStyle
)

# Gráficos (opcional)
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None

# ReportGenerator (rutas tolerantes)
REPORT_GENERATOR_AVAILABLE = False
REPORT_GENERATOR_IMPORT_ERROR = ""
try:
    from app.core.reporting import ReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except Exception as e1:
    REPORT_GENERATOR_IMPORT_ERROR = str(e1)
    try:
        from app.core.reporting.report_generator import ReportGenerator
        REPORT_GENERATOR_AVAILABLE = True
        REPORT_GENERATOR_IMPORT_ERROR = ""
    except Exception as e2:
        REPORT_GENERATOR_IMPORT_ERROR = f"{e1} | {e2}"
        ReportGenerator = None  # type: ignore

# Persistencia JSON para splitters y tabs
from app.core.app_settings import (
    get_splitter_sizes, set_splitter_sizes,
    get_tab_index, set_tab_index,
)

# Dependencias de exportación (mensajes amigables)
try:
    import reportlab  # noqa
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False
try:
    import openpyxl  # noqa
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False


def _hex(c: QColor) -> str:
    """Convierte QColor a string hexadecimal."""
    return c.name() if isinstance(c, QColor) else str(c)


class ReportWindow(QMainWindow):
    """
    Reporte de Licitación, adaptado dinámicamente al tema activo.
    Usa QPalette para obtener colores del tema en lugar de hardcoded.
    """

    def __init__(self, licitacion, parent: Optional[QWidget] = None, start_maximized: bool = False):
        super().__init__(parent)
        self.licitacion = licitacion

        # ✅ CORRECCIÓN: Obtener colores del tema activo
        self.ui = self._resolve_theme_colors()

        self._setup_palette()
        self._build_ui()

        self.setWindowTitle(f"Reporte: {getattr(self.licitacion, 'nombre_proceso', '')}")
        self.resize(1100, 850)
        if start_maximized:
            self.showMaximized()

        # Poblar datos
        self._populate_kpis()
        self._populate_cronograma()
        self._populate_financiero()
        self._populate_checklist()
        self._populate_competidores()

        # Restaurar splitters/tabs desde JSON
        self._restore_splitters_and_tabs_json()

        # Conectar splitters para guardar en caliente
        self.split_mid.splitterMoved.connect(self._on_split_mid_moved)
        self.split_bottom.splitterMoved.connect(self._on_split_bottom_moved)
        self.main_vsplitter.splitterMoved.connect(self._on_main_vsplitter_moved)

    # ---------- Tema / Colores ----------
    def _resolve_theme_colors(self) -> dict:
        """
        ✅ CORRECCIÓN: Usa QPalette para obtener colores del tema activo
        en lugar de hardcodear valores.
        """
        app = QGuiApplication.instance()
        pal: QPalette = app.palette() if app else QPalette()

        def get_color(role: QPalette.ColorRole, fallback: str) -> str:
            """Obtiene color de la paleta o usa fallback."""
            try:
                color = pal.color(role)
                if color.isValid():
                    return _hex(color)
            except Exception:
                pass
            return fallback

        # Obtener colores del tema activo
        accent = get_color(QPalette.ColorRole.Highlight, "#7C4DFF")
        text = get_color(QPalette.ColorRole.Text, "#E6E9EF")
        text_sec = get_color(QPalette.ColorRole.PlaceholderText, "#B9C0CC")
        window = get_color(QPalette.ColorRole.Window, "#1E1E1E")
        base = get_color(QPalette.ColorRole.Base, "#252526")
        alt = get_color(QPalette.ColorRole.AlternateBase, "#2D2D30")
        button = get_color(QPalette.ColorRole.Button, "#3E3E42")
        border = get_color(QPalette.ColorRole.Mid, "#3A4152")

        # Colores semánticos (fijos pero adaptables)
        success = "#00C853"
        danger = "#FF5252"
        warning = "#FFA726"
        info = accent

        return {
            "accent": accent,
            "accent_soft": f"{accent}26",  # ~15% alpha
            "text": text,
            "text_sec": text_sec,
            "window": window,
            "base": base,
            "alt": alt,
            "button": button,
            "border": border,
            "success": success,
            "danger": danger,
            "warning": warning,
            "info": info,
        }

    def _setup_palette(self):
        """
        ✅ CORRECCIÓN: QSS mínimo que respeta el tema global.
        No sobrescribe colores, solo ajusta espaciados y bordes.
        """
        u = self.ui
        self.setStyleSheet(
            "QMainWindow {"
            f"  background: {u['window']};"
            "}"
            "QWidget {"
            "  font-family: 'Segoe UI', 'DejaVu Sans', Arial;"
            "  font-size: 10pt;"
            "}"
            "QToolBar {"
            f"  background: {u['window']};"
            f"  border-bottom: 1px solid {u['border']};"
            "  spacing: 5px;"
            "  padding: 5px;"
            "}"
            "QStatusBar {"
            f"  background: {u['window']};"
            f"  color: {u['text_sec']};"
            "}"
            "QTabWidget::pane {"
            f"  border: 1px solid {u['border']};"
            f"  background: {u['base']};"
            "  border-radius: 6px;"
            "}"
            "QTabBar::tab {"
            f"  background: {u['alt']};"
            f"  color: {u['text_sec']};"
            "  padding: 8px 16px;"
            "  border-top-left-radius: 6px;"
            "  border-top-right-radius: 6px;"
            "  margin-right: 2px;"
            "  font-weight: 600;"
            "}"
            "QTabBar::tab:selected {"
            f"  background: {u['base']};"
            f"  color: {u['accent']};"
            "  font-weight: bold;"
            f"  border-bottom: 2px solid {u['accent']};"
            "}"
            "QTabBar::tab:hover:!selected {"
            f"  background: {u['button']};"
            "}"
        )

    def _card_stylesheet(self) -> str:
        """Estilo de tarjetas/groupbox adaptado al tema."""
        u = self.ui
        return (
            "QGroupBox, QFrame {"
            f"  background-color: {u['base']};"
            f"  border: 1px solid {u['border']};"
            "  border-radius: 8px;"
            "  padding: 12px;"
            "  margin-top: 0.5em;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 8px;"
            f"  color: {u['accent']};"
            "  font-weight: bold;"
            "  font-size: 11pt;"
            "}"
        )

    # ---------- UI ----------
    def _build_toolbar(self):
        tb = QToolBar("Exportar", self)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        self.act_pdf = QAction(
            self._icon(QStyle.StandardPixmap.SP_FileIcon, "report"),
            "Exportar a PDF",
            self
        )
        self.act_pdf.setShortcut(QKeySequence("Ctrl+P"))
        self.act_pdf.triggered.connect(lambda: self._export_report("pdf"))
        self.act_pdf.setEnabled(True)

        self.act_xls = QAction(
            self._icon(QStyle.StandardPixmap.SP_DialogSaveButton, "docs"),
            "Exportar a Excel",
            self
        )
        self.act_xls.setShortcut(QKeySequence("Ctrl+E"))
        self.act_xls.triggered.connect(lambda: self._export_report("excel"))
        self.act_xls.setEnabled(True)

        tb.addAction(self.act_pdf)
        tb.addAction(self.act_xls)

    def _build_ui(self):
        self._build_toolbar()

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # ==================== KPIs SUPERIORES (FIJOS) ====================
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        root.addLayout(kpi_row)

        self.card_estado = self._kpi_card("Estado Actual", self.ui["accent"])
        self.card_docs = self._kpi_card("Progreso Docs", self.ui["accent"], with_progress=True)
        self.card_dias = self._kpi_card("Días Restantes", self.ui["warning"])
        self.card_dif = self._kpi_card("Diferencia Oferta", self.ui["danger"])

        for c in (self.card_estado, self.card_docs, self.card_dias, self.card_dif):
            kpi_row.addWidget(c)

        # ==================== SPLITTER VERTICAL PRINCIPAL ====================
        # Divide la ventana en dos áreas verticales: Superior (Cronograma+Financiero) e Inferior (Tabs)
        self.main_vsplitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(self.main_vsplitter, 1)

        # ==================== ÁREA SUPERIOR: CRONOGRAMA + FINANCIERO ====================
        # Splitter horizontal para Cronograma | Financiero
        self.split_mid = QSplitter(Qt.Orientation.Horizontal)
        self.main_vsplitter.addWidget(self.split_mid)

        # --- CRONOGRAMA ---
        self.box_crono = QGroupBox("Cronograma")
        self.box_crono.setStyleSheet(self._card_stylesheet())
        v_crono = QVBoxLayout(self.box_crono)
        v_crono.setContentsMargins(8, 8, 8, 8)
        
        self.tbl_crono = QTableWidget(0, 3)
        self.tbl_crono.setAlternatingRowColors(True)
        self.tbl_crono.setHorizontalHeaderLabels(["Hito", "Fecha Límite", "Estado"])
        self._tune_table(self.tbl_crono)
        self._tune_cronograma_header()
        
        v_crono.addWidget(self.tbl_crono)
        self.split_mid.addWidget(self.box_crono)

        # --- FINANCIERO ---
        self.box_fin = QGroupBox("Resumen Financiero (Solo Lotes Participados)")
        self.box_fin.setStyleSheet(self._card_stylesheet())
        v_fin = QVBoxLayout(self.box_fin)
        v_fin.setContentsMargins(8, 8, 8, 8)

        # Grid con datos financieros
        self.grid_fin = QGridLayout()
        self.grid_fin.setVerticalSpacing(6)
        self.grid_fin.setHorizontalSpacing(12)
        v_fin.addLayout(self.grid_fin)

        # Gráfico matplotlib
        if MATPLOTLIB_AVAILABLE:
            self.canvas_fin = self._new_canvas()
            canvas_wrapper = self._wrap_canvas("Comparativo Oferta vs Base (participados)", self.canvas_fin)
            v_fin.addWidget(canvas_wrapper, 1)
        
        self.split_mid.addWidget(self.box_fin)

        # Proporción inicial del splitter horizontal (Cronograma:Financiero)
        self.split_mid.setStretchFactor(0, 2)  # Cronograma
        self.split_mid.setStretchFactor(1, 3)  # Financiero (más espacio para gráfico)

        # ==================== ÁREA INFERIOR: TABS (CHECKLIST + COMPETIDORES) ====================
        # Splitter horizontal para los dos tabs
        self.split_bottom = QSplitter(Qt.Orientation.Horizontal)
        self.main_vsplitter.addWidget(self.split_bottom)

        # --- TAB 1: CHECKLIST ---
        self.box_checklist = QGroupBox("Checklist de Documentos")
        self.box_checklist.setStyleSheet(self._card_stylesheet())
        v_chk = QVBoxLayout(self.box_checklist)
        v_chk.setContentsMargins(8, 8, 8, 8)
        
        self.tbl_docs = QTableWidget(0, 4)
        self.tbl_docs.setHorizontalHeaderLabels(["✓", "Documento", "Categoría", "Condición"])
        self._tune_table(self.tbl_docs)
        self.tbl_docs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_docs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        v_chk.addWidget(self.tbl_docs)
        self.split_bottom.addWidget(self.box_checklist)

        # --- TAB 2: COMPETIDORES ---
        self.box_competidores = QGroupBox("Competidores y Resultados")
        self.box_competidores.setStyleSheet(self._card_stylesheet())
        v_comp = QVBoxLayout(self.box_competidores)
        v_comp.setContentsMargins(8, 8, 8, 8)
        
        self.tree_comp = QTreeWidget()
        self.tree_comp.setColumnCount(7)
        self.tree_comp.setHeaderLabels([
            "Participante / Lote Ofertado",
            "Monto Ofertado",
            "Monto Habilitado (Fase A)",
            "Estado Fase A",
            "Monto Base Lote",
            "% Diferencia",
            "Ganador",
        ])
        self.tree_comp.setAlternatingRowColors(True)
        
        v_comp.addWidget(self.tree_comp)
        self.split_bottom.addWidget(self.box_competidores)

        # Proporción inicial del splitter horizontal inferior (Checklist:Competidores)
        self.split_bottom.setStretchFactor(0, 1)
        self.split_bottom.setStretchFactor(1, 1)

        # Proporción inicial del splitter vertical principal
        # (Superior:Inferior) - Damos más espacio al área inferior (tabs)
        self.main_vsplitter.setStretchFactor(0, 2)  # Área superior (Cronograma+Financiero)
        self.main_vsplitter.setStretchFactor(1, 3)  # Área inferior (Checklist+Competidores)

    # ---------- Persistencia splitters/tabs ----------
    def _restore_splitters_and_tabs_json(self):
        """Restaura los tamaños de los splitters desde la configuración guardada."""
        # Splitter horizontal medio (Cronograma | Financiero)
        sizes_mid = get_splitter_sizes("ReportWindow", "split_mid")
        if sizes_mid and all(isinstance(s, int) and s > 0 for s in sizes_mid) and len(sizes_mid) == 2:
            self.split_mid.setSizes(sizes_mid)
        else:
            self.split_mid.setSizes([400, 600])  # Default: 40% cronograma, 60% financiero

        # Splitter horizontal inferior (Checklist | Competidores)
        sizes_bottom = get_splitter_sizes("ReportWindow", "split_bottom")
        if sizes_bottom and all(isinstance(s, int) and s > 0 for s in sizes_bottom) and len(sizes_bottom) == 2:
            self.split_bottom.setSizes(sizes_bottom)
        else:
            self.split_bottom.setSizes([500, 500])  # Default: 50/50

        # Splitter vertical principal (Superior | Inferior)
        sizes_main = get_splitter_sizes("ReportWindow", "main_vsplitter")
        if sizes_main and all(isinstance(s, int) and s > 0 for s in sizes_main) and len(sizes_main) == 2:
            self.main_vsplitter.setSizes(sizes_main)
        else:
            self.main_vsplitter.setSizes([300, 500])  # Default: 37.5% superior, 62.5% inferior

    def _on_split_mid_moved(self, pos: int, index: int):
        """Guarda el estado del splitter horizontal medio."""
        try:
            set_splitter_sizes("ReportWindow", "split_mid", self.split_mid.sizes())
        except Exception:
            pass

    def _on_split_bottom_moved(self, pos: int, index: int):
        """Guarda el estado del splitter horizontal inferior."""
        try:
            set_splitter_sizes("ReportWindow", "split_bottom", self.split_bottom.sizes())
        except Exception:
            pass

    def _on_main_vsplitter_moved(self, pos: int, index: int):
        """Guarda el estado del splitter vertical principal."""
        try:
            set_splitter_sizes("ReportWindow", "main_vsplitter", self.main_vsplitter.sizes())
        except Exception:
            pass

    def _on_tabs_changed(self, idx: int):
        try:
            set_tab_index("ReportWindow", "main", int(idx))
        except Exception:
            pass

    # ---------- Cards / tablas / gráficos ----------
    def _kpi_card(self, title: str, accent: str, with_progress: bool = False) -> QFrame:
        card = QFrame()
        card.setStyleSheet(self._card_stylesheet())
        lay = QVBoxLayout(card)
        lay.setSpacing(6)
        lay.setContentsMargins(12, 12, 12, 12)

        t = QLabel(title)
        t.setStyleSheet(f"color:{self.ui['text_sec']}; font-weight:600; font-size:10pt;")
        lay.addWidget(t)

        row = QHBoxLayout()
        v = QLabel("--")
        v.setStyleSheet(f"color:{accent}; font-size:24pt; font-weight:700;")
        row.addWidget(v)
        row.addStretch(1)
        lay.addLayout(row)

        pb = None
        if with_progress:
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            pb.setFormat("%p%")
            pb.setStyleSheet(
                "QProgressBar {"
                "  min-height: 16px;"
                "  border-radius: 8px;"
                f"  background: {self.ui['alt']};"
                f"  border: 1px solid {self.ui['border']};"
                f"  color: {self.ui['text']};"
                "}"
                "QProgressBar::chunk {"
                f"  background: {self.ui['accent']};"
                "  border-radius: 8px;"
                "}"
            )
            lay.addWidget(pb)

        card._value_label = v
        card._progress = pb
        return card

    def _populate_kpis(self):
        # Estado actual
        estado = getattr(self.licitacion, "estado", "N/D") or "N/D"
        self.card_estado._value_label.setText(estado)

        # Progreso docs
        pct = 0.0
        try:
            if hasattr(self.licitacion, "get_porcentaje_completado"):
                pct = float(self.licitacion.get_porcentaje_completado() or 0.0)
        except Exception:
            pass
        self.card_docs._value_label.setText(f"{pct:.1f}%")
        if self.card_docs._progress:
            self.card_docs._progress.setValue(int(round(pct)))

        # Días restantes
        dias = "N/D"
        try:
            if hasattr(self.licitacion, "get_dias_restantes"):
                dias = str(self.licitacion.get_dias_restantes())
        except Exception:
            pass
        self.card_dias._value_label.setText(str(dias))

        # Diferencia oferta
        dif = 0.0
        try:
            if hasattr(self.licitacion, "get_diferencia_porcentual"):
                dif = float(self.licitacion.get_diferencia_porcentual(solo_participados=True) or 0.0)
        except Exception:
            pass
        color = self.ui["danger"] if dif > 0 else self.ui["success"]
        self.card_dif._value_label.setStyleSheet(f"color:{color}; font-size:24pt; font-weight:700;")
        self.card_dif._value_label.setText(f"{dif:+.2f}%")

    def _tune_cronograma_header(self):
        h = self.tbl_crono.horizontalHeader()
        h.setVisible(True)
        h.setHighlightSections(False)
        h.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setStretchLastSection(False)
        h.setMinimumSectionSize(80)

    def _populate_cronograma(self):
        self.tbl_crono.setRowCount(0)
        cron = getattr(self.licitacion, "cronograma", {}) or {}
        for evento, datos in sorted(cron.items(), key=lambda x: x[0]):
            r = self.tbl_crono.rowCount()
            self.tbl_crono.insertRow(r)
            fecha = (datos or {}).get("fecha_limite") or (datos or {}).get("fecha") or "N/D"
            estado = (datos or {}).get("estado", "Pendiente")
            self.tbl_crono.setItem(r, 0, QTableWidgetItem(str(evento)))
            self.tbl_crono.setItem(r, 1, QTableWidgetItem(str(fecha)))
            it = QTableWidgetItem(str(estado))
            low = str(estado).lower()
            if low.startswith("cumpl"):
                it.setForeground(QColor(self.ui["success"]))
            elif low.startswith("pend"):
                it.setForeground(QColor(self.ui["warning"]))
            elif low.startswith("incum") or low.startswith("venc"):
                it.setForeground(QColor(self.ui["danger"]))
            self.tbl_crono.setItem(r, 2, it)
        self.tbl_crono.resizeColumnsToContents()
        #self.tbl_crono.resizeRowsToContents()

    # ------------------------ Financiero ------------------------
    def _populate_financiero(self):
        while self.grid_fin.count():
            item = self.grid_fin.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        base = 0.0
        ofertado = 0.0
        dif_pct = 0.0
        try:
            if hasattr(self.licitacion, "get_monto_base_total"):
                base = float(self.licitacion.get_monto_base_total(solo_participados=True) or 0.0)
            if hasattr(self.licitacion, "get_oferta_total"):
                ofertado = float(self.licitacion.get_oferta_total(solo_participados=True) or 0.0)
            if hasattr(self.licitacion, "get_diferencia_porcentual"):
                dif_pct = float(self.licitacion.get_diferencia_porcentual(solo_participados=True) or 0.0)
        except Exception:
            pass

        data = [
            ("Monto Base (Presupuesto):", self._money(base), None),
            ("Monto de Nuestra Oferta:", self._money(ofertado), None),
            ("Diferencia Absoluta:", self._money(ofertado - base), self.ui["text"]),
            ("Diferencia Porcentual:", f"{dif_pct:+.2f}%", self.ui["danger"] if dif_pct > 0 else self.ui["success"]),
        ]
        for r, (lbl, val, color) in enumerate(data):
            l = QLabel(lbl)
            # ✅ REDUCIR TAMAÑO DE FUENTE
            l.setStyleSheet(f"font-weight:600; color:{self.ui['text_sec']}; font-size:9pt;")
            v = QLabel(val)
            if color:
                # ✅ REDUCIR TAMAÑO DE FUENTE
                v.setStyleSheet(f"color:{color}; font-weight:700; font-size:10pt;")
            v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.grid_fin.addWidget(l, r, 0)
            self.grid_fin.addWidget(v, r, 1)

        # ... resto del código del gráfico ...

        if MATPLOTLIB_AVAILABLE:
            ax = self.canvas_fin.figure.subplots()
            ax.clear()

            # ✅ CORRECCIÓN: Usar colores del tema en matplotlib
            ax.set_facecolor(self.ui["base"])
            ax.tick_params(axis="x", colors=self.ui["text"])
            ax.tick_params(axis="y", colors=self.ui["text"])
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color(self.ui["border"])
            ax.spines["bottom"].set_color(self.ui["border"])

            labels = ["Base", "Oferta"]
            values = [base, ofertado]
            colors = [self.ui["accent"], self.ui["success"]]

            y_pos = [1, 0]  # "Base" arriba
            bars = ax.barh(y_pos, values, color=colors, height=0.45)
            ax.set_yticks(y_pos, labels, color=self.ui["text"])

            for rect, val in zip(bars, values):
                ax.text(
                    rect.get_width() * 1.01,
                    rect.get_y() + rect.get_height() / 2,
                    f"RD$ {val:,.0f}",
                    va="center",
                    ha="left",
                    fontsize=9,
                    color=self.ui["text"],
                )

            ax.set_xlabel("Monto", color=self.ui["text_sec"])
            max_v = max(values) if values else 1
            ax.set_xlim(0, max_v * 1.25)

            self.canvas_fin.figure.set_facecolor(self.ui["base"])
            self.canvas_fin.figure.tight_layout()
            self.canvas_fin.draw()

    # ------------------------ Checklist documentos ------------------------
    def _populate_checklist(self):
        self.tbl_docs.setRowCount(0)
        docs = getattr(self.licitacion, "documentos_solicitados", []) or []
        docs_sorted = sorted(docs, key=lambda d: ((getattr(d, "categoria", "") or ""), (getattr(d, "nombre", "") or "")))
        for d in docs_sorted:
            row = self.tbl_docs.rowCount()
            self.tbl_docs.insertRow(row)
            ok = "✅" if bool(getattr(d, "presentado", False)) else "❌"
            cat = getattr(d, "categoria", "") or ""
            subs = getattr(d, "subsanable", "") or ""
            vals = [ok, getattr(d, "nombre", "") or "", cat, subs]
            for col, text in enumerate(vals):
                it = QTableWidgetItem(text)
                if col in (0, 3):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_docs.setItem(row, col, it)
            if (subs == "No Subsanable") and (ok == "❌"):
                for c in range(self.tbl_docs.columnCount()):
                    it = self.tbl_docs.item(row, c)
                    if it:
                        it.setForeground(QColor(self.ui["danger"]))
        #self.tbl_docs.resizeRowsToContents()

    # ------------------------ Competidores ------------------------
    def _populate_competidores(self):
        self.tree_comp.clear()

        def _norm(s: str) -> str:
            s = (s or "").strip()
            s = s.replace("➡️", "").replace("(Nuestra Oferta)", "")
            while "  " in s:
                s = s.replace("  ", " ")
            return s.upper()

        cron = getattr(self.licitacion, "cronograma", {}) or {}
        hito_eval = cron.get("Informe de Evaluacion Tecnica", {})
        estado_hito_cumplido = hito_eval.get("estado") == "Cumplido"
        estados_que_implican_fase_A_evaluada = {"Adjudicada", "Descalificado Fase B", "Sobre B Entregado"}
        fase_A_evaluada = estado_hito_cumplido or (getattr(self.licitacion, "estado", "") in estados_que_implican_fase_A_evaluada)

        ganadores_por_lote = {
            str(getattr(l, "numero", "")): (getattr(l, "ganador_nombre", "") or "").strip()
            for l in getattr(self.licitacion, "lotes", [])
        }
        nuestras_empresas = {_norm(str(getattr(e, "nombre", e))) for e in getattr(self.licitacion, "empresas_nuestras", [])}

        participantes = [o.__dict__ for o in getattr(self.licitacion, "oferentes_participantes", [])]
        nuestras = (
            ", ".join(str(getattr(e, "nombre", e)) for e in getattr(self.licitacion, "empresas_nuestras", []))
            or "Nuestras Empresas"
        )
        nuestras_ofertas = [
            {
                "lote_numero": getattr(l, "numero", ""),
                "monto": getattr(l, "monto_ofertado", 0),
                "paso_fase_A": getattr(l, "fase_A_superada", False),
            }
            for l in getattr(self.licitacion, "lotes", [])
            if bool(getattr(l, "participamos", False))
        ]
        participantes.append({"nombre": f"➡️ {nuestras} (Nuestra Oferta)", "es_nuestra": True, "ofertas_por_lote": nuestras_ofertas})

        for p in participantes:
            if fase_A_evaluada:
                p["monto_habilitado"] = sum(o.get("monto", 0) for o in p.get("ofertas_por_lote", []) if o.get("paso_fase_A", True))
            else:
                p["monto_habilitado"] = 0

        participantes_orden = sorted(
            participantes, key=lambda it: it["monto_habilitado"] if it["monto_habilitado"] > 0 else float("inf")
        )

        for p in participantes_orden:
            is_ours = bool(p.get("es_nuestra"))
            nombre = p.get("nombre", "")
            parent = QTreeWidgetItem(self.tree_comp)
            parent.setText(0, nombre)
            parent.setText(1, f"RD$ {sum(o.get('monto', 0) for o in p.get('ofertas_por_lote', [])):,.2f}")
            parent.setText(2, "RD$ {:,.2f}".format(p.get("monto_habilitado", 0) or 0))
            if fase_A_evaluada:
                any_ok = (
                    any(o.get("paso_fase_A", False) for o in p.get("ofertas_por_lote", []))
                    if not is_ours
                    else any(o.get("paso_fase_A", True) for o in p.get("ofertas_por_lote", []))
                )
                parent.setText(3, "Habilitado" if any_ok else "Descalificado")
            else:
                parent.setText(3, "Pendiente")

            nombre_participante_norm = _norm(nombre)
            nombres_en_padre = {x.strip() for x in nombre_participante_norm.split(",") if x.strip()}

            gano_alguno = 0

            for oferta in sorted(p.get("ofertas_por_lote", []), key=lambda o: str(o.get("lote_numero"))):
                lote_num = str(oferta.get("lote_numero"))
                lote_obj = next(
                    (l for l in getattr(self.licitacion, "lotes", []) if str(getattr(l, "numero", "")) == lote_num), None
                )
                lote_nombre = getattr(lote_obj, "nombre", "N/E") if lote_obj else "N/E"
                base = float(getattr(lote_obj, "monto_base", 0) or 0.0) if lote_obj else 0.0
                of_m = float(oferta.get("monto", 0) or 0.0)
                dif_pct = ((of_m - base) / base * 100.0) if base > 0 and of_m > 0 else 0.0

                child = QTreeWidgetItem(parent)
                child.setText(0, f"    ↳ Lote {lote_num}: {lote_nombre}")
                child.setText(1, f"RD$ {of_m:,.2f}")
                child.setText(4, f"RD$ {base:,.2f}" if base > 0 else "N/D")
                child.setText(5, f"{dif_pct:+.2f}%" if base > 0 and of_m > 0 else "N/D")
                if fase_A_evaluada:
                    paso_a = oferta.get("paso_fase_A", True) if is_ours else oferta.get("paso_fase_A", False)
                    child.setText(3, "✅" if paso_a else "❌")
                else:
                    child.setText(3, "⏳")

                ganador_real = (ganadores_por_lote.get(lote_num, "") or "").strip().upper()
                es_ganador = False
                if ganador_real:
                    if is_ours and ganador_real in nuestras_empresas:
                        es_ganador = True
                    elif ganador_real in nombres_en_padre:
                        es_ganador = True
                    elif nombre_participante_norm.startswith(ganador_real):
                        es_ganador = True

                child.setText(6, "Sí" if es_ganador else "No")
                if es_ganador:
                    gano_alguno += 1
                    for c in range(child.columnCount()):
                        child.setForeground(c, QColor(self.ui["success"]))

            if gano_alguno > 0:
                parent.setText(6, f"Sí ({gano_alguno})")
                for c in range(parent.columnCount()):
                    parent.setForeground(c, QColor(self.ui["success"]))

        self.tree_comp.expandAll()
        for i in range(7):
            self.tree_comp.resizeColumnToContents(i)

    # ------------------------ Exportar ------------------------
    def _export_report(self, formato: str):
        ext = ".pdf" if formato == "pdf" else ".xlsx"
        title = f"Guardar como {formato.upper()}"
        default_name = f"Reporte_{str(getattr(self.licitacion, 'numero_proceso', 'proceso')).replace(' ', '_')}{ext}"
        path, _ = QFileDialog.getSaveFileName(self, title, default_name, "PDF (*.pdf);;Excel (*.xlsx)")
        if not path:
            return

        if not REPORT_GENERATOR_AVAILABLE or ReportGenerator is None:
            return QMessageBox.warning(
                self,
                "Exportar",
                "ReportGenerator no está disponible en esta instalación.\n\n"
                f"Detalle del import:\n{REPORT_GENERATOR_IMPORT_ERROR}\n\n"
                "Asegúrate de que exista app/core/reporting/report_generator.py y que "
                "app/core/reporting/__init__.py exporte ReportGenerator.",
            )

        if formato == "pdf" and not REPORTLAB_AVAILABLE:
            return QMessageBox.warning(self, "Exportar", "La librería 'reportlab' no está instalada (pip install reportlab).")
        if formato == "excel" and not OPENPYXL_AVAILABLE:
            return QMessageBox.warning(self, "Exportar", "La librería 'openpyxl' no está instalada (pip install openpyxl).")

        try:
            gen = ReportGenerator()
            if hasattr(gen, "generate_bid_results_report"):
                gen.generate_bid_results_report(self.licitacion, path)
            elif hasattr(gen, "generate_package_analysis_report"):
                gen.generate_package_analysis_report(self.licitacion, path)
            else:
                raise AttributeError(
                    "ReportGenerator no expone 'generate_bid_results_report' ni 'generate_package_analysis_report'."
                )

            QMessageBox.information(self, "Exportar", f"Reporte guardado en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Exportar", f"No se pudo exportar el reporte:\n{e}")
            import traceback
            traceback.print_exc()

    # ------------------------ Utilidades ------------------------
    def _tune_table(self, t: QTableWidget):
        """Configura tabla con estilos mínimos que respetan el tema."""
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Solo definir gridline-color
        t.setStyleSheet(
            "QTableWidget {"
            f"  gridline-color: {self.ui['border']};"
            "}"
        )
        
        # ✅ AÑADIR: Reducir altura de filas
        t.verticalHeader().setDefaultSectionSize(28)  # Altura de fila reducida
        t.setMinimumHeight(120)  # Altura mínima de la tabla

    def _new_canvas(self):
        """Crea canvas de matplotlib con fondo del tema."""
        fig = Figure(figsize=(5.2, 2.8), dpi=100, facecolor=self.ui["base"])
        return FigureCanvas(fig)

    def _wrap_canvas(self, title: str, canvas):
        box = QGroupBox(title)
        box.setStyleSheet(self._card_stylesheet())
        v = QVBoxLayout(box)
        v.addWidget(canvas, 1)
        return box

    def _money(self, v: float) -> str:
        try:
            return "RD$ {:,.2f}".format(float(v or 0.0))
        except Exception:
            return "RD$ 0.00"

    def closeEvent(self, event):
        """Guarda todos los estados de splitters al cerrar."""
        try:
            set_splitter_sizes("ReportWindow", "split_mid", self.split_mid.sizes())
            set_splitter_sizes("ReportWindow", "split_bottom", self.split_bottom.sizes())
            set_splitter_sizes("ReportWindow", "main_vsplitter", self.main_vsplitter.sizes())
        finally:
            super().closeEvent(event)

    def _icon(self, std: QStyle.StandardPixmap, semantic_name: str = "") -> QIcon:
        """
        Devuelve un icono. Intenta cargar app.ui.icons.icon_loader.get_icon en tiempo de ejecución.
        Si falla o no existe, usa el QStyle nativo como fallback.
        """
        if not hasattr(self, "_icon_loader_func"):
            self._icon_loader_func = None
            try:
                import importlib
                mod = importlib.import_module("app.ui.icons.icon_loader")
                func = getattr(mod, "get_icon", None)
                if callable(func):
                    self._icon_loader_func = func
            except Exception:
                self._icon_loader_func = None

        if callable(getattr(self, "_icon_loader_func", None)) and semantic_name:
            try:
                return self._icon_loader_func(semantic_name)  # type: ignore[misc]
            except Exception:
                pass

        return self.style().standardIcon(std)