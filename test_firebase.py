"""Test de conectividad con Firebase"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Añadir el proyecto al path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

print("=" * 60)
print("TEST DE FIREBASE")
print("=" * 60)

# 1. Verificar configuración
print("\n[1] VERIFICACIÓN DE CONFIGURACIÓN")
print("-" * 60)

from app.core import lic_config

try:
    cred_path, bucket = lic_config.get_firebase_config()
    print(f"✓ Archivo de credenciales: {cred_path}")
    print(f"✓ Bucket configurado: {bucket}")
    
    if cred_path and os.path.exists(cred_path):
        print(f"✓ El archivo existe: {cred_path}")
        
        # Verificar que es un JSON válido
        import json
        with open(cred_path, 'r') as f:
            cred_data = json.load(f)
            print(f"✓ JSON válido")
            print(f"  - Project ID: {cred_data.get('project_id')}")
            print(f"  - Client Email: {cred_data.get('client_email')}")
    else:
        print(f"✗ El archivo NO existe: {cred_path}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error leyendo configuración: {e}")
    sys.exit(1)

# 2. Inicializar Firebase
print("\n[2] INICIALIZACIÓN DE FIREBASE")
print("-" * 60)

try:
    from firebase_admin import credentials, initialize_app, firestore
    
    print("Creando credenciales...")
    cred = credentials.Certificate(cred_path)
    print("✓ Credenciales creadas")
    
    print("Inicializando app...")
    app = initialize_app(cred)
    print("✓ Firebase inicializado")
    
    print("Obteniendo cliente Firestore...")
    client = firestore.client()
    print("✓ Cliente Firestore obtenido")
    
except Exception as e:
    print(f"✗ Error inicializando Firebase: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Probar consulta simple
print("\n[3] PRUEBA DE CONSULTA")
print("-" * 60)

try:
    print("Consultando colección 'licitaciones'...")
    
    # Consulta limitada para no sobrecargar
    docs_ref = client.collection('licitaciones').limit(5)
    
    print("Obteniendo documentos (timeout 10s)...")
    docs = docs_ref.get(timeout=10)
    
    print(f"✓ Consulta exitosa: {len(docs)} documentos obtenidos")
    
    if docs:
        print("\nPrimeros documentos:")
        for i, doc in enumerate(docs[:3], 1):
            data = doc.to_dict()
            print(f"  {i}. {data.get('numero_proceso')} - {data.get('nombre_proceso', 'Sin nombre')[:50]}")
    
except Exception as e:
    print(f"✗ Error en consulta: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Verificar tiempos de respuesta
print("\n[4] PRUEBA DE RENDIMIENTO")
print("-" * 60)

try:
    import time
    
    print("Consultando TODAS las licitaciones...")
    start = time.time()
    
    all_docs = client.collection('licitaciones').get(timeout=30)
    
    elapsed = time.time() - start
    
    print(f"✓ Tiempo de consulta: {elapsed:.2f}s")
    print(f"✓ Total de documentos: {len(all_docs)}")
    
    if elapsed > 10:
        print("⚠️  ADVERTENCIA: La consulta tomó más de 10 segundos")
        print("   Esto puede causar que la UI se congele al iniciar")
        print("   Solución: Implementar carga asíncrona o paginación")
    
except Exception as e:
    print(f"✗ Error en consulta masiva: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETADO")
print("=" * 60)