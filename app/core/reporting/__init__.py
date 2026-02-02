"""
Reporting package - Motor de reportes, KPIs y generación de documentos.
"""
from app.core.reporting.report_generator import ReportGenerator

# Importar ReportingEngine desde el archivo reporting.py del nivel superior
import sys
from pathlib import Path

# Obtener el path del archivo reporting.py
core_path = Path(__file__).parent.parent
reporting_file = core_path / "reporting.py"

if reporting_file.exists():
    # Importar dinámicamente
    import importlib.util
    spec = importlib.util.spec_from_file_location("reporting_core", str(reporting_file))
    reporting_core = importlib.util.module_from_spec(spec)
    sys.modules["reporting_core"] = reporting_core
    spec.loader.exec_module(reporting_core)
    
    # Exportar ReportingEngine
    ReportingEngine = reporting_core.ReportingEngine
    print("[INFO] ReportingEngine cargado desde app/core/reporting.py")  # ✅ Sin emoji
else:
    print(f"[WARNING] No se encontro {reporting_file}")  # ✅ Sin emoji
    
    # Clase fallback
    class ReportingEngine:
        """Fallback cuando no se encuentra el módulo."""
        def __init__(self, db_adapter):
            self.db = db_adapter
        
        def calculate_kpis(self, **kwargs):
            from app.core.reporting.report_generator import ReportKPIs
            return ReportKPIs()
        
        def export_to_excel(self, **kwargs):
            return False
        
        def generate_monthly_report(self, year, month):
            return {}

__all__ = ["ReportGenerator", "ReportingEngine"]