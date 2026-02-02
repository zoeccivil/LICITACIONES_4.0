"""
Configuración simple para la app de licitaciones. 

Guarda y lee: 
- Ruta del archivo de credenciales de Firebase
- Bucket de Storage
en un pequeño JSON en la carpeta raíz del proyecto/ejecutable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Tuple, Optional

CONFIG_FILENAME = "lic_config.json"  # ← CORREGIDO (sin espacio)


def _get_base_dir() -> Path:
    """
    Devuelve la carpeta base del proyecto/ejecutable donde se guardará lic_config.json.
    
    - Si es ejecutable (frozen): carpeta donde está el .exe
    - Si es script. py: carpeta RAÍZ del proyecto (2 niveles arriba de app/core/)
    """
    if getattr(sys, "frozen", False):
        # Ejecutable:  carpeta del . exe
        base = Path(sys.executable).parent
        print(f"[lic_config] Modo ejecutable, base dir:  {base}")
        return base
    else:
        # Script:  subir desde app/core/ a la raíz del proyecto
        # lic_config.py está en app/core/, así que subimos 2 niveles
        current = Path(__file__).resolve().parent  # app/core/
        base = current.parent. parent  # GESTOR_LICITACIONS_3.0/
        print(f"[lic_config] Modo script, base dir: {base}")
        return base


def _config_path() -> Path:
    """Ruta completa del archivo de configuración."""
    return _get_base_dir() / CONFIG_FILENAME


def _load_raw_config() -> dict:
    """Lee el JSON de configuración.  Devuelve {} si no existe o hay error."""
    path = _config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        print(f"[lic_config] Error leyendo {path}: {e}")
        return {}


def _save_raw_config(data: dict) -> None:
    """Guarda el dict en el JSON de configuración."""
    path = _config_path()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[lic_config] ✓ Configuración guardada en:  {path}")
    except Exception as e:
        print(f"[lic_config] ✗ Error guardando configuración en {path}: {e}")
        raise


def get_firebase_config() -> Tuple[Optional[str], Optional[str]]: 
    """
    Devuelve (credentials_path, storage_bucket) desde el JSON de config. 
    
    Si no hay datos guardados, devuelve (None, None).
    """
    data = _load_raw_config()
    cred = data.get("firebase_credentials_path")
    bucket = data.get("firebase_storage_bucket")
    
    if cred:
        cred = str(cred)
    if bucket:
        bucket = str(bucket)
    
    return cred, bucket


def set_firebase_config(credentials_path: str, storage_bucket:  str) -> None:
    """
    Guarda la ruta del archivo de credenciales y el bucket en el JSON de config. 
    """
    data = _load_raw_config()
    data["firebase_credentials_path"] = credentials_path
    data["firebase_storage_bucket"] = storage_bucket
    _save_raw_config(data)


def get_config_path_for_display() -> str:
    """Devuelve la ruta del archivo de configuración para mostrar al usuario."""
    return str(_config_path())