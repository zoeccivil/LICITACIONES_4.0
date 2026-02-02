"""Script para limpiar prints de debug innecesarios."""
import re
from pathlib import Path

# Patrones a eliminar (comentar en lugar de borrar)
PATTERNS_TO_COMMENT = [
    r'print\(f"\[DEBUG\]\[DB\._map_licitacion\].*?\n',
    r'print\(f"   \[RAW-LOTE\].*?\n',
    r'print\(f"   \[MODEL-LOTE\].*?\n',
    r'print\("\[DEBUG\] Refrescando.*?\n',
    r'print\("\[DEBUG\] Guardando.*?\n',
]

# Archivos a limpiar
FILES_TO_CLEAN = [
    "app/core/db_adapter.py",
    "app/ui/views/licitaciones_list_view.py",
]

def comment_debug_prints(file_path: Path):
    """Comenta prints de debug en un archivo."""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    for pattern in PATTERNS_TO_COMMENT:
        content = re.sub(pattern, lambda m: '# ' + m.group(0), content, flags=re.MULTILINE)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"✓ Limpiado: {file_path}")
        return True
    else:
        print(f"  Sin cambios: {file_path}")
        return False

def main():
    """Ejecuta limpieza."""
    print("🧹 Limpiando prints de debug...\n")
    
    cleaned = 0
    for file_str in FILES_TO_CLEAN:
        file_path = Path(file_str)
        if file_path.exists():
            if comment_debug_prints(file_path):
                cleaned += 1
        else:
            print(f"⚠️  No encontrado: {file_path}")
    
    print(f"\n✅ Limpieza completada: {cleaned} archivos modificados")

if __name__ == "__main__":
    main()