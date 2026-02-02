# app/ui/tabs/tab_details_general.py
from __future__ import annotations
import os
import platform
import subprocess
import datetime
from typing import TYPE_CHECKING, List, Dict, Any
from app.ui.dialogs.visor_documentos_dialog import VisorDocumentosDialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QTextEdit, QDateEdit, QMessageBox, QFileDialog, QApplication, QStyle, QDialog
)
from PyQt6.QtCore import Qt, QDate, QSettings # Añade QSettings
from PyQt6.QtGui import QIcon, QDesktopServices

# Importaciones necesarias para diálogos y modelos
from app.core.models import Licitacion, Empresa, Documento # Añade Documento
from app.core.db_adapter import DatabaseAdapter
# Importar diálogos necesarios (ajusta las rutas si es necesario)
from app.ui.dialogs.seleccionar_empresas_dialog import SeleccionarEmpresasDialog
from app.ui.dialogs.gestion_documentos_dialog import GestionDocumentosDialog
from app.ui.dialogs.ordenar_documentos_dialog import DialogoOrdenarDocumentos

if TYPE_CHECKING:
    from app.ui.windows.licitation_details_window import LicitationDetailsWindow
# --- Importaciones Necesarias (Añadir/Verificar al principio del archivo) ---
import os
import logging
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
# Importar el diálogo de orden y la lista de categorías
from app.ui.dialogs.ordenar_documentos_dialog import DialogoOrdenarDocumentos, CATEGORIAS_EXPEDIENTE
# Importar la función de generación de PDF del nuevo módulo
from app.core.logic.pdf_generator import generar_pdf_expediente_categoria
# Importar la función de previsualización
from app.core.utils import previsualizar_archivo
# Importar el diálogo de orden y la lista de categorías
from app.ui.dialogs.ordenar_documentos_dialog import DialogoOrdenarDocumentos, CATEGORIAS_EXPEDIENTE
# Importar la función de generación de ZIP del nuevo módulo
from app.core.logic.zip_generator import generar_expediente_zip_por_categoria
# Constantes para estados (puedes moverlas a config.py o models.py)
from app.ui.dialogs.historial_subsanacion_dialog import HistorialSubsanacionDialog # ¡Importar nuevo diálogo!

ESTADOS_LICITACION = [
    "Iniciada", "En Proceso", "Sobre A Entregado", "Sobre B Entregado",
    "Descalificado Fase A", "Descalificado Fase B", "Adjudicada", "Desierta", "Cancelada"
]
ESTADOS_CRONOGRAMA = ["Pendiente", "Cumplido", "Incumplido"]

# --- AÑADIR ESTA LÍNEA ---
DEFAULT_CATEGORIES = ["Legal", "Técnica", "Economica", "Otros"]
# --- FIN LÍNEA AÑADIDA ---

# =============================================================================
# ▼▼▼ CORRECCIÓN 1: El nombre de la clase es 'DialogoGestionarDocumento' ▼▼▼
# =============================================================================
from app.ui.dialogs.gestionar_documento_dialog import DialogoGestionarDocumento 
# =============================================================================

# Podrías necesitar otros diálogos como el visor, gestión de docs, historial, etc.
# from app.ui.dialogs.visor_documentos_dialog import VisorDocumentosDialog
# from app.ui.dialogs.historial_subsanacion_dialog import HistorialSubsanacionDialog

# Importar helper para rutas de Dropbox si lo necesitas para abrir archivos
# from app.core.utils import reconstruir_ruta_absoluta # Asumiendo que moviste la función

if TYPE_CHECKING:
    # Evita importación circular, solo para type hinting
    from app.ui.windows.licitation_details_window import LicitationDetailsWindow

# Constantes para estados (puedes moverlas a config.py o models.py)
ESTADOS_LICITACION = [
    "Iniciada", "En Proceso", "Sobre A Entregado", "Sobre B Entregado",
    "Descalificado Fase A", "Descalificado Fase B", "Adjudicada", "Desierta", "Cancelada"
]
ESTADOS_CRONOGRAMA = ["Pendiente", "Cumplido", "Incumplido"]

class TabDetailsGeneral(QWidget):
    """Pestaña para los detalles generales, estado, cronograma y acciones de documentos."""

    def __init__(self, licitacion:  Licitacion, db: DatabaseAdapter, parent_window: LicitationDetailsWindow):
        super().__init__(parent_window)
        
        # **CRÍTICO:  Guardar la MISMA referencia que recibimos (no copiar)**
        self.licitacion = licitacion
        self.db = db
        self. parent_window = parent_window  # Referencia a la ventana principal de detalles

        # DEBUG: Confirmar que recibimos la misma referencia
        print(f"[DEBUG][TabDetailsGeneral.__init__] id(licitacion recibida): {id(self.licitacion)}")
        print(f"[DEBUG][TabDetailsGeneral.__init__] empresas_nuestras:  {len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0}")
        if self.licitacion.empresas_nuestras:
            for emp in self. licitacion.empresas_nuestras:
                nombre = emp.nombre if hasattr(emp, 'nombre') else str(emp)
                print(f"  - {nombre}")

        # Referencias a los widgets de entrada para fácil acceso
        self._widgets: Dict[str, QWidget] = {}

        self._build_ui()
        
        # **NO llamar load_data() aquí - se llama desde LicitationDetailsWindow._load_data_into_tabs()**
        # Si lo llamas aquí, puede sobrescribir datos antes de que se carguen desde el header

    def _build_ui(self):
        """Construye la interfaz de usuario de la pestaña."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15) # Espacio entre secciones

        # --- Sección Superior (Identificación y Empresas) ---
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Grupo Identificación
        group_ident = QGroupBox("Identificación del Proceso")
        form_ident = QFormLayout(group_ident) # Ideal para label-widget pairs
        form_ident.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self._widgets['codigo'] = QLineEdit()
        self._widgets['nombre'] = QLineEdit()
        self._widgets['institucion'] = QComboBox()
        self._widgets['institucion'].setEditable(False) # Hacerlo no editable como en Tkinter
        # Rellenaremos las instituciones en load_data
        form_ident.addRow("Código:", self._widgets['codigo'])
        form_ident.addRow("Nombre:", self._widgets['nombre'])
        form_ident.addRow("Institución:", self._widgets['institucion'])
        top_layout.addWidget(group_ident, stretch=2) # Darle más peso horizontal

        # Grupo Nuestras Empresas
        group_empresas = QGroupBox("Nuestras Empresas")
        layout_empresas = QVBoxLayout(group_empresas)
        self._widgets['empresas_label'] = QLabel("Cargando...")
        self._widgets['empresas_label'].setWordWrap(True)
        self._widgets['empresas_label'].setStyleSheet("color: gray;")
        btn_select_empresas = QPushButton("Seleccionar...")
        btn_select_empresas.setIcon(QIcon.fromTheme("document-open", self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)))
        btn_select_empresas.clicked.connect(self._abrir_selector_empresas)
        layout_empresas.addWidget(self._widgets['empresas_label'], stretch=1) # Ocupa espacio vertical
        layout_empresas.addWidget(btn_select_empresas, alignment=Qt.AlignmentFlag.AlignRight)
        top_layout.addWidget(group_empresas, stretch=1) # Menos peso

        # --- Sección Media (Info General y Cronograma) ---
        middle_layout = QHBoxLayout()
        main_layout.addLayout(middle_layout)

        # Grupo Info General y Estado
        group_info = QGroupBox("Información General y Estado")
        layout_info = QFormLayout(group_info)
        layout_info.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self._widgets['estado'] = QComboBox()
        self._widgets['estado'].addItems(ESTADOS_LICITACION)
        self._widgets['estado'].currentIndexChanged.connect(self._on_estado_change)
        self._widgets['adjudicada_a'] = QComboBox()
        self._widgets['adjudicada_a'].setEditable(True) # Permitir escribir o seleccionar
        self._widgets['adjudicada_a'].setEnabled(False) # Deshabilitado inicialmente
        self._widgets['progreso_label'] = QLabel("0.0%")
        self._widgets['progreso_label'].setStyleSheet("font-weight: bold;")
        self._widgets['docs_manual_check'] = QCheckBox("Documentación completa (sin requisitos)")
        self._widgets['fase_b_check'] = QCheckBox("Fase B (Sobres Económicos) superada")
        self._widgets['motivo_text'] = QTextEdit()
        self._widgets['motivo_text'].setPlaceholderText("Motivo de descalificación o comentarios adicionales...")
        self._widgets['motivo_text'].setFixedHeight(80) # Altura fija

        layout_info.addRow("Estado:", self._widgets['estado'])
        layout_info.addRow("Adjudicada a:", self._widgets['adjudicada_a'])
        layout_info.addRow("Progreso Docs:", self._widgets['progreso_label'])
        layout_info.addRow(self._widgets['docs_manual_check'])
        layout_info.addRow(self._widgets['fase_b_check'])
        layout_info.addRow(QLabel("Motivo/Comentarios:"))
        layout_info.addRow(self._widgets['motivo_text'])
        middle_layout.addWidget(group_info)

        # Grupo Cronograma
        group_crono = QGroupBox("Cronograma del Proceso")
        layout_crono = QGridLayout(group_crono) # Usamos grid para alinear columnas
        self._widgets['cronograma'] = {} # Dict para guardar widgets de cronograma {evento: (QDateEdit, QComboBox)}
        eventos = self.licitacion.cronograma.keys() if self.licitacion.cronograma else []
        if not eventos: # Asegurar eventos por defecto si no hay cronograma
             eventos = [
                "Presentacion de Ofertas", "Apertura de Ofertas", "Informe de Evaluacion Tecnica",
                "Notificaciones de Subsanables", "Entrega de Subsanaciones",
                "Notificacion de Habilitacion Sobre B", "Apertura de Oferta Economica", "Adjudicacion"
             ]
        for i, evento in enumerate(eventos):
            lbl = QLabel(f"{evento}:")
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setFixedWidth(120) # Ancho fijo para fecha
            combo_estado = QComboBox()
            combo_estado.addItems(ESTADOS_CRONOGRAMA)
            combo_estado.setFixedWidth(100) # Ancho fijo para estado

            layout_crono.addWidget(lbl, i, 0)
            layout_crono.addWidget(date_edit, i, 1)
            layout_crono.addWidget(combo_estado, i, 2)
            self._widgets['cronograma'][evento] = (date_edit, combo_estado)
        layout_crono.setColumnStretch(0, 1) # Permitir que la etiqueta crezca si es necesario
        middle_layout.addWidget(group_crono)

        # --- Sección Inferior (Acciones de Documentos) ---
        group_docs = QGroupBox("Documentos del Proceso")
        layout_docs = QGridLayout(group_docs) # Grid para botones en 2 filas
        main_layout.addWidget(group_docs)

        buttons_docs_info = [
            ("👀 Ver checklist...", self._abrir_visor_docs, "document-open-recent", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("🛠️ Gestionar Documentos...", self._abrir_gestion_docs, "document-edit", QStyle.StandardPixmap.SP_FileDialogContentsView),
            ("🔀 Ordenar Docs (Guardar)", self._ordenar_docs, "view-sort-ascending", QStyle.StandardPixmap.SP_ArrowUp),
            ("📄 Generar Expediente PDF", self._generar_expediente_pdf, "application-pdf", QStyle.StandardPixmap.SP_FileIcon),
            ("🗃️ Generar ZIP Categoría", self._generar_expediente_zip, "application-zip", QStyle.StandardPixmap.SP_DriveHDIcon),
            ("🗂️ Abrir Carpeta Destino", self._abrir_carpeta_destino, "folder-open", QStyle.StandardPixmap.SP_DirOpenIcon),
            ("🔎 Validar Faltantes", self._validar_faltantes, "edit-find", QStyle.StandardPixmap.SP_DialogYesButton),
            ("📜 Ver Historial Subsanación", self._abrir_historial_subsanacion, "view-history", QStyle.StandardPixmap.SP_MessageBoxInformation),
        ]

        row, col = 0, 0
        max_cols = 4 # Botones por fila
        for text, func, icon_theme, icon_std in buttons_docs_info:
            button = QPushButton(text)
            # Intentar icono de tema, si no, usar estándar
            icon = QIcon.fromTheme(icon_theme, self.style().standardIcon(icon_std))
            if not icon.isNull():
                 button.setIcon(icon)
            button.clicked.connect(func)
            layout_docs.addWidget(button, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        main_layout.addStretch(1) # Empuja todo hacia arriba

    # --- Métodos de Carga y Recolección de Datos ---

    def load_data(self):
        """Carga los datos de self.licitacion en los widgets de la pestaña."""
        print(f"[DEBUG][TabDetailsGeneral.load_data] INICIO")
        print(f"  - id(self. licitacion): {id(self.licitacion)}")
        print(f"  - numero_proceso: {self.licitacion.numero_proceso or '(vacío)'}")
        print(f"  - empresas_nuestras: {len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0}")
        
        # Cargar campos básicos
        self._widgets['codigo'].setText(self.licitacion.numero_proceso or "")
        self._widgets['nombre'].setText(self. licitacion.nombre_proceso or "")

        # Cargar y seleccionar Institución
        combo_inst = self._widgets['institucion']
        combo_inst.blockSignals(True)
        combo_inst.clear()
        try:
            # Obtenemos lista actualizada de la BD
            instituciones_db = self.db.get_instituciones_maestras()
            nombres_instituciones = sorted([i. get('nombre', '') for i in instituciones_db if i.get('nombre')])
            combo_inst.addItems(nombres_instituciones)
            
            # Intentar seleccionar la actual
            if self.licitacion.institucion and self.licitacion.institucion in nombres_instituciones:
                combo_inst.setCurrentText(self.licitacion.institucion)
            elif self.licitacion.institucion:
                # Si no está en la lista (quizás se borró), añadirla temporalmente
                combo_inst.addItem(self. licitacion.institucion)
                combo_inst.setCurrentText(self.licitacion.institucion)
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error cargando instituciones:  {e}")
            import traceback
            traceback.print_exc()
            # Mostrar la que está guardada aunque falle la carga
            if self.licitacion.institucion:
                combo_inst. addItem(self.licitacion.institucion)
                combo_inst.setCurrentText(self. licitacion.institucion)
        finally:
            combo_inst.blockSignals(False)

        # **CRÍTICO: Actualizar display de empresas (NO sobrescribir empresas_nuestras)**
        print(f"[DEBUG][TabDetailsGeneral.load_data] Antes de _actualizar_display_empresas:")
        print(f"  - empresas_nuestras: {len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0}")
        
        try:
            self._actualizar_display_empresas()
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error en _actualizar_display_empresas: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[DEBUG][TabDetailsGeneral.load_data] Después de _actualizar_display_empresas:")
        print(f"  - empresas_nuestras: {len(self.licitacion.empresas_nuestras) if self.licitacion. empresas_nuestras else 0}")

        # Cargar Estado y Adjudicado A
        self._widgets['estado']. setCurrentText(self.licitacion.estado or "Iniciada")
        
        combo_adj = self._widgets['adjudicada_a']
        combo_adj.blockSignals(True)
        combo_adj.clear()
        
        try:
            # Construir lista de participantes para el combo "Adjudicada a"
            nuestras_empresas_nombres = set()
            if self.licitacion.empresas_nuestras:
                for e in self.licitacion.empresas_nuestras:
                    nombre = e.nombre if hasattr(e, 'nombre') else str(e)
                    if nombre: 
                        nuestras_empresas_nombres.add(nombre)
            
            competidores_nombres = set()
            if hasattr(self.licitacion, 'oferentes_participantes') and self.licitacion.oferentes_participantes:
                for o in self.licitacion. oferentes_participantes:
                    if hasattr(o, 'nombre') and o.nombre:
                        competidores_nombres. add(o.nombre)
            
            todos_participantes = sorted(list(nuestras_empresas_nombres. union(competidores_nombres)))
            
            if todos_participantes:
                combo_adj. addItems(todos_participantes)
            
            # Seleccionar la empresa adjudicada si existe
            if self.licitacion.adjudicada_a: 
                if self.licitacion.adjudicada_a in todos_participantes:
                    combo_adj.setCurrentText(self.licitacion.adjudicada_a)
                else:
                    # Permitir texto libre si no está en la lista
                    combo_adj.setEditText(self.licitacion. adjudicada_a)
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error construyendo combo adjudicada_a: {e}")
            import traceback
            traceback.print_exc()
        finally:
            combo_adj.blockSignals(False)
        
        # Habilitar/deshabilitar "Adjudicada a" según el estado
        try:
            self._on_estado_change()
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error en _on_estado_change: {e}")

        # Cargar Checkboxes y Texto
        try:
            if hasattr(self.licitacion, 'get_porcentaje_completado'):
                progreso = self.licitacion.get_porcentaje_completado()
            else:
                progreso = 0.0
            self._widgets['progreso_label']. setText(f"{progreso:.1f}%")
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error calculando progreso: {e}")
            self._widgets['progreso_label']. setText("0.0%")
        
        self._widgets['docs_manual_check'].setChecked(bool(self.licitacion.docs_completos_manual))
        self._widgets['fase_b_check'].setChecked(bool(self.licitacion.fase_B_superada))
        self._widgets['motivo_text']. setPlainText(self.licitacion.motivo_descalificacion or "")

        # Cargar Cronograma
        try:
            crono_widgets = self._widgets.get('cronograma', {})
            crono_data = self.licitacion.cronograma or {}
            
            for evento, (date_edit, combo_estado) in crono_widgets.items():
                datos_evento = crono_data. get(evento, {})
                fecha_str = datos_evento. get("fecha_limite")
                estado = datos_evento.get("estado", "Pendiente")
                
                # Cargar fecha
                if fecha_str:
                    try: 
                        qdate = QDate.fromString(fecha_str, "yyyy-MM-dd")
                        if qdate.isValid():
                            date_edit. setDate(qdate)
                        else:
                            date_edit.clear()
                    except Exception as e_fecha:
                        print(f"[WARNING][TabDetailsGeneral.load_data] Error parseando fecha '{fecha_str}' para evento '{evento}': {e_fecha}")
                        date_edit.clear()
                else:
                    date_edit.clear()
                
                # Cargar estado
                combo_estado.setCurrentText(estado)
        except Exception as e:
            print(f"[ERROR][TabDetailsGeneral.load_data] Error cargando cronograma: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[DEBUG][TabDetailsGeneral. load_data] FIN")
        print(f"  - empresas_nuestras final: {len(self.licitacion.empresas_nuestras) if self.licitacion. empresas_nuestras else 0}")



    def collect_data(self) -> bool:
        """Recolecta los datos de los widgets y actualiza self.licitacion.  Retorna False si hay error."""
        print("TabDetailsGeneral:  Recolectando datos...")
        try:
            self.licitacion.numero_proceso = self._widgets['codigo']. text().strip()
            self.licitacion.nombre_proceso = self._widgets['nombre'].text().strip()
            self.licitacion. institucion = self._widgets['institucion'].currentText()

            # Estado / Adjudicación
            self.licitacion.estado = self._widgets['estado'].currentText()
            self.licitacion.adjudicada = (self. licitacion.estado == "Adjudicada")
            # Leemos el texto actual del combobox (puede ser seleccionado o escrito)
            self.licitacion.adjudicada_a = self._widgets['adjudicada_a'].currentText().strip() if self. licitacion.adjudicada else ""

            # Checkboxes y Texto
            self.licitacion. docs_completos_manual = self._widgets['docs_manual_check'].isChecked()
            self.licitacion.fase_B_superada = self._widgets['fase_b_check'].isChecked()
            self.licitacion.motivo_descalificacion = self._widgets['motivo_text'].toPlainText().strip()

            # Cronograma
            if not isinstance(self.licitacion.cronograma, dict):
                self.licitacion.cronograma = {}  # Asegurar que sea un dict
            crono_widgets = self._widgets. get('cronograma', {})
            for evento, (date_edit, combo_estado) in crono_widgets.items():
                fecha = date_edit.date().toString("yyyy-MM-dd") if not date_edit.date().isNull() else None
                self.licitacion. cronograma[evento] = {
                    "fecha_limite": fecha,
                    "estado":  combo_estado.currentText()
                }

            # **Empresas propias**:  Ya están en self.licitacion.empresas_nuestras
            # (actualizadas por _abrir_selector_empresas), solo validamos
            empresas_count = len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0
            print(f"TabDetailsGeneral:  empresas_nuestras actuales en licitacion: {empresas_count}")
            if empresas_count > 0:
                for emp in self.licitacion.empresas_nuestras:
                    nombre = emp.nombre if hasattr(emp, 'nombre') else str(emp)
                    print(f"  - {nombre}")

            # Validación básica (código, nombre y al menos una empresa)
            if not self.licitacion.numero_proceso or not self.licitacion.nombre_proceso:
                QMessageBox.warning(
                    self, 
                    "Datos Incompletos", 
                    "El Código y el Nombre del Proceso no pueden estar vacíos."
                )
                return False
            
            if empresas_count == 0:
                QMessageBox.warning(
                    self, 
                    "Campo Requerido", 
                    "Debe seleccionar al menos una empresa propia.\n\n"
                    "Use el botón '✓ Seleccionar.. .' en la sección 'B. Empresas Propias'."
                )
                return False

            print("TabDetailsGeneral: Datos recolectados correctamente.")
            return True  # Indicar éxito
            
        except Exception as e: 
            QMessageBox.critical(
                self, 
                "Error al Recolectar", 
                f"No se pudieron leer los datos de la pestaña General:\n{e}"
            )
            print(f"Error detallado recolectando General: {e}")
            import traceback
            traceback.print_exc()
            return False  # Indicar fallo

    # --- Métodos de Acción / Slots ---

    def _on_estado_change(self):
        """Habilita o deshabilita el ComboBox 'Adjudicada a' según el estado."""
        es_adjudicada = self._widgets['estado'].currentText() == "Adjudicada"
        self._widgets['adjudicada_a'].setEnabled(es_adjudicada)
        if not es_adjudicada:
             # Limpiar selección si el estado ya no es Adjudicada
             self._widgets['adjudicada_a'].setCurrentIndex(-1)
             self._widgets['adjudicada_a'].setCurrentText("")


    def _abrir_selector_empresas(self):
        """Abre el diálogo para seleccionar las empresas participantes."""
        print("[DEBUG][_abrir_selector_empresas] INICIO")
        print(f"  - id(self.licitacion): {id(self.licitacion)}")
        print(f"  - empresas_nuestras ANTES: {len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0}")
        
        try:
            # Obtener lista completa de empresas maestras desde la DB
            print("[DEBUG][_abrir_selector_empresas] Obteniendo empresas maestras de la DB...")
            todas_las_empresas_dicts = self.db.get_empresas_maestras()
            print(f"[DEBUG][_abrir_selector_empresas] Empresas disponibles en DB: {len(todas_las_empresas_dicts)}")
            
            # Obtener lista actual de nombres de la licitación
            nombres_actuales = set()
            if self.licitacion.empresas_nuestras:
                for e in self.licitacion.empresas_nuestras:
                    nombre = e.nombre if hasattr(e, 'nombre') else str(e)
                    if nombre: 
                        nombres_actuales. add(nombre)
            
            print(f"[DEBUG][_abrir_selector_empresas] Empresas pre-seleccionadas: {nombres_actuales}")

            print("[DEBUG][_abrir_selector_empresas] Abriendo diálogo...")
            dialogo = SeleccionarEmpresasDialog(self, todas_las_empresas_dicts, list(nombres_actuales))
            resultado = dialogo.exec()
            
            print(f"[DEBUG][_abrir_selector_empresas] Resultado del diálogo: {resultado} (Accepted={QDialog.DialogCode.Accepted})")
            
            if resultado == QDialog. DialogCode.Accepted:
                nuevos_nombres_seleccionados = dialogo.get_empresas_seleccionadas()
                print(f"[DEBUG][_abrir_selector_empresas] Nuevas empresas seleccionadas: {nuevos_nombres_seleccionados}")
                
                # Actualizar el objeto licitacion en memoria (creando nuevos objetos Empresa)
                self.licitacion.empresas_nuestras = [Empresa(nombre) for nombre in nuevos_nombres_seleccionados]
                
                print(f"[DEBUG][_abrir_selector_empresas] DESPUÉS de asignar:")
                print(f"  - id(self.licitacion): {id(self.licitacion)}")
                print(f"  - empresas_nuestras:  {len(self.licitacion.empresas_nuestras)}")
                for emp in self.licitacion. empresas_nuestras: 
                    nombre = emp.nombre if hasattr(emp, 'nombre') else str(emp)
                    print(f"    - {nombre}")
                
                # Actualizar la etiqueta visual
                self._actualizar_display_empresas()
                
                # Opcional: notificar a otras pestañas si es necesario
                try:
                    if hasattr(self, 'parent_window') and self.parent_window:
                        if hasattr(self.parent_window, 'tab_lotes'):
                            # Actualizar combos de empresa en la pestaña de lotes
                            if hasattr(self.parent_window. tab_lotes, 'actualizar_combos_empresa'):
                                self.parent_window.tab_lotes. actualizar_combos_empresa()
                                print("[DEBUG][_abrir_selector_empresas] Combos de empresa actualizados en tab_lotes")
                except Exception as e:
                    print(f"[WARNING][_abrir_selector_empresas] No se pudo actualizar tab_lotes: {e}")
            else:
                print("[DEBUG][_abrir_selector_empresas] Usuario canceló el diálogo")
                
        except Exception as e: 
            print(f"[ERROR][_abrir_selector_empresas] Excepción: {e}")
            import traceback
            traceback. print_exc()
            QMessageBox.critical(self, "Error", f"No se pudo abrir el selector de empresas:\n{e}")
        
        print("[DEBUG][_abrir_selector_empresas] FIN")

    def _actualizar_display_empresas(self):
        """Actualiza el label que muestra las empresas seleccionadas."""
        print(f"[DEBUG][_actualizar_display_empresas] INICIO")
        print(f"  - empresas_nuestras: {len(self.licitacion.empresas_nuestras) if self.licitacion.empresas_nuestras else 0}")
        
        # Verificar que el widget existe
        if 'empresas_label' not in self._widgets:
            print("[ERROR][_actualizar_display_empresas] Widget 'empresas_label' no encontrado en self._widgets")
            return
        
        empresas_label = self._widgets['empresas_label']
        
        if not self.licitacion.empresas_nuestras or len(self.licitacion. empresas_nuestras) == 0:
            empresas_label.setText("(Ninguna empresa seleccionada)")
            empresas_label.setStyleSheet("color: gray; font-style: italic;")
            print("[DEBUG][_actualizar_display_empresas] Mostrando:  (Ninguna)")
        else:
            nombres = []
            for emp in self.licitacion.empresas_nuestras:
                nombre = emp. nombre if hasattr(emp, 'nombre') else str(emp)
                if nombre:
                    nombres.append(nombre)
            
            if nombres:
                texto = "\n".join(nombres)  # Una empresa por línea
                empresas_label.setText(texto)
                empresas_label.setStyleSheet("color: #C62828; font-weight: bold;")  # Rojo oscuro
                print(f"[DEBUG][_actualizar_display_empresas] Mostrando {len(nombres)} empresa(s):")
                for n in nombres:
                    print(f"    - {n}")
            else:
                empresas_label.setText("(Ninguna empresa seleccionada)")
                empresas_label.setStyleSheet("color: gray; font-style: italic;")
                print("[DEBUG][_actualizar_display_empresas] Sin nombres válidos, mostrando (Ninguna)")
        
        print("[DEBUG][_actualizar_display_empresas] FIN")




    def _abrir_visor_docs(self):
        QMessageBox.information(self, "Próximamente", "Abrir Visor de Checklist (a implementar).")
        # try:
        #     # Asume que VisorDocumentosDialog existe y recibe (parent, licitacion, categorias)
        #     categorias = self.db.get_categorias_documentos() # O donde las obtengas
        #     dlg = VisorDocumentosDialog(self, self.licitacion, categorias)
        #     dlg.exec()
        #     self.load_data() # Recargar por si algo cambió indirectamente
        # except Exception as e:
        #     QMessageBox.critical(self, "Error", f"No se pudo abrir el visor:\n{e}")

    def _abrir_gestion_docs(self):
            """Abre el diálogo principal para gestionar la lista de documentos."""
            print("Abriendo Gestión de Documentos...")
            try:
                # Pasar la licitación actual y el adaptador de DB
                dlg = GestionDocumentosDialog(self, self.licitacion, self.db)
                result = dlg.exec() # Muestra modal y espera

                if result == QDialog.DialogCode.Accepted:
                    # Si el usuario presionó OK, los cambios ya están en self.licitacion.documentos_solicitados
                    # Solo necesitamos recargar la vista de esta pestaña (TabDetailsGeneral)
                    print("Gestión de Documentos aceptada. Recargando TabDetailsGeneral...")
                    self.load_data() # Recarga datos como el % completado
                    # La ventana principal (LicitationDetailsWindow) guardará los cambios al presionar su botón Guardar
                else:
                    print("Gestión de Documentos cancelada.")

            except ImportError:
                QMessageBox.warning(self, "Archivo Faltante", "No se encontró el archivo 'gestion_documentos_dialog.py'.")
            except Exception as e:
                QMessageBox.critical(self, "Error al Abrir Gestión", f"No se pudo abrir la gestión de documentos:\n{e}")
                print(f"Error detallado abriendo gestión docs: {e}")

    def _ordenar_docs(self):
            """Abre el diálogo para reordenar documentos y guarda el orden en memoria y BD."""
            print("Abriendo diálogo para ordenar documentos...")
            if not self.licitacion.documentos_solicitados:
                QMessageBox.information(self, "Sin Documentos", "Esta licitación no tiene documentos para ordenar.")
                return

            try:
                # Crear y mostrar el diálogo, pasando la lista actual
                dlg = DialogoOrdenarDocumentos(self, self.licitacion.documentos_solicitados)
                result = dlg.exec() # Muestra modal

                if result == QDialog.DialogCode.Accepted:
                    # Obtener el nuevo orden del diálogo
                    nuevo_orden_por_categoria = dlg.get_orden_documentos()
                    # (Opcional: usar dlg.get_inclusion_categorias() si lo necesitas)

                    if nuevo_orden_por_categoria is None:
                        print("WARN: El diálogo de orden se aceptó pero no devolvió resultados.")
                        return

                    # --- Actualizar atributo 'orden_pliego' en los objetos Documento ---
                    pares_docid_orden = [] # Lista para guardar en BD: [(doc_id, nuevo_orden)]
                    orden_global = 1
                    # Iterar en el orden de categorías definido en el diálogo
                    for cat_name in dlg._categorias_orden: # Usar el orden interno del diálogo
                        lista_ordenada_cat = nuevo_orden_por_categoria.get(cat_name, [])
                        for doc in lista_ordenada_cat:
                            # Actualizar el objeto Documento en memoria (en self.licitacion.documentos_solicitados)
                            setattr(doc, 'orden_pliego', orden_global)
                            # Preparar datos para guardar en BD (solo si el doc tiene ID)
                            doc_id = getattr(doc, "id", None)
                            if doc_id is not None:
                                pares_docid_orden.append((doc_id, orden_global))
                            orden_global += 1

                    print(f"Nuevo orden aplicado en memoria a {len(pares_docid_orden)} documentos.")

                    # --- Guardar orden en Base de Datos ---
                    if self.licitacion.id and pares_docid_orden: # Solo si la licitación ya existe y hay orden
                        try:
                            ok = self.db.guardar_orden_documentos(self.licitacion.id, pares_docid_orden)
                            if ok:
                                QMessageBox.information(self, "Orden Guardado", "El nuevo orden de documentos se ha guardado en la base de datos.")
                            else:
                                QMessageBox.warning(self, "Error al Guardar", "No se pudo guardar el orden en la base de datos.")
                        except AttributeError:
                            QMessageBox.warning(self,"Falta Método DB", "El db_adapter no tiene 'guardar_orden_documentos'. El orden solo se guardó en memoria.")
                        except Exception as e_db:
                            QMessageBox.critical(self, "Error DB", f"Error guardando orden en BD:\n{e_db}")
                    elif not self.licitacion.id:
                        QMessageBox.information(self,"Orden en Memoria","El orden se aplicó. Se guardará en la BD la próxima vez que guarde la licitación completa.")


                    # Opcional: Refrescar alguna vista si es necesario (ej: si se muestra el orden en otro lugar)
                    # self.load_data()

                else:
                    print("Ordenación cancelada por el usuario.")

            except ImportError:
                QMessageBox.warning(self, "Archivo Faltante", "No se encontró el archivo 'ordenar_documentos_dialog.py'.")
            except Exception as e:
                QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error al ordenar documentos:\n{e}")
                print(f"Error detallado en _ordenar_docs: {e}")

    def _generar_expediente_pdf(self):
        QMessageBox.information(self, "Próximamente", "Generar Expediente PDF (a implementar).")
        # Lógica similar a Tkinter:
        # 1. Abrir diálogo de orden (adaptado a PyQt6)
        # 2. Guardar orden en DB
        # 3. Pedir carpeta destino (QFileDialog.getExistingDirectory)
        # 4. Llamar a la función generar_expediente_pdf (que ya tienes)
        # 5. Mostrar resultado y opción de abrir

    def _generar_expediente_zip(self):
        QMessageBox.information(self, "Próximamente", "Generar ZIP por Categoría (a implementar).")
        # Lógica similar a Tkinter:
        # 1. Abrir diálogo de orden (adaptado a PyQt6)
        # 2. Guardar orden en DB
        # 3. Pedir carpeta destino (QFileDialog.getExistingDirectory)
        # 4. Llamar a la función generar_expediente_zip_por_categoria (que ya tienes)
        # 5. Mostrar resultado y opción de abrir



    def _abrir_carpeta_destino(self):
        """
        Crea y abre la carpeta 'expedientes' (relativa a la ubicación
        desde donde se ejecuta el script) en el explorador de archivos del sistema.
        """
        try:
            # Usar os.path.abspath asegura que tengamos una ruta completa
            # basada en el directorio de trabajo actual.
            carpeta = os.path.abspath("expedientes")
            
            # Crear la carpeta si no existe (no falla si ya existe)
            os.makedirs(carpeta, exist_ok=True)
            
            print(f"Abriendo carpeta destino: {carpeta}")

            # --- Lógica Moderna de PyQt6 ---
            # QUrl.fromLocalFile se encarga de formatear la ruta
            # correctamente para el sistema operativo (ej: 'file:///C:/...' en Windows)
            url = QUrl.fromLocalFile(carpeta)
            
            # QDesktopServices.openUrl es la forma multiplataforma
            # de abrir archivos, carpetas o URLs web.
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "Error al Abrir",
                                    f"No se pudo abrir la carpeta del explorador en:\n{carpeta}")
            # --- Fin Lógica PyQt6 ---

        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado",
                                 f"Ocurrió un error al intentar abrir la carpeta:\n{e}")
            print(f"Error detallado en _abrir_carpeta_destino: {e}")

    def _validar_faltantes(self):
        """Revisa qué documentos de la licitación no tienen archivo adjunto."""
        docs_sin_archivo = [
            f"- [{getattr(d, 'codigo', 'S/C')}] {getattr(d, 'nombre', 'Sin Nombre')}"
            for d in self.licitacion.documentos_solicitados
            if not getattr(d, 'ruta_archivo', '')
        ]

        if not self.licitacion.documentos_solicitados:
             msg = "No hay documentos cargados en esta licitación."
             QMessageBox.information(self, "Validación", msg)
        elif not docs_sin_archivo:
             msg = "¡Todos los documentos tienen un archivo adjunto!"
             QMessageBox.information(self, "Validación Completa", msg)
        else:
             num_faltantes = len(docs_sin_archivo)
             msg = f"Faltan archivos adjuntos para {num_faltantes} documento(s):\n\n"
             msg += "\n".join(docs_sin_archivo[:15]) # Mostrar los primeros 15
             if num_faltantes > 15:
                 msg += f"\n... y {num_faltantes - 15} más."
             QMessageBox.warning(self, "Archivos Faltantes", msg)

    def _abrir_historial_subsanacion(self):
         QMessageBox.information(self, "Próximamente", "Ver Historial de Subsanaciones (a implementar).")
         # try:
         #     # Asume que HistorialSubsanacionDialog existe
         #     dlg = HistorialSubsanacionDialog(self, self.licitacion, self.db)
         #     dlg.exec()
         # except Exception as e:
         #     QMessageBox.critical(self, "Error", f"No se pudo abrir el historial:\n{e}")

    def _abrir_visor_docs(self):
            """Abre el diálogo visor de checklist de documentos."""
            print("Abriendo Visor de Documentos...")
            try:
                # Obtener categorías (considera obtenerlas una vez en __init__ si no cambian)
                categorias = DEFAULT_CATEGORIES # Usar las definidas o self.db.get_categorias() si lo tienes
                dlg = VisorDocumentosDialog(self, self.licitacion, categorias)
                dlg.exec() # Muestra el diálogo modal
                print("Visor de Documentos cerrado.")
                # No se necesita recargar datos aquí ya que el visor es de solo lectura
            except ImportError:
                QMessageBox.warning(self, "Archivo Faltante", "No se encontró el archivo 'visor_documentos_dialog.py'.")
            except Exception as e:
                QMessageBox.critical(self, "Error al Abrir Visor", f"No se pudo abrir el visor de documentos:\n{e}")
                print(f"Error detallado abriendo visor: {e}")


    def _generar_expediente_pdf(self):
        """
        Permite ordenar documentos, selecciona categorías y genera un PDF
        por cada categoría seleccionada en la carpeta destino elegida.
        """
        print("Iniciando generación de Expediente(s) PDF...")
        if not self.licitacion.documentos_solicitados:
            QMessageBox.warning(self, "Sin Documentos", "Esta licitación no tiene documentos cargados.")
            return
        # Es crucial tener el ID para guardar el orden en la BD
        if not self.licitacion.id:
             QMessageBox.warning(self, "Licitación no Guardada", "Guarde la licitación al menos una vez antes de generar expedientes.")
             return

        # 1. Abrir diálogo de ordenación
        try:
            # Pasar la lista de documentos y el ID/Adapter para persistencia opcional
            dlg_orden = DialogoOrdenarDocumentos(
                parent=self,
                documentos_actuales=self.licitacion.documentos_solicitados,
                # --- PASAR ID Y ADAPTER ---
                licitacion_id=self.licitacion.id,
                db_adapter=self.db
                # --- FIN ---
            )

            result = dlg_orden.exec() # Muestra modal

            if result != QDialog.DialogCode.Accepted:
                print("Generación PDF cancelada en diálogo de orden.")
                return # Usuario canceló

            orden_por_categoria: Dict[str, List[Documento]] | None = dlg_orden.get_orden_documentos()
            incluir_categorias: Dict[str, bool] | None = dlg_orden.get_inclusion_categorias()

            if orden_por_categoria is None or incluir_categorias is None:
                 QMessageBox.warning(self,"Cancelado","No se obtuvo orden válido del diálogo.")
                 return

            # --- El diálogo ahora guarda el orden directamente ---
            # No necesitamos guardar el orden aquí de nuevo,
            # pero sí debemos actualizar la lista en memoria si cambió.
            print("Orden confirmado/modificado. Actualizando lista en memoria...")
            documentos_actualizados_memoria = []
            orden_global = 1
            for cat_name in CATEGORIAS_EXPEDIENTE: # Usar la misma lista que el diálogo
                 lista_ordenada_cat = orden_por_categoria.get(cat_name, [])
                 for doc in lista_ordenada_cat:
                      setattr(doc, 'orden_pliego', orden_global) # Actualizar atributo
                      documentos_actualizados_memoria.append(doc)
                      orden_global += 1
            # Reconstruir lista principal manteniendo los no categorizados
            docs_no_categorizados = [d for d in self.licitacion.documentos_solicitados if getattr(d, 'categoria', 'Otros') not in CATEGORIAS_EXPEDIENTE]
            self.licitacion.documentos_solicitados = documentos_actualizados_memoria + docs_no_categorizados
            print(f"Orden 'orden_pliego' actualizado en memoria para {len(documentos_actualizados_memoria)} documentos.")


        except ImportError:
             QMessageBox.critical(self, "Error", "No se encontró el diálogo 'DialogoOrdenarDocumentos'.")
             return
        except Exception as e_dlg:
             QMessageBox.critical(self, "Error Diálogo Orden", f"Falló al abrir o usar el diálogo de orden:\n{e_dlg}")
             print(f"Error detallado abriendo DialogoOrdenarDocumentos: {e_dlg}")
             return

        # 2. Pedir carpeta de destino
        # Sugerir última carpeta usada o carpeta de documentos
        last_dir = QSettings("Zoeccivil", "Licitaciones").value("Paths/last_pdf_export_dir", os.path.expanduser("~"))
        carpeta_destino = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Salida para los PDF", last_dir)
        if not carpeta_destino:
            print("Selección de carpeta cancelada.")
            return
        # Guardar última carpeta usada
        QSettings("Zoeccivil", "Licitaciones").setValue("Paths/last_pdf_export_dir", carpeta_destino)


        # 3. Generar un PDF por cada categoría incluida
        generados = []
        errores = []
        categorias_a_procesar = CATEGORIAS_EXPEDIENTE # Usar la lista definida

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) # Cursor de espera

        try: # Envolver el bucle en try/finally para restaurar cursor
            for cat_name in categorias_a_procesar:
                if not incluir_categorias.get(cat_name, False):
                    print(f"Categoría '{cat_name}' no incluida, saltando.")
                    continue

                docs_cat_ordenados = orden_por_categoria.get(cat_name, [])
                if not docs_cat_ordenados:
                    print(f"Categoría '{cat_name}' sin documentos, saltando.")
                    continue

                nombre_archivo = f"Expediente_{cat_name}_{self.licitacion.numero_proceso}.pdf"
                nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in (' ', '.', '-', '_')).rstrip()
                out_path = os.path.join(carpeta_destino, nombre_archivo)

                meta = {
                    'titulo_expediente': f"Expediente {cat_name} - {self.licitacion.numero_proceso}",
                    'creado_por': os.getenv("USERNAME", "Usuario"),
                    'qr_text': f"{self.licitacion.numero_proceso}|{self.licitacion.institucion}|{cat_name}"
                }

                print(f"Generando PDF para '{cat_name}' en: {out_path}...")
                try:
                    # Llamar a la función del módulo pdf_generator
                    exito_pdf, mensaje_pdf = generar_pdf_expediente_categoria(
                         documentos_categoria=docs_cat_ordenados,
                         ruta_salida=out_path,
                         licitacion_info=self.licitacion, # Pasar objeto completo
                         metadata=meta
                    )

                    if exito_pdf:
                        print(f"PDF para '{cat_name}' generado con éxito.")
                        generados.append(out_path)
                    else:
                        print(f"Error generando PDF para '{cat_name}': {mensaje_pdf}")
                        errores.append(f"- {cat_name}: {mensaje_pdf}")

                except ImportError:
                     msg = "Falta el módulo 'pdf_generator' o sus dependencias (PyPDF2, reportlab, qrcode)."
                     print(f"ERROR: {msg}")
                     errores.append(f"- {cat_name}: {msg}")
                     QMessageBox.critical(self, "Error Crítico", msg)
                     break # Detener si falta la función principal
                except Exception as e_gen:
                    msg = f"Error inesperado generando PDF para '{cat_name}': {e_gen}"
                    print(f"ERROR: {msg}")
                    logging.exception(msg)
                    errores.append(f"- {cat_name}: {e_gen}")

        finally:
            QApplication.restoreOverrideCursor() # Restaurar cursor normal


        # 4. Mostrar Resultados
        if generados:
            msg_exito = f"✅ {len(generados)} Archivo(s) PDF generados con éxito en:\n{carpeta_destino}\n\n"
            msg_exito += "\n".join([f"- {os.path.basename(p)}" for p in generados])
            if errores:
                 msg_exito += "\n\n⚠️ Ocurrieron errores en algunas categorías:\n" + "\n".join(errores)
            QMessageBox.information(self, "Generación Completa", msg_exito)

            # 5. Opción de Previsualizar (usando utils.previsualizar_archivo)
            if QMessageBox.question(self, "Abrir Archivo", f"¿Desea abrir el último PDF generado?\n({os.path.basename(generados[-1])})",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
                try:
                    previsualizar_archivo(generados[-1]) # Llamar a la función de utils
                except ImportError:
                    QMessageBox.warning(self, "Falta Función", "No se encontró la función 'previsualizar_archivo' en utils.")
                except Exception as e_prev:
                    QMessageBox.critical(self, "Error al Previsualizar", f"No se pudo abrir el archivo:\n{e_prev}")
        elif errores:
            QMessageBox.critical(self, "Error en Generación", "No se pudo generar ningún PDF debido a los siguientes errores:\n\n" + "\n".join(errores))
        else:
             QMessageBox.warning(self, "Sin Salida", "No se generó ningún PDF. Verifique que seleccionó categorías y que estas tenían documentos.")



    def _generar_expediente_zip(self):
        """
        Permite ordenar documentos, selecciona categorías y genera un ZIP
        por cada categoría seleccionada en la carpeta destino elegida.
        """
        print("Iniciando generación de Expediente(s) ZIP...")
        if not self.licitacion.documentos_solicitados:
            QMessageBox.warning(self, "Sin Documentos", "Esta licitación no tiene documentos cargados.")
            return
        if not self.licitacion.id:
             QMessageBox.warning(self, "Licitación no Guardada", "Guarde la licitación al menos una vez antes de generar expedientes.")
             return

        # 1. Abrir diálogo de ordenación (igual que en PDF)
        try:
            dlg_orden = DialogoOrdenarDocumentos(
                parent=self,
                documentos_actuales=self.licitacion.documentos_solicitados,
                licitacion_id=self.licitacion.id,
                db_adapter=self.db
            )
            if dlg_orden.exec() != QDialog.DialogCode.Accepted:
                print("Generación ZIP cancelada en diálogo de orden.")
                return

            orden_por_categoria: Dict[str, List[Documento]] | None = dlg_orden.get_orden_documentos()
            incluir_categorias: Dict[str, bool] | None = dlg_orden.get_inclusion_categorias()

            if orden_por_categoria is None or incluir_categorias is None:
                 QMessageBox.warning(self,"Cancelado","No se obtuvo orden válido del diálogo.")
                 return

            # --- El diálogo ya guardó el orden en la BD (si se configuró) ---
            # --- y actualizó los atributos 'orden_pliego' en memoria ---
            # Actualizar la lista principal en memoria (igual que en PDF)
            documentos_actualizados_memoria = []
            orden_global = 1
            categorias_a_procesar = CATEGORIAS_EXPEDIENTE # Usar la lista definida
            for cat_name in categorias_a_procesar:
                 lista_ordenada_cat = orden_por_categoria.get(cat_name, [])
                 for doc in lista_ordenada_cat:
                      setattr(doc, 'orden_pliego', orden_global) # Asegurar que el objeto tenga el orden
                      documentos_actualizados_memoria.append(doc)
                      orden_global += 1
            
            docs_no_categorizados = [d for d in self.licitacion.documentos_solicitados if getattr(d, 'categoria', 'Otros') not in categorias_a_procesar]
            self.licitacion.documentos_solicitados = documentos_actualizados_memoria + docs_no_categorizados
            print(f"Orden 'orden_pliego' actualizado en memoria para {len(documentos_actualizados_memoria)} documentos.")
            # No es necesario llamar a db.guardar_orden_documentos aquí si el diálogo ya lo hizo

        except ImportError:
             QMessageBox.critical(self, "Error", "No se encontró el diálogo 'DialogoOrdenarDocumentos'.")
             return
        except Exception as e_dlg:
             QMessageBox.critical(self, "Error Diálogo Orden", f"Falló al abrir o usar el diálogo de orden:\n{e_dlg}")
             print(f"Error detallado abriendo DialogoOrdenarDocumentos: {e_dlg}")
             return

        # 2. Pedir carpeta de destino
        settings = QSettings("Zoeccivil", "Licitaciones")
        last_dir = settings.value("Paths/last_zip_export_dir", os.path.expanduser("~"))
        carpeta_destino = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Salida para los ZIPs", last_dir)
        if not carpeta_destino:
            print("Selección de carpeta cancelada.")
            return
        settings.setValue("Paths/last_zip_export_dir", carpeta_destino) # Guardar última carpeta

        # 3. Generar un ZIP por categoría
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) # Cursor de espera
        try:
            # Llamar a la función de lógica
            exito_general, generados, errores = generar_expediente_zip_por_categoria(
                licitacion=self.licitacion,
                carpeta_salida=carpeta_destino,
                orden_por_cat=orden_por_categoria,
                incluir=incluir_categorias,
                categorias_orden=categorias_a_procesar
            )
        except ImportError:
             QMessageBox.critical(self, "Error Crítico", "Falta el módulo 'zip_generator' o sus dependencias (csv, zipfile).")
             exito_general, generados, errores = False, [], ["Error de importación."]
        except Exception as e_gen:
            msg = f"Error inesperado generando ZIPs: {e_gen}"
            print(f"ERROR: {msg}")
            logging.exception(msg)
            exito_general, generados, errores = False, [], [msg]
        finally:
            QApplication.restoreOverrideCursor() # Restaurar cursor

        # 4. Mostrar Resultados
        if exito_general:
            msg_exito = f"✅ {len(generados)} Archivo(s) ZIP generados con éxito en:\n{carpeta_destino}\n\n"
            msg_exito += "\n".join([f"- {os.path.basename(p)}" for p in generados])
            if errores:
                 msg_exito += "\n\n⚠️ Ocurrieron errores en algunas categorías:\n" + "\n".join(errores)
            QMessageBox.information(self, "Generación Completa", msg_exito)

            # 5. Opción de Abrir Carpeta
            if QMessageBox.question(self, "Abrir Carpeta", "¿Desea abrir la carpeta de salida?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
                try:
                    print(f"Intentando abrir carpeta: {carpeta_destino}")
                    if not QDesktopServices.openUrl(QUrl.fromLocalFile(carpeta_destino)):
                         QMessageBox.warning(self,"Error al Abrir", f"No se pudo abrir la carpeta:\n{carpeta_destino}")
                except Exception as e_open:
                    QMessageBox.critical(self, "Error Inesperado", f"No se pudo abrir la carpeta:\n{e_open}")
        elif errores:
            QMessageBox.critical(self, "Error en Generación", "No se pudo generar ningún ZIP debido a los siguientes errores:\n\n" + "\n".join(errores))
        else:
             QMessageBox.warning(self, "Sin Salida", "No se generó ningún ZIP. Verifique que seleccionó categorías y que estas tenían documentos.")

    def _abrir_historial_subsanacion(self):
        """
        Abre el diálogo para ver el historial de subsanaciones.
        """
        print("Abriendo Historial de Subsanaciones...")
        
        # Verificar que la licitación ya esté guardada (tenga un ID)
        if not self.licitacion or not self.licitacion.id:
             QMessageBox.warning(self, "Licitación no Guardada",
                                 "Debe guardar la licitación al menos una vez para poder ver su historial de subsanaciones.")
             return
             
        try:
            # Crear y ejecutar el diálogo
            dlg = HistorialSubsanacionDialog(self, self.licitacion, self.db)
            dlg.exec() # Muestra el diálogo modal
            print("Historial de Subsanaciones cerrado.")
            
        except ImportError:
            QMessageBox.critical(self, "Archivo Faltante",
                                 "No se encontró el archivo 'historial_subsanacion_dialog.py'.")
        except AttributeError as e:
             # Esto pasará si 'obtener_historial_subsanacion' no existe en el db_adapter
            if "'obtener_historial_subsanacion'" in str(e):
                 QMessageBox.critical(self, "Función Faltante",
                                      "El método 'obtener_historial_subsanacion' no existe en el DatabaseAdapter.")
                 print(f"ERROR: {e}")
            else:
                 QMessageBox.critical(self, "Error de Atributo", f"Ocurrió un error:\n{e}")
                 print(f"Error detallado abriendo historial: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado",
                                 f"No se pudo abrir el historial de subsanaciones:\n{e}")
            print(f"Error detallado abriendo historial: {e}")