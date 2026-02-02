"""
Modern Main Entry Point - Punto de entrada para la UI moderna.
Inicializa la aplicación con tema Titanium Construct v2 y base de datos.
Incluye diálogo de configuración de Firebase automático.
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget
from PyQt6.QtCore import Qt

# Asegurar que el directorio raíz esté en el path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.theme.titanium_construct_v2 import apply_titanium_construct_v2
from app.ui.windows.modern_main_window import ModernMainWindow
from app.ui.dialogs.firebase_config_dialog import show_firebase_config_dialog
from app.core import lic_config


def _initialize_firebase() -> Optional[object]:
    """
    Inicializa Firebase si el backend es Firestore.

    Estrategia: 
    1. Intentar credenciales desde configuración propia (lic_config) si existe. 
    2. Intentar GOOGLE_APPLICATION_CREDENTIALS. 
    3. Intentar JSON en LICITACIONES_FIRESTORE_KEY_JSON.
    4. Si nada funciona, abrir diálogo de configuración de Firebase. 

    Returns:
        Cliente de Firestore o None si no se puede inicializar.
    """
    print(f"[Firebase] Buscando configuración en: {lic_config.get_config_path_for_display()}")
    
    from firebase_admin import App, credentials, firestore, initialize_app
    from app.core import firebase_adapter

    load_dotenv()

    credentials_path: Optional[str] = None

    # 1) Intentar leer desde configuración propia (lic_config)
    try:
        cfg_cred_path, cfg_bucket = lic_config.get_firebase_config()
        if cfg_cred_path: 
            credentials_path = cfg_cred_path
            print(f"[Firebase] ✓ Credenciales encontradas en lic_config: {cfg_cred_path}")
    except Exception as e: 
        print(f"[Firebase] ⚠ No se pudo leer lic_config: {e}")

    # 2) Intentar variable de entorno GOOGLE_APPLICATION_CREDENTIALS
    if not credentials_path:
        env_cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_cred:
            credentials_path = env_cred
            print(f"[Firebase] ✓ Usando GOOGLE_APPLICATION_CREDENTIALS: {env_cred}")

    # 3) Intentar JSON directo en LICITACIONES_FIRESTORE_KEY_JSON
    json_key = os.getenv("LICITACIONES_FIRESTORE_KEY_JSON")

    cred: Optional[credentials.Certificate] = None

    if credentials_path and os.path.exists(credentials_path):
        # Usar archivo de credenciales
        cred = credentials.Certificate(credentials_path)
        print(f"[Firebase] ✓ Credenciales cargadas desde archivo: {credentials_path}")
    elif json_key:
        # Usar JSON embebido en variable de entorno
        try:
            cred_data = json.loads(json_key)
            cred = credentials.Certificate(cred_data)
            print("[Firebase] ✓ Credenciales cargadas desde variable de entorno JSON")
        except Exception as e: 
            print(f"[Firebase] ✗ Error al parsear LICITACIONES_FIRESTORE_KEY_JSON: {e}")
            cred = None

    # 4) Si aún no tenemos credenciales, abrir diálogo de configuración
    if cred is None:
        print("[Firebase] ⚠ No se encontraron credenciales, abriendo diálogo de configuración...")
        
        # Asegurarnos de que exista una QApplication
        app = QApplication.instance()
        if app is None: 
            app = QApplication(sys.argv)
            apply_titanium_construct_v2(app)

        parent = QWidget()
        parent.hide()

        configured = show_firebase_config_dialog(parent=parent)
        
        if not configured: 
            QMessageBox.warning(
                parent,
                "Firebase No Configurado",
                (
                    "No se encontraron credenciales de Firebase y la configuración "
                    "fue cancelada.\n\n"
                    "La aplicación continuará sin conexión a la base de datos.\n"
                    "Algunas funciones pueden no estar disponibles."
                ),
            )
            return None

        # Reintentar obtener credenciales desde la config guardada
        try:
            credentials_path, _bucket = lic_config.get_firebase_config()
            print(f"[Firebase] ✓ Credenciales obtenidas después del diálogo: {credentials_path}")
        except Exception as e:
            print(f"[Firebase] ✗ Error leyendo lic_config después del diálogo: {e}")
            credentials_path = None

        if credentials_path and os.path.exists(credentials_path):
            cred = credentials.Certificate(credentials_path)
            # Setear variable de entorno para otras librerías
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"[Firebase] ✓ GOOGLE_APPLICATION_CREDENTIALS seteada: {credentials_path}")
        else:
            QMessageBox.critical(
                parent,
                "Error de Configuración",
                "No se pudo obtener una ruta de credenciales válida tras la configuración."
            )
            return None

    # Opciones de inicialización (projectId opcional)
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    options = {"projectId": project_id} if project_id else None

    try:
        app_fb: Optional[App] = initialize_app(cred, options)
        print("[Firebase] ✓ Firebase inicializado correctamente")
    except ValueError: 
        # App ya inicializada; reutilizar instancia por defecto
        app_fb = None
        print("[Firebase] ℹ Firebase ya estaba inicializado, reutilizando instancia")

    client = firestore.client(app_fb)
    
    # Configurar cliente en el adaptador
    from app.core import firebase_adapter
    firebase_adapter.set_client(client)
    
    print("[Firebase] ✓ Cliente Firestore configurado y listo")
    return client


def initialize_database():
    """
    Inicializa el adaptador de base de datos según la configuración.
    
    Returns:
        DatabaseAdapter configurado y abierto, o None si falla.
    """
    from app.core.db_adapter_selector import get_database_adapter
    
    load_dotenv()
    backend = os.getenv("APP_DB_BACKEND", "firestore").lower()
    
    print(f"[INFO] Backend configurado: {backend}")
    
    # Inicializar cliente según backend
    db_client = None
    
    if backend == "firestore":
        db_client = _initialize_firebase()
        
        if not db_client:
            print("[ERROR] No se pudo inicializar Firebase")
            return None
    
    # Crear adaptador de base de datos
    try:
        print(f"[INFO] Inicializando adaptador de base de datos para: {backend}")
        db = get_database_adapter(db_client=db_client)
        db.open()
        
        backend_names = {
            "firestore": "Firebase Firestore",
            "sqlite": "SQLite Local",
            "mysql": "MySQL"
        }
        
        print(f"[INFO] ✓ Conexión a {backend_names.get(backend, backend)} establecida correctamente")
        return db
        
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar {backend}: {e}")
        
        # Mostrar diálogo de error detallado
        error_msg = f"No se pudo inicializar la conexión al backend '{backend}'.\n\n"
        
        if backend == "firestore":
            error_msg += (
                "Posibles causas:\n"
                "• Falta el archivo de credenciales de Firebase\n"
                "• Variable GOOGLE_APPLICATION_CREDENTIALS no configurada\n"
                "• Credenciales inválidas o expiradas\n"
                "• Error de permisos en Firestore\n\n"
                "Solución:\n"
                "1. Descarga las credenciales desde Firebase Console\n"
                "2. Configúralas en 'Archivo > Configurar Firebase'\n"
                "3. O edita manualmente 'lic_config.json'\n"
                "4. Verifica que el proyecto tenga Firestore habilitado"
            )
        elif backend == "sqlite":
            error_msg += (
                "Posibles causas:\n"
                "• Ruta del archivo de base de datos inválida\n"
                "• Permisos de escritura insuficientes\n"
                "• Archivo corrupto\n\n"
                "Verifica la variable SQLITE_DB_PATH en el archivo .env"
            )
        elif backend == "mysql":
            error_msg += (
                "Posibles causas:\n"
                "• Servidor MySQL no disponible\n"
                "• Credenciales incorrectas\n"
                "• Base de datos no existe\n"
                "• Firewall bloqueando conexión\n\n"
                "Verifica las variables MYSQL_* en el archivo .env"
            )
        
        error_msg += f"\n\nError técnico:\n{str(e)}"
        
        import traceback
        error_msg += f"\n\nTraceback:\n{traceback.format_exc()}"
        
        QMessageBox.critical(
            None,
            "Error de Base de Datos",
            error_msg
        )
        
        return None


def show_splash_screen(app):
    """
    Muestra una pantalla de carga opcional.
    
    Args:
        app: Instancia de QApplication
    
    Returns:
        Splash screen widget o None
    """
    try:
        from PyQt6.QtWidgets import QSplashScreen
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
        from PyQt6.QtCore import Qt, QRect
        
        # Crear pixmap con degradado
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor("#1E1E1E"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Degradado de fondo
        gradient = QLinearGradient(0, 0, 600, 400)
        gradient.setColorAt(0, QColor("#1E1E1E"))
        gradient.setColorAt(1, QColor("#2D2D30"))
        painter.fillRect(pixmap.rect(), gradient)
        
        # Título
        painter.setPen(QColor("#7C4DFF"))
        font = QFont("Segoe UI", 32, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            pixmap.rect().adjusted(0, -50, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            "GESTOR DE\nLICITACIONES"
        )
        
        # Subtítulo
        painter.setPen(QColor("#B0B0B0"))
        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            pixmap.rect().adjusted(0, 100, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            "Modern UI Edition v4.0"
        )
        
        # Mensaje de carga
        painter.setPen(QColor("#7C4DFF"))
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            pixmap.rect().adjusted(0, 150, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            "Inicializando..."
        )
        
        # Versión en esquina
        painter.setPen(QColor("#6B7280"))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(
            pixmap.rect().adjusted(0, 0, -20, -20),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
            "v4.0.0"
        )
        
        painter.end()
        
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
        
        return splash
        
    except Exception as e:
        print(f"[WARNING] No se pudo mostrar splash screen: {e}")
        return None


def main():
    """
    Punto de entrada principal de la aplicación.
    """
    # Cargar variables de entorno
    load_dotenv()
    
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Gestor de Licitaciones")
    app.setOrganizationName("Zoeccivil")
    app.setOrganizationDomain("zoeccivil.com")
    
    # Aplicar tema moderno
    try:
        apply_titanium_construct_v2(app)
        print("[INFO] ✓ Tema Titanium Construct v2 aplicado")
    except Exception as e:
        print(f"[WARNING] No se pudo aplicar tema: {e}")
    
    # Mostrar splash (opcional)
    splash = show_splash_screen(app)
    
    # Pequeña pausa para que se vea el splash
    app.processEvents()
    
    # Inicializar base de datos (incluye diálogo de Firebase si es necesario)
    db = initialize_database()
    
    if not db:
        # Si falla la inicialización, cerrar splash
        if splash:
            splash.close()
        
        # Preguntar si quiere intentar configurar de nuevo
        reply = QMessageBox.question(
            None,
            "Configuración Requerida",
            "¿Desea intentar configurar Firebase nuevamente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reintentar configuración
            try:
                parent = QWidget()
                parent.hide()
                
                if show_firebase_config_dialog(parent=parent):
                    QMessageBox.information(
                        None,
                        "Configuración Guardada",
                        "Reinicie la aplicación para aplicar los cambios."
                    )
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "Error",
                    f"No se pudo abrir el diálogo de configuración:\n{e}"
                )
        
        return sys.exit(1)
    
    # Crear ventana principal
    try:
        window = ModernMainWindow(db=db)
        
        # Cerrar splash antes de mostrar ventana
        if splash:
            splash.finish(window)
        
        window.show()
        
        print("[INFO] ✓ Aplicación iniciada correctamente")
        
    except Exception as e:
        if splash:
            splash.close()
        
        QMessageBox.critical(
            None,
            "Error de Inicialización",
            f"No se pudo iniciar la aplicación:\n\n{e}"
        )
        
        import traceback
        traceback.print_exc()
        
        return sys.exit(1)
    
    # Ejecutar aplicación
    return_code = app.exec()
    
    # Limpiar
    if db:
        try:
            db.close()
            print("[INFO] ✓ Conexión a base de datos cerrada correctamente")
        except Exception as e:
            print(f"[WARNING] Error al cerrar base de datos: {e}")
    
    sys.exit(return_code)


if __name__ == "__main__":
    main()