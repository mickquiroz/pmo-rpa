"""
validate_api.py — Script de validación de la lógica de negocio del API.
Ejecutar desde la raíz del proyecto: python scripts/validate_api.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import get_db, _PROGRESS_QUERY, DB_PATH  # noqa: E402

print(f"DB_PATH: {DB_PATH}")
print(f"DB existe: {DB_PATH.exists()}\n")

with get_db() as conn:
    rows = conn.execute(_PROGRESS_QUERY).fetchall()

if not rows:
    print("[WARN] No hay proyectos en la base de datos.")
    sys.exit(0)

for r in rows:
    print(
        f"  Proyecto id={r['id']} | {r['process_name']!r}\n"
        f"    Developer   : {r['developer_name']}\n"
        f"    Health      : {r['health_status']}\n"
        f"    Progreso    : {r['progress_percentage']:.1f}%\n"
    )

print(f"[OK] Cálculo de progress_percentage validado. Total proyectos: {len(rows)}")

# Verificar la matemática esperada del seed:
# Discovery (10, Completed) -> 10*1.0 = 10
# Design    (30, In Progress) -> 30*0.5 = 15
# Development (40, Pending) -> 0
# UAT       (20, Pending) -> 0
# Esperado: 25.0%
expected = 25.0
actual = rows[0]["progress_percentage"]
assert abs(actual - expected) < 0.001, f"ERROR: esperado {expected}, obtenido {actual}"
print(f"[OK] Matemática correcta: {actual:.1f}% (esperado {expected:.1f}%)")
