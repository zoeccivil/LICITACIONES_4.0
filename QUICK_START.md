# 🚀 Quick Start - Modern UI

## Inicio Rápido (5 pasos)

### 1. Verificar Dependencias
```bash
python3 --version  # Python 3.8+
pip show PyQt6     # Debe estar instalado
```

Si PyQt6 no está instalado:
```bash
pip install PyQt6
```

### 2. Configurar Base de Datos

Crear/editar archivo `.env` en la raíz del proyecto:

**Opción A - Firestore:**
```env
APP_DB_BACKEND=firestore
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
FIREBASE_PROJECT_ID=your-project-id
```

**Opción B - SQLite:**
```env
APP_DB_BACKEND=sqlite
SQLITE_DB_PATH=./licitaciones.db
```

**Opción C - MySQL:**
```env
APP_DB_BACKEND=mysql
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=licitaciones
```

### 3. Ejecutar la Aplicación

**Nueva UI Moderna (Recomendado):**
```bash
python modern_main.py
```

**UI Antigua (Backup):**
```bash
python app/main.py
```

### 4. Verificar que Funciona

Deberías ver:
1. ✅ Ventana con sidebar morado/oscuro a la izquierda
2. ✅ Dashboard con 4 tarjetas de estadísticas
3. ✅ Mensaje en status bar: "✓ Conectado a [backend]"

### 5. Explorar la UI

- **Sidebar** → Clic en "📊 Dashboard General"
- **Sidebar** → Clic en "📋 Gestión Licitaciones"
- **Filtros** → Probar búsqueda de licitaciones
- **Tabla** → Doble clic para ver detalles

---

## 🎨 Vista Previa Visual

### Layout General
```
┌────────────────────────────────────────────────┐
│ [📊] Dashboard General                         │ ← Status Bar
├──────────┬─────────────────────────────────────┤
│          │                                     │
│ 📊 Dash  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ │
│          │  │ 8   │ │ 47  │ │ 3   │ │ 32% │ │ ← StatCards
│ 📋 Licit │  └─────┘ └─────┘ └─────┘ └─────┘ │
│          │                                     │
│ 📄 Report│  ┌─────────────────────────────┐   │
│          │  │                             │   │
│ Sidebar  │  │   Placeholder para          │   │ ← Chart Area
│ 250px    │  │   Gráfico                   │   │
│          │  │                             │   │
│          │  └─────────────────────────────┘   │
└──────────┴─────────────────────────────────────┘
```

### Vista Licitaciones
```
┌────────────────────────────────────────────────┐
│ Gestión / Listado Maestro                      │
├──────────┬─────────────────────────────────────┤
│          │ [+ Nueva] [✏ Editar]               │
│          │                                     │
│ 📊 Dash  │ ┌─────────────────────────────────┐│
│          │ │ Filtros:                        ││
│ 📋 Licit │ │ [Buscar] [Lote] [Estado] [Lim..││
│          │ └─────────────────────────────────┘│
│ 📄 Report│                                     │
│          │ ┌─────────────────────────────────┐│
│          │ │ Tabla de Licitaciones           ││
│          │ │ ├─ Activas    │ Finalizadas     ││
│          │ │ │   8 items   │   47 items      ││
│          │ └─────────────────────────────────┘│
│          │ Activas: 8 | Ganadas: 0 | ...     │
└──────────┴─────────────────────────────────────┘
```

---

## 🎯 Características Principales

### Dashboard
- ✅ **Activas**: Cuenta licitaciones no finalizadas
- ✅ **Ganadas**: Total de licitaciones ganadas
- ✅ **Por Vencer**: Vencen en próximos 7 días
- ✅ **Ratio**: % de éxito (ganadas/finalizadas)

### Licitaciones
- ✅ **Filtros**: Proceso, Lote, Estado, Empresa
- ✅ **Tabs**: Activas vs Finalizadas
- ✅ **Tabla**: Con progress bars y heatmaps
- ✅ **Estadísticas**: Footer con contadores

### Navegación
- ✅ **Sidebar**: Siempre visible
- ✅ **Iconos**: Visual y claro
- ✅ **Estado activo**: Resaltado morado

---

## 🐛 Solución de Problemas

### Error: "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### Error: "Firebase no configurado"
1. Verifica que `.env` existe
2. Verifica ruta de credenciales
3. O usa SQLite: `APP_DB_BACKEND=sqlite`

### Error: "No se pudo conectar a la BD"
1. Verifica variables en `.env`
2. Para SQLite: Verifica permisos del archivo
3. Para MySQL: Verifica que el servidor esté corriendo
4. Para Firestore: Verifica credenciales

### La ventana se ve en blanco
1. Espera unos segundos (cargando datos)
2. Revisa logs en consola
3. Verifica conexión a BD

### Los datos no aparecen
1. Verifica que la BD tiene datos
2. Revisa logs de consola
3. Intenta con la UI antigua: `python app/main.py`

---

## 📚 Más Información

| Documento | Contenido |
|-----------|-----------|
| **IMPLEMENTATION_SUMMARY.md** | Resumen completo de implementación |
| **MODERN_UI_README.md** | Guía de usuario y desarrollador |
| **ARCHITECTURE.md** | Diagramas técnicos y arquitectura |
| **COMPARISON.md** | Comparación UI antigua vs nueva |

---

## 💡 Tips Útiles

### Cambiar Color de Acento
```python
# Editar: app/ui/theme/titanium_construct_v2.py
PRIMARY = QColor("#7C4DFF")  # Morado → Cambia aquí
```

### Ver Ambas UIs
```bash
# Terminal 1: UI Moderna
python modern_main.py

# Terminal 2: UI Antigua
python app/main.py
```

### Debug
Añadir prints para debug:
```python
# En modern_main.py, después de línea 180
print(f"[DEBUG] DB Client: {db_client}")
print(f"[DEBUG] Backend: {backend}")
```

---

## ✅ Checklist Primera Ejecución

- [ ] Python 3.8+ instalado
- [ ] PyQt6 instalado (`pip show PyQt6`)
- [ ] Archivo `.env` creado con configuración
- [ ] Backend seleccionado (firestore/sqlite/mysql)
- [ ] Ejecutar: `python modern_main.py`
- [ ] Ver ventana con sidebar oscuro
- [ ] Ver dashboard con 4 tarjetas
- [ ] Navegar a "Gestión Licitaciones"
- [ ] Filtrar datos en la tabla
- [ ] ✨ Disfrutar de la nueva UI

---

## 🎉 ¡Listo!

Si ves la ventana con el tema oscuro y el sidebar morado, ¡la implementación funcionó perfectamente!

**Próximos pasos:**
1. Explorar todas las vistas
2. Personalizar colores si lo deseas
3. Añadir más datos de prueba
4. Integrar gráficos en el dashboard (opcional)

**¿Problemas?** Revisa los documentos de troubleshooting o los logs de consola.

---

**Versión**: 4.0 - Modern UI  
**Fecha**: 2026-02-02  
**Estado**: ✅ Funcionando
