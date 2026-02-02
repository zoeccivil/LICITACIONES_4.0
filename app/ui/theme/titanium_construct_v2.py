"""
Titanium Construct v2 - Modern Dark PyQt6 Theme
Professional dark theme with purple accent (#7C4DFF) for dashboard applications.
Based on the Titanium Construct design system.
"""
from __future__ import annotations
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


# Titanium Construct v2 Color Palette (Dark Theme)
BACKGROUND = QColor("#1E1E1E")       # Main background
SURFACE = QColor("#2D2D30")          # Surface/card background
SURFACE_HOVER = QColor("#3E3E42")    # Hover state
BORDER = QColor("#3E3E42")           # Borders
PRIMARY = QColor("#7C4DFF")          # Purple accent
PRIMARY_HOVER = QColor("#651FFF")    # Darker purple for hover
TEXT = QColor("#FFFFFF")             # Primary text
TEXT_MUTED = QColor("#B0B0B0")       # Secondary text

# Semantic Colors
SUCCESS = QColor("#00C853")          # Green
WARNING = QColor("#FFAB00")          # Orange
ERROR = QColor("#D50000")            # Red
DANGER = QColor("#FF5252")           # Bright red
INFO = QColor("#448AFF")             # Blue

THEME_NAME = "Titanium Construct v2"


class TitaniumStyle:
    """
    Clase que provee estilos QSS para el tema Titanium Construct v2.
    """
    
    @staticmethod
    def get_stylesheet() -> str:
        """
        Retorna el stylesheet completo (QSS) para aplicar el tema.
        
        Returns:
            str: Qt Style Sheet con todos los estilos del tema.
        """
        return """
/* ===================================================================
   TITANIUM CONSTRUCT V2 - DARK THEME
   Professional dark theme with purple accent
   =================================================================== */

/* === BASE & RESET === */
QWidget {
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 13px;
    color: #FFFFFF;
    background-color: #1E1E1E;
}

QMainWindow, QDialog {
    background-color: #1E1E1E;
}

/* === FRAMES & CONTAINERS === */
QFrame {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    border-radius: 8px;
}

QGroupBox {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    border-radius: 8px;
    margin-top: 1.2em;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #7C4DFF;
    font-weight: bold;
    font-size: 13px;
    left: 10px;
}

/* === BUTTONS === */
QPushButton {
    background-color: #7C4DFF;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #651FFF;
}

QPushButton:pressed {
    background-color: #5E35B1;
}

QPushButton:disabled {
    background-color: #3E3E42;
    color: #6B7280;
}

/* Secondary Button Style */
QPushButton[class="secondary"] {
    background-color: transparent;
    border: 1px solid #3E3E42;
    color: #FFFFFF;
}

QPushButton[class="secondary"]:hover {
    border-color: #B0B0B0;
    background-color: #3E3E42;
}

/* === INPUT FIELDS === */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #121212;
    border: 1px solid #3E3E42;
    border-radius: 6px;
    padding: 8px 12px;
    color: #FFFFFF;
    selection-background-color: #7C4DFF;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #7C4DFF;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #2D2D30;
    color: #6B7280;
}

/* === COMBO BOX === */
QComboBox {
    background-color: #121212;
    border: 1px solid #3E3E42;
    border-radius: 6px;
    padding: 8px 12px;
    color: #FFFFFF;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #7C4DFF;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #B0B0B0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    selection-background-color: #7C4DFF;
    selection-color: #FFFFFF;
    color: #FFFFFF;
}

/* === TABLES === */
QTableWidget, QTableView {
    background-color: #2D2D30;
    alternate-background-color: #252526;
    gridline-color: #3E3E42;
    border: 1px solid #3E3E42;
    border-radius: 8px;
    selection-background-color: rgba(124, 77, 255, 0.2);
    selection-color: #FFFFFF;
}

QTableWidget::item, QTableView::item {
    padding: 8px;
    border: none;
}

QTableWidget::item:hover, QTableView::item:hover {
    background-color: #3E3E42;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(124, 77, 255, 0.3);
}

QHeaderView::section {
    background-color: #252526;
    color: #B0B0B0;
    padding: 12px 15px;
    border: none;
    border-bottom: 1px solid #3E3E42;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QHeaderView::section:hover {
    background-color: #2D2D30;
}

/* === SCROLLBARS === */
QScrollBar:vertical {
    background-color: #1E1E1E;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3E3E42;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4E4E52;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1E1E1E;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #3E3E42;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4E4E52;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* === TABS === */
QTabWidget::pane {
    border: 1px solid #3E3E42;
    background-color: #2D2D30;
    border-radius: 8px;
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
    position: relative;
}

QTabBar::tab:hover:!selected {
    background-color: #3E3E42;
    color: #FFFFFF;
}

/* === PROGRESS BAR === */
QProgressBar {
    background-color: #121212;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #448AFF;
    border-radius: 3px;
}

/* === LABELS === */
QLabel {
    background-color: transparent;
    color: #FFFFFF;
}

/* === MENU BAR === */
QMenuBar {
    background-color: #2D2D30;
    border-bottom: 1px solid #3E3E42;
    color: #FFFFFF;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #3E3E42;
}

QMenuBar::item:pressed {
    background-color: #7C4DFF;
}

/* === MENU === */
QMenu {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
    color: #FFFFFF;
}

QMenu::item:selected {
    background-color: #7C4DFF;
}

QMenu::separator {
    height: 1px;
    background-color: #3E3E42;
    margin: 4px 8px;
}

/* === TOOLBAR === */
QToolBar {
    background-color: #2D2D30;
    border: none;
    border-bottom: 1px solid #3E3E42;
    spacing: 6px;
    padding: 4px;
}

QToolBar::separator {
    background-color: #3E3E42;
    width: 1px;
    margin: 4px 8px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
    color: #FFFFFF;
}

QToolButton:hover {
    background-color: #3E3E42;
}

QToolButton:pressed {
    background-color: #7C4DFF;
}

/* === STATUS BAR === */
QStatusBar {
    background-color: #2D2D30;
    border-top: 1px solid #3E3E42;
    color: #B0B0B0;
}

/* === CHECKBOXES & RADIO BUTTONS === */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #FFFFFF;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 2px solid #3E3E42;
    background-color: #121212;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #7C4DFF;
}

QCheckBox::indicator:checked {
    background-color: #7C4DFF;
    border-color: #7C4DFF;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QRadioButton::indicator:checked {
    background-color: #7C4DFF;
    border-color: #7C4DFF;
}

/* === TOOLTIPS === */
QToolTip {
    background-color: #2D2D30;
    border: 1px solid #7C4DFF;
    color: #FFFFFF;
    padding: 6px;
    border-radius: 4px;
}

/* === SPLITTER === */
QSplitter::handle {
    background-color: #3E3E42;
}

QSplitter::handle:hover {
    background-color: #7C4DFF;
}
"""


def apply_titanium_construct_v2(app: QApplication) -> None:
    """
    Aplica el tema Titanium Construct v2 a la aplicación.
    
    Args:
        app: Instancia de QApplication a la que aplicar el tema.
    """
    # Aplicar stylesheet
    app.setStyleSheet(TitaniumStyle.get_stylesheet())
    
    # Configurar paleta de colores
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, BACKGROUND)
    palette.setColor(QPalette.ColorRole.WindowText, TEXT)
    palette.setColor(QPalette.ColorRole.Base, SURFACE)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252526"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, SURFACE)
    palette.setColor(QPalette.ColorRole.ToolTipText, TEXT)
    palette.setColor(QPalette.ColorRole.Text, TEXT)
    palette.setColor(QPalette.ColorRole.Button, SURFACE)
    palette.setColor(QPalette.ColorRole.ButtonText, TEXT)
    palette.setColor(QPalette.ColorRole.Link, PRIMARY)
    palette.setColor(QPalette.ColorRole.Highlight, PRIMARY)
    palette.setColor(QPalette.ColorRole.HighlightedText, TEXT)
    
    app.setPalette(palette)
