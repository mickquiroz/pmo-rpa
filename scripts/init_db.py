# -*- coding: utf-8 -*-
"""
init_db.py
----------
PMO-RPA MVP - Database Initialization Script
Fase 1: Capa de Datos

Responsabilidades:
  - Crear el archivo SQLite en ./data/pmo_rpa.db
  - Definir el esquema relacional normalizado (4 tablas)
  - Insertar datos semilla (seed) para validar integridad referencial
  - Idempotente: puede ejecutarse múltiples veces sin duplicar datos

Autor   : Antigravity Senior Architect Agent
Fecha   : 2026-04-18
"""

import sqlite3
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de rutas
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # raíz del proyecto
DB_DIR   = BASE_DIR / "data"
DB_PATH  = DB_DIR / "pmo_rpa.db"


# ---------------------------------------------------------------------------
# DDL — Data Definition Language
# ---------------------------------------------------------------------------

DDL_DEVELOPERS = """
CREATE TABLE IF NOT EXISTS Developers (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    email     TEXT    NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1  -- 1 = True, 0 = False (SQLite bool)
);
"""

DDL_PROJECTS = """
CREATE TABLE IF NOT EXISTS Projects (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    process_name       TEXT    NOT NULL,
    developer_id       INTEGER NOT NULL,
    start_date         TEXT    NOT NULL,          -- formato ISO-8601: YYYY-MM-DD
    estimated_end_date TEXT    NOT NULL,          -- formato ISO-8601: YYYY-MM-DD
    health_status      TEXT    NOT NULL DEFAULT 'Green'
                                CHECK(health_status IN ('Green', 'Yellow', 'Red')),
    CONSTRAINT fk_projects_developer
        FOREIGN KEY (developer_id) REFERENCES Developers(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
"""

DDL_PHASES = """
CREATE TABLE IF NOT EXISTS Phases (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id        INTEGER NOT NULL,
    phase_name        TEXT    NOT NULL,
    weight_percentage INTEGER NOT NULL
                              CHECK(weight_percentage BETWEEN 1 AND 100),
    status            TEXT    NOT NULL DEFAULT 'Pending'
                              CHECK(status IN ('Pending', 'In Progress', 'Completed')),
    completion_date   TEXT,                       -- NULL hasta que se complete
    CONSTRAINT fk_phases_project
        FOREIGN KEY (project_id) REFERENCES Projects(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""

DDL_BLOCKERS = """
CREATE TABLE IF NOT EXISTS Blockers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL,
    description    TEXT    NOT NULL,
    report_date    TEXT    NOT NULL,              -- formato ISO-8601: YYYY-MM-DD
    resolver_owner TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'Open'
                           CHECK(status IN ('Open', 'Resolved')),
    CONSTRAINT fk_blockers_project
        FOREIGN KEY (project_id) REFERENCES Projects(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""

ALL_DDL = [DDL_DEVELOPERS, DDL_PROJECTS, DDL_PHASES, DDL_BLOCKERS]


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

SEED_DEVELOPERS = [
    # (name, email, is_active)
    ("John Doe RPA", "john.doe.rpa@empresa.com", 1),
]

SEED_PROJECTS = [
    # (process_name, developer_email_ref, start_date, estimated_end_date, health_status)
    (
        "Automatización de Conciliación Bancaria",
        "john.doe.rpa@empresa.com",
        "2026-04-01",
        "2026-08-31",
        "Green",
    ),
]

# Fases estándar RPA  (phase_name, weight_percentage, status)
SEED_PHASES_TEMPLATE = [
    ("Discovery",    10, "Completed"),
    ("Design",       30, "In Progress"),
    ("Development",  40, "Pending"),
    ("UAT",          20, "Pending"),
]


# ---------------------------------------------------------------------------
# Inicialización de la base de datos
# ---------------------------------------------------------------------------

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Ejecuta todos los DDL para crear tablas (IF NOT EXISTS)."""
    cursor.execute("PRAGMA foreign_keys = ON;")
    for ddl in ALL_DDL:
        cursor.execute(ddl)
    print("  [OK] Esquema creado / verificado correctamente.")


def insert_seed_data(cursor: sqlite3.Cursor) -> None:
    """
    Inserta datos semilla de forma idempotente.
    Usa INSERT OR IGNORE para evitar duplicados en ejecuciones repetidas.
    """

    # --- Developers ---
    cursor.executemany(
        """
        INSERT OR IGNORE INTO Developers (name, email, is_active)
        VALUES (?, ?, ?)
        """,
        SEED_DEVELOPERS,
    )
    print(f"  [OK] Developers insertados / ya existentes: {len(SEED_DEVELOPERS)}")

    # --- Projects ---
    for proj in SEED_PROJECTS:
        process_name, dev_email, start_date, end_date, health = proj

        # Resolver developer_id por email (integridad referencial explícita)
        cursor.execute(
            "SELECT id FROM Developers WHERE email = ?", (dev_email,)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(
                f"Developer con email '{dev_email}' no encontrado. "
                "Verifica los datos semilla."
            )
        developer_id = row[0]

        cursor.execute(
            """
            INSERT OR IGNORE INTO Projects
                (process_name, developer_id, start_date, estimated_end_date, health_status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (process_name, developer_id, start_date, end_date, health),
        )
    print(f"  [OK] Projects insertados / ya existentes: {len(SEED_PROJECTS)}")

    # --- Phases (4 fases por proyecto) ---
    # Obtener ID del proyecto semilla para asociar las fases
    cursor.execute(
        "SELECT id FROM Projects WHERE process_name = ?",
        (SEED_PROJECTS[0][0],),
    )
    project_row = cursor.fetchone()
    if project_row is None:
        raise ValueError("No se encontró el proyecto semilla para insertar Phases.")
    project_id = project_row[0]

    for phase_name, weight, status in SEED_PHASES_TEMPLATE:
        completion_date = "2026-04-15" if status == "Completed" else None
        cursor.execute(
            """
            INSERT OR IGNORE INTO Phases
                (project_id, phase_name, weight_percentage, status, completion_date)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM Phases
                WHERE project_id = ? AND phase_name = ?
            )
            """,
            (
                project_id, phase_name, weight, status, completion_date,
                project_id, phase_name,
            ),
        )
    print(f"  [OK] Phases insertadas / ya existentes: {len(SEED_PHASES_TEMPLATE)}")
    print("  [OK] Seed data completado.")


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  PMO-RPA - Inicializacion de Base de Datos SQLite")
    print("=" * 60)
    print(f"  Ruta de la base de datos: {DB_PATH}")

    # Asegurarse de que el directorio data/ existe
    DB_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            print("\n[1/2] Creando esquema...")
            create_schema(cursor)

            print("\n[2/2] Insertando datos semilla...")
            insert_seed_data(cursor)

            conn.commit()

        # Verificación post-ejecución
        db_size = DB_PATH.stat().st_size
        if db_size > 0:
            print(f"\n{'=' * 60}")
            print(f"  [SUCCESS] Base de datos creada exitosamente.")
            print(f"     Tamano: {db_size:,} bytes")
            print(f"     Ruta  : {DB_PATH}")
            print(f"{'=' * 60}")
        else:
            print("  [WARNING] El archivo .db existe pero esta vacio.")
            sys.exit(1)

    except sqlite3.Error as e:
        print(f"\n  [ERROR] Error de SQLite: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n  [ERROR] Error en datos semilla: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n  [ERROR] Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
