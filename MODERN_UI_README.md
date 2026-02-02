# Modern UI - Titanium Construct v2

Este documento describe la nueva interfaz moderna implementada para el Gestor de Licitaciones.

## 🎨 Características

La nueva UI moderna incluye:

- **Tema Oscuro Profesional**: Basado en Titanium Construct v2 con paleta de colores oscuros y acento morado (#7C4DFF)
- **Navegación con Sidebar**: Barra lateral moderna con iconos y efectos hover
- **Vistas Modulares**: Dashboard y Lista de Licitaciones separadas
- **Componentes Reutilizables**: StatCard, StatusBadge, ModernProgressBar, ModernSidebar
- **Arquitectura Limpia**: Código bien estructurado con type hints y docstrings

## 🚀 Cómo Usar

### Opción 1: Ejecutar la Nueva UI (Recomendado)

Para probar la nueva interfaz moderna, ejecuta:

```bash
python modern_main.py
```

### Opción 2: Ejecutar la UI Antigua

La UI antigua sigue funcionando sin cambios:

```bash
python app/main.py
```

## 📁 Estructura de Archivos Nuevos

```
LICITACIONES_4.0/
├── modern_main.py                          # Nuevo punto de entrada
└── app/
    ├── ui/
    │   ├── theme/
    │   │   └── titanium_construct_v2.py    # Sistema de tema oscuro
    │   ├── widgets/
    │   │   ├── __init__.py
    │   │   └── modern_widgets.py           # Componentes reutilizables
    │   ├── views/
    │   │   ├── dashboard_view.py           # Vista de dashboard con estadísticas
    │   │   └── licitaciones_list_view.py   # Vista de tabla de licitaciones
    │   └── windows/
    │       └── modern_main_window.py       # Ventana principal moderna
```

## 🎯 Componentes

### 1. Tema (titanium_construct_v2.py)

Define la paleta de colores y estilos QSS:

- **Background**: #1E1E1E (fondo principal)
- **Surface**: #2D2D30 (superficies/tarjetas)
- **Primary**: #7C4DFF (acento morado)
- **Success**: #00C853 (verde)
- **Warning**: #FFAB00 (naranja)
- **Error**: #D50000 (rojo)

Uso:
```python
from app.ui.theme.titanium_construct_v2 import apply_titanium_construct_v2

app = QApplication(sys.argv)
apply_titanium_construct_v2(app)
```

### 2. Widgets Modernos (modern_widgets.py)

#### StatCard
Tarjeta de estadística para el dashboard:
```python
card = StatCard(
    title="Total Activas",
    value="8",
    accent_color="#7C4DFF",
    icon_text="📋"
)
```

#### ModernSidebar
Barra lateral de navegación:
```python
sidebar = ModernSidebar()
sidebar.add_navigation_item("dashboard", "Dashboard", "📊", is_active=True)
sidebar.navigation_changed.connect(self._on_navigation_changed)
```

#### StatusBadge
Badge de estado para tablas:
```python
badge = StatusBadge("En curso", status_type="info")
# status_type: "success", "warning", "error", "info", "default"
```

#### ModernProgressBar
Barra de progreso delgada:
```python
progress = ModernProgressBar(value=75, color="#448AFF")
progress.set_value(100)
```

### 3. Vistas

#### DashboardView
Vista con tarjetas de estadísticas clave:
- Total Activas
- Ganadas (YTD)
- Por Vencer (7 días)
- Ratio de Éxito

#### LicitacionesListView
Vista de tabla con:
- Filtros de búsqueda
- Tabs (Activas/Finalizadas)
- Tabla con progress bars y badges
- Footer con estadísticas

### 4. Ventana Principal (ModernMainWindow)

Contenedor principal con:
- Sidebar de navegación
- QStackedWidget para cambiar entre vistas
- Gestión de base de datos
- Integración con modelo de licitaciones

## 🔧 Configuración

### Base de Datos

La aplicación moderna usa el mismo sistema de base de datos que la versión antigua.
Configura el backend en el archivo `.env`:

```env
APP_DB_BACKEND=firestore  # o sqlite, mysql
```

Para Firestore:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
FIREBASE_PROJECT_ID=your-project-id
```

## 🎨 Personalización

### Cambiar Colores del Tema

Edita `app/ui/theme/titanium_construct_v2.py`:

```python
PRIMARY = QColor("#7C4DFF")  # Cambiar color de acento
BACKGROUND = QColor("#1E1E1E")  # Cambiar fondo
```

### Añadir Nueva Vista

1. Crea un nuevo archivo en `app/ui/views/`
2. Hereda de `QWidget`
3. Implementa la interfaz
4. Añade la vista en `ModernMainWindow._create_views()`
5. Añade el item en el sidebar

Ejemplo:
```python
# En modern_main_window.py
self.sidebar.add_navigation_item("mi_vista", "Mi Vista", "🔧")
self.mi_vista = MiVistaCustom()
self.content_stack.addWidget(self.mi_vista)
```

## 📸 Capturas de Pantalla

### Dashboard
- Muestra 4 tarjetas con estadísticas clave
- Placeholder para gráfico de tendencias
- Tema oscuro profesional

### Gestión de Licitaciones
- Tabla moderna con progress bars
- Filtros de búsqueda avanzados
- Tabs para activas/finalizadas
- Footer con estadísticas en tiempo real

## 🔄 Compatibilidad

- **PyQt6**: Requerido
- **Python**: 3.8+
- **Backward Compatible**: La UI antigua sigue funcionando sin cambios
- **Base de Datos**: Compatible con Firestore, SQLite y MySQL

## 📝 Notas Técnicas

- Todos los archivos usan type hints de Python
- Documentación completa con docstrings
- Código siguiendo PEP 8
- Arquitectura modular y escalable
- Sin dependencias adicionales (usa las mismas que la app antigua)

## 🐛 Troubleshooting

### La aplicación no inicia
- Verifica que PyQt6 esté instalado: `pip install PyQt6`
- Verifica que las variables de entorno estén configuradas
- Revisa el archivo `.env`

### Los colores no se aplican correctamente
- Asegúrate de llamar `apply_titanium_construct_v2(app)` antes de crear ventanas
- Verifica que no haya otros temas aplicados

### Las vistas no cargan datos
- Verifica la conexión a la base de datos
- Revisa los logs de consola
- Asegúrate de que el modelo de licitaciones esté inicializado

## 🤝 Contribuir

Para añadir nuevas funcionalidades:

1. Mantén la arquitectura existente
2. Usa los componentes reutilizables cuando sea posible
3. Sigue el estilo de código existente
4. Añade docstrings y type hints
5. Prueba con diferentes backends de BD

## 📄 Licencia

Mismo que el proyecto principal.
