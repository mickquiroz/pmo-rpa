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

DDL_ROLES = """
CREATE TABLE IF NOT EXISTS Roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT
);
"""

DDL_PERMISSIONS = """
CREATE TABLE IF NOT EXISTS Permissions (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT    NOT NULL UNIQUE
);
"""

DDL_ROLE_PERMISSIONS = """
CREATE TABLE IF NOT EXISTS Role_Permissions (
    role_id       INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY(role_id, permission_id),
    CONSTRAINT fk_rp_role
        FOREIGN KEY (role_id) REFERENCES Roles(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_rp_permission
        FOREIGN KEY (permission_id) REFERENCES Permissions(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""

DDL_USERS = """
CREATE TABLE IF NOT EXISTS Users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    hashed_password TEXT    NOT NULL,
    role_id         INTEGER NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id) REFERENCES Roles(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
"""

DDL_PROJECT_TYPES = """
CREATE TABLE IF NOT EXISTS Project_Types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);
"""

DDL_PHASE_TEMPLATES = """
CREATE TABLE IF NOT EXISTS Phase_Templates (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_type_id   INTEGER NOT NULL,
    phase_name        TEXT    NOT NULL,
    weight_percentage INTEGER NOT NULL
                              CHECK(weight_percentage BETWEEN 1 AND 100),
    CONSTRAINT fk_phase_templates_type
        FOREIGN KEY (project_type_id) REFERENCES Project_Types(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""

DDL_PROJECTS = """
CREATE TABLE IF NOT EXISTS Projects (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    process_name          TEXT    NOT NULL,
    project_type_id       INTEGER NOT NULL,
    assigned_developer_id INTEGER NOT NULL,
    commercial_id         INTEGER,
    start_date            TEXT    NOT NULL,          -- formato ISO-8601: YYYY-MM-DD
    estimated_end_date    TEXT    NOT NULL,          -- formato ISO-8601: YYYY-MM-DD
    health_status         TEXT    NOT NULL DEFAULT 'Green'
                                   CHECK(health_status IN ('Green', 'Yellow', 'Red')),
    is_deleted            BOOLEAN NOT NULL DEFAULT 0,
    CONSTRAINT fk_projects_type
        FOREIGN KEY (project_type_id) REFERENCES Project_Types(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_projects_developer
        FOREIGN KEY (assigned_developer_id) REFERENCES Users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_projects_commercial
        FOREIGN KEY (commercial_id) REFERENCES Users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
"""

DDL_PHASES = """
CREATE TABLE IF NOT EXISTS Phases (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id         INTEGER NOT NULL,
    phase_name         TEXT    NOT NULL,
    weight_percentage  INTEGER NOT NULL
                               CHECK(weight_percentage BETWEEN 1 AND 100),
    status             TEXT    NOT NULL DEFAULT 'Pending'
                               CHECK(status IN ('Pending', 'In Progress', 'Completed')),
    start_date         TEXT    NOT NULL,                  -- formato ISO-8601
    estimated_end_date TEXT    NOT NULL,                  -- formato ISO-8601
    completion_date    TEXT,                              -- NULL hasta que se complete
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

DDL_PHASE_COMMENTS = """
CREATE TABLE IF NOT EXISTS Phase_Comments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id     INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    comment_text TEXT    NOT NULL,
    created_at   TEXT    NOT NULL,
    CONSTRAINT fk_pc_phase
        FOREIGN KEY (phase_id) REFERENCES Phases(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_pc_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
"""

ALL_DDL = [
    DDL_ROLES, DDL_PERMISSIONS, DDL_ROLE_PERMISSIONS,
    DDL_USERS, DDL_PROJECT_TYPES, DDL_PHASE_TEMPLATES,
    DDL_PROJECTS, DDL_PHASES, DDL_BLOCKERS, DDL_PHASE_COMMENTS
]


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_ROLES = [
    ("Admin", "Administrador del sistema"),
    ("PMO", "Project Management Office"),
    ("Developer", "Desarrollador RPA"),
    ("Pre-Sales Viewer", "Consultor o preventa"),
]

SEED_USERS = [
    # (name, email, role_name, is_active, raw_password)
    ("System Admin", "admin@empresa.com", "Admin", 1, "admin123"),
    ("PMO Lead", "pmo@empresa.com", "PMO", 1, "pmo123"),
    ("John Doe RPA", "john.doe.rpa@empresa.com", "Developer", 1, "dev123"),
    ("Jane Sales", "jane.sales@empresa.com", "Pre-Sales Viewer", 1, "sales123"),
]

SEED_PROJECT_TYPES = [
    ("RPA",),
    ("RPA + IA",),
    ("Web",),
    ("Chatbot IA",),
]

# phase_name, weight_percentage for RPA
SEED_PHASE_TEMPLATES_RPA = [
    ("Discovery", 10),
    ("Design", 20),
    ("Development", 40),
    ("UAT", 30),
]

SEED_PROJECTS = [
    # (process_name, project_type_name, developer_email_ref, commercial_email_ref, start_date, estimated_end_date, health_status)
    (
        "Automatizacion de Conciliacion Bancaria",
        "RPA",
        "john.doe.rpa@empresa.com",
        "jane.sales@empresa.com",
        "2026-04-01",
        "2026-08-31",
        "Green",
    ),
]

# Fases estándar RPA instanciadas para el proyecto
SEED_PHASES_TEMPLATE = [
    ("Discovery",    10, "Completed",   "2026-04-01", "2026-04-15"),
    ("Design",       20, "In Progress", "2026-04-16", "2026-05-15"),
    ("Development",  40, "Pending",     "2026-05-16", "2026-07-31"),
    ("UAT",          30, "Pending",     "2026-08-01", "2026-08-31"),
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

    # --- Roles ---
    for r_name, r_desc in SEED_ROLES:
        cursor.execute(
            "INSERT OR IGNORE INTO Roles (name, description) VALUES (?, ?)",
            (r_name, r_desc)
        )
    print(f"  [OK] Roles insertados: {len(SEED_ROLES)}")

    # --- Users ---
    for user in SEED_USERS:
        name, email, role_name, is_active, raw_pwd = user
        hashed_pwd = pwd_context.hash(raw_pwd)
        
        cursor.execute("SELECT id FROM Roles WHERE name = ?", (role_name,))
        role_row = cursor.fetchone()
        if not role_row:
            raise ValueError(f"Role '{role_name}' no encontrado para usuario '{email}'.")
        role_id = role_row[0]

        cursor.execute(
            """
            INSERT OR IGNORE INTO Users (name, email, hashed_password, role_id, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, hashed_pwd, role_id, is_active)
        )
    print(f"  [OK] Users insertados / ya existentes: {len(SEED_USERS)}")

    # --- Project Types ---
    for pt in SEED_PROJECT_TYPES:
        cursor.execute("INSERT OR IGNORE INTO Project_Types (name) VALUES (?)", pt)
    print(f"  [OK] Project_Types insertados: {len(SEED_PROJECT_TYPES)}")

    # --- Phase Templates ---
    cursor.execute("SELECT id FROM Project_Types WHERE name = 'RPA'")
    pt_row = cursor.fetchone()
    if pt_row:
        type_id = pt_row[0]
        for p_name, p_weight in SEED_PHASE_TEMPLATES_RPA:
            cursor.execute(
                """
                INSERT OR IGNORE INTO Phase_Templates (project_type_id, phase_name, weight_percentage)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM Phase_Templates WHERE project_type_id = ? AND phase_name = ?
                )
                """,
                (type_id, p_name, p_weight, type_id, p_name)
            )
    print(f"  [OK] Phase_Templates para RPA insertados.")

    # --- Projects ---
    for proj in SEED_PROJECTS:
        process_name, pt_name, dev_email, comm_email, start_date, end_date, health = proj

        cursor.execute("SELECT id FROM Users WHERE email = ?", (dev_email,))
        row_dev = cursor.fetchone()
        assigned_developer_id = row_dev[0] if row_dev else None

        cursor.execute("SELECT id FROM Users WHERE email = ?", (comm_email,))
        row_comm = cursor.fetchone()
        commercial_id = row_comm[0] if row_comm else None

        cursor.execute("SELECT id FROM Project_Types WHERE name = ?", (pt_name,))
        row_type = cursor.fetchone()
        pt_id = row_type[0] if row_type else None

        if not assigned_developer_id or not pt_id:
            continue

        cursor.execute(
            """
            INSERT OR IGNORE INTO Projects
                (process_name, project_type_id, assigned_developer_id, commercial_id, start_date, estimated_end_date, health_status, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (process_name, pt_id, assigned_developer_id, commercial_id, start_date, end_date, health),
        )
    print(f"  [OK] Projects insertados / ya existentes: {len(SEED_PROJECTS)}")

    # --- Phases (4 fases por proyecto) ---
    # Obtener ID del proyecto semilla para asociar las fases
    cursor.execute(
        "SELECT id FROM Projects WHERE process_name = ?",
        (SEED_PROJECTS[0][0],),
    )
    project_row = cursor.fetchone()
    if project_row:
        project_id = project_row[0]

        for phase_name, weight, status, start_date, estimated_end_date in SEED_PHASES_TEMPLATE:
            completion_date = "2026-04-15" if status == "Completed" else None
            cursor.execute(
                """
                INSERT OR IGNORE INTO Phases
                    (project_id, phase_name, weight_percentage, status, start_date, estimated_end_date, completion_date)
                SELECT ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM Phases
                    WHERE project_id = ? AND phase_name = ?
                )
                """,
                (
                    project_id, phase_name, weight, status, start_date, estimated_end_date, completion_date,
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
