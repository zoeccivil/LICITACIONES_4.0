# Arquitectura de la UI Moderna

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     modern_main.py                          │
│  - Entry Point                                              │
│  - Inicializa QApplication                                  │
│  - Aplica Titanium Construct v2 Theme                       │
│  - Inicializa Firebase/DB                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ crea
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ModernMainWindow                               │
│  - Ventana principal (QMainWindow)                          │
│  - Layout: Sidebar + Content Area                           │
│  - Gestiona navegación y cambio de vistas                   │
└───────┬─────────────────────┬───────────────────────────────┘
        │                     │
        │ contiene            │ contiene
        ▼                     ▼
┌───────────────┐    ┌────────────────────────┐
│ ModernSidebar │    │   QStackedWidget       │
│               │    │   (Content Area)       │
│ - Dashboard   │    │                        │
│ - Licitaciones│◄───┤ ┌────────────────────┐ │
│ - Reportes    │    │ │  DashboardView     │ │
│               │    │ │  - 4 StatCards     │ │
│ Navigation    │    │ │  - Chart Placeholder│ │
│ Buttons       │    │ └────────────────────┘ │
│               │    │                        │
└───────────────┘    │ ┌────────────────────┐ │
                     │ │ LicitacionesListView│ │
                     │ │  - Filters Panel   │ │
                     │ │  - Tables (Tabs)   │ │
                     │ │  - Footer Stats    │ │
                     │ └────────────────────┘ │
                     │                        │
                     │ ┌────────────────────┐ │
                     │ │  ReportesView      │ │
                     │ │  (Placeholder)     │ │
                     │ └────────────────────┘ │
                     └────────────────────────┘
```

## Flujo de Datos

```
┌──────────────┐
│ Database     │
│ (Firestore/  │
│  SQLite/     │
│  MySQL)      │
└──────┬───────┘
       │
       │ load_all_licitaciones()
       ▼
┌──────────────────────┐
│ DatabaseAdapter      │
│ (db_adapter.py)      │
└──────┬───────────────┘
       │
       │ subscribe_to_licitaciones()
       ▼
┌──────────────────────────────┐
│ LicitacionesTableModel       │
│ - set_rows()                 │
│ - Notifica cambios           │
└──────┬───────────────────────┘
       │
       │ Model actualizado
       ├──────────────┬────────────────┐
       │              │                │
       ▼              ▼                ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│DashboardView│ │Licitaciones  │ │StatusProxy   │
│             │ │ListView      │ │Model         │
│refresh_stats│ │              │ │              │
│()           │ │refresh()     │ │invalidate()  │
└─────────────┘ └──────────────┘ └──────────────┘
```

## Estructura de Archivos y Responsabilidades

```
app/ui/
├── theme/
│   └── titanium_construct_v2.py
│       ├── TitaniumStyle.get_stylesheet()  → Retorna QSS completo
│       └── apply_titanium_construct_v2()   → Aplica tema a QApplication
│
├── widgets/
│   └── modern_widgets.py
│       ├── StatCard                → Tarjeta de estadística (Dashboard)
│       ├── ModernSidebar            → Barra de navegación lateral
│       ├── StatusBadge              → Badge de estado (en tablas)
│       └── ModernProgressBar        → Barra de progreso delgada
│
├── views/
│   ├── dashboard_view.py
│   │   └── DashboardView
│   │       ├── _setup_ui()          → Crea grid de StatCards
│   │       ├── refresh_stats()      → Actualiza valores desde DB
│   │       ├── _count_activas()     → Calcula métricas
│   │       └── _calculate_ratio()   → Calcula ratio de éxito
│   │
│   └── licitaciones_list_view.py
│       └── LicitacionesListView
│           ├── _setup_ui()          → Crea tabla, filtros, footer
│           ├── _setup_models()      → Configura proxy models
│           ├── _apply_delegates()   → Progress bars & heatmaps
│           ├── _apply_filters()     → Filtra tablas
│           └── refresh()            → Actualiza vista completa
│
└── windows/
    └── modern_main_window.py
        └── ModernMainWindow
            ├── _setup_ui()                  → Layout Sidebar + Stack
            ├── _initialize_database()       → Conecta a BD
            ├── _create_views()              → Instancia vistas
            ├── _subscribe_to_updates()      → Escucha cambios BD
            └── _on_navigation_changed()     → Cambia vista activa
```

## Interacción entre Componentes

### 1. Inicio de la Aplicación

```
modern_main.py
    │
    ├─► QApplication.instance()
    ├─► apply_titanium_construct_v2(app)
    ├─► _initialize_firebase() [si backend = firestore]
    └─► ModernMainWindow(db_client)
            │
            ├─► DatabaseAdapter.open()
            ├─► LicitacionesTableModel()
            ├─► _create_views()
            │       ├─► DashboardView(db)
            │       └─► LicitacionesListView(model, db)
            │
            └─► window.show()
```

### 2. Navegación del Usuario

```
Usuario hace clic en Sidebar
    │
    ▼
ModernSidebar.navigation_changed.emit("licitaciones")
    │
    ▼
ModernMainWindow._on_navigation_changed("licitaciones")
    │
    ├─► content_stack.setCurrentIndex(1)
    ├─► statusBar().showMessage("Gestión / Listado Maestro")
    └─► licitaciones_view.refresh()
```

### 3. Actualización de Datos

```
Base de Datos cambia
    │
    ▼
DatabaseAdapter notifica via callback
    │
    ▼
LicitacionesTableModel.set_rows(new_data)
    │
    ├─► beginResetModel()
    ├─► self._rows = new_data
    └─► endResetModel()
            │
            ├──────────────┬────────────────┐
            │              │                │
            ▼              ▼                ▼
    DashboardView    ListView.refresh()   Tablas se
    .refresh_stats()                      actualizan
```

## Widgets Reutilizables - Jerarquía

```
QWidget (PyQt6)
    │
    ├─► StatCard (QFrame)
    │   └── children:
    │       ├── QLabel (title)
    │       └── QLabel (value)
    │
    ├─► StatusBadge (QLabel)
    │   └── styled with QSS
    │
    ├─► ModernProgressBar (QWidget)
    │   └── children:
    │       ├── QProgressBar
    │       └── QLabel (percentage)
    │
    └─► ModernSidebar (QFrame)
        └── children:
            ├── Brand widget
            ├── QPushButton (nav items) × N
            └── Stretch
```

## Estilos CSS (QSS) - Aplicación

```
QApplication
    │
    └─► setStyleSheet(TitaniumStyle.get_stylesheet())
            │
            ├─► Estilos globales
            │   ├── QWidget (base)
            │   ├── QMainWindow
            │   └── QDialog
            │
            ├─► Controles
            │   ├── QPushButton
            │   ├── QLineEdit
            │   ├── QComboBox
            │   └── QTableWidget
            │
            └─► Componentes personalizados
                └── #StatCard, #ModernSidebar, etc.
```

## Patrón de Diseño Utilizado

**MVC (Model-View-Controller) con Señales/Slots de Qt:**

- **Model**: `LicitacionesTableModel`, `StatusFilterProxyModel`
- **View**: `DashboardView`, `LicitacionesListView`, `ModernMainWindow`
- **Controller**: Señales de PyQt6 (`navigation_changed`, `detail_requested`)

**Composición sobre Herencia:**
- Widgets reutilizables se componen en vistas
- Vistas se componen en la ventana principal
- No se fuerza herencia innecesaria

**Dependency Injection:**
- `DatabaseAdapter` se pasa a las vistas
- `LicitacionesTableModel` se comparte entre vistas
- Permite testing y flexibilidad
