# -*- coding: utf-8 -*-
"""
main.py
-------
PMO-RPA MVP — FastAPI Backend  (Fase 2)

Endpoints expuestos:
  GET  /api/v1/projects                    – Lista todos los proyectos con progreso calculado
  GET  /api/v1/projects/{project_id}/phases – Fases de un proyecto específico
  PATCH /api/v1/phases/{phase_id}           – Actualiza el estado de una fase
  POST  /api/v1/blockers                    – Registra un nuevo blocker

Lógica de negocio:
  - progress_percentage se calcula al vuelo usando SUM(CASE ...) sobre Phases.
    Completed  → peso × 1.0
    In Progress → peso × 0.5
    Pending    → peso × 0.0

Autor  : Antigravity Senior Architect Agent
Fecha  : 2026-04-18
"""

from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator, List, Optional, Literal

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from datetime import timedelta

from .auth import verify_password, create_access_token, get_current_user, get_admin_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from .services.chatbot_service import get_assistant

# ---------------------------------------------------------------------------
# Configuración global
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "pmo_rpa.db"

# Cargar variables de entorno
load_dotenv(BASE_DIR / ".env")

API_PREFIX = "/api/v1"

# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PMO-RPA API",
    description=(
        "API RESTful para el sistema de control de proyectos RPA. "
        "Provee visibilidad en tiempo real sobre el avance, fases y bloqueos."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Startup: Seed de permisos básicos
# ---------------------------------------------------------------------------

def seed_permissions() -> None:
    """
    Verifica e inserta los permisos semilla en la tabla Permissions.
    Se ejecuta al arrancar la aplicación.
    """
    BASIC_PERMISSIONS = [
        "write:projects",
        "delete:projects",
        "edit:phases",
        "add:comments",
        "read:projects",
    ]
    with get_db() as conn:
        for action in BASIC_PERMISSIONS:
            existing = conn.execute(
                "SELECT id FROM Permissions WHERE action = ?", (action,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO Permissions (action) VALUES (?)",
                    (action,)
                )
        conn.commit()


def init_db_schema() -> None:
    """
    Asegura que la base de datos tenga la estructura necesaria para la Fase 29.
    Añade la columna display_order a la tabla Phases si no existe.
    """
    with get_db() as conn:
        try:
            conn.execute("ALTER TABLE Phases ADD COLUMN display_order INTEGER DEFAULT 0;")
            conn.commit()
        except sqlite3.OperationalError:
            # La columna probablemente ya existe
            pass

@app.on_event("startup")
def on_startup() -> None:
    init_db_schema()
    seed_permissions()
    
    # Health Check interno para el Chatbot AI (Fase 1)
    llm_key = os.getenv("LLM_API_KEY")
    if not llm_key:
        print("\n" + "!"*60)
        print(" AVISO: Variable 'LLM_API_KEY' no encontrada en .env")
        print(" El Asistente IA (Chatbot) estará inactivo en esta sesión.")
        print("!"*60 + "\n")
    else:
        print("\n" + "*"*60)
        print(" INFO: 'LLM_API_KEY' detectada correctamente.")
        print(" Entorno preparado para integración con Anthropic Claude 3 Haiku.")
        print("*"*60 + "\n")

# ---------------------------------------------------------------------------
# CORS — permite conexiones desde cualquier origen en el MVP local
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helper: gestor de contexto para conexiones SQLite
# ---------------------------------------------------------------------------


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Gestor de contexto para conexiones SQLite.
    Garantiza cierre correcto de la conexión y activación de
    foreign keys y row_factory para acceso por columna.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row          # acceso tipo dict por columna
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pydantic Schemas (validación de entrada / serialización de salida)
# ---------------------------------------------------------------------------


class ProjectResponse(BaseModel):
    """Representación pública de un proyecto con su progreso calculado."""

    id: int
    process_name: str
    project_type_id: int
    assigned_developer_id: int
    commercial_id: Optional[int]
    developer_name: str
    health_status: str
    start_date: str
    estimated_end_date: str
    progress_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Porcentaje calculado al vuelo desde la tabla Phases.",
    )

    class Config:
        from_attributes = True


class PhaseResponse(BaseModel):
    """Representación pública de una fase."""

    id: int
    project_id: int
    phase_name: str
    weight_percentage: int
    status: str
    start_date: str
    estimated_end_date: str
    completion_date: Optional[str]
    display_order: int = 0

    class Config:
        from_attributes = True


class PhaseUpdate(BaseModel):
    """Payload para actualizar el estado de una fase."""

    status: str = Field(
        ...,
        pattern="^(Pending|In Progress|Completed)$",
        description="Debe ser uno de: 'Pending', 'In Progress', 'Completed'.",
    )


class PhaseDatesUpdate(BaseModel):
    """Payload para que la PMO actualice las fechas de la fase."""

    start_date: str
    estimated_end_date: str


class PhaseCreate(BaseModel):
    """Payload para crear una nueva fase."""
    project_id: int = Field(..., gt=0)
    phase_name: str = Field(..., min_length=2)
    weight_percentage: int = Field(..., ge=0, le=100)
    start_date: str
    estimated_end_date: str


class PhaseDetailsUpdate(BaseModel):
    """Payload para editar los datos estructurales de la fase."""
    phase_name: str = Field(..., min_length=2)
    weight_percentage: int = Field(..., ge=0, le=100)
    display_order: Optional[int] = 0


class ProjectCreate(BaseModel):
    """Payload para inyectar nuevos proyectos y generar fases en cascada."""

    process_name: str = Field(..., min_length=2)
    project_type_id: int = Field(..., gt=0)
    assigned_developer_id: int = Field(..., gt=0)
    commercial_id: Optional[int] = None
    start_date: str
    estimated_end_date: str


class BlockerCreate(BaseModel):
    """Payload para crear un nuevo blocker."""

    project_id: int = Field(..., gt=0)
    description: str = Field(..., min_length=5)
    resolver_owner: str = Field(..., min_length=2)


class BlockerResponse(BaseModel):
    """Representación pública de un blocker creado."""

    id: int
    project_id: int
    description: str
    report_date: str
    resolver_owner: str
    status: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Payload para crear un nuevo usuario."""
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=6)
    role_id: int = Field(..., gt=0)


class UserResponse(BaseModel):
    """Representación pública de un usuario."""
    id: int
    name: str
    email: str
    role_id: int
    role_name: str
    is_active: int
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdateMe(BaseModel):
    """Payload para que un usuario actualice su propio perfil."""
    name: Optional[str] = Field(None, min_length=2)
    profile_picture: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = []

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permission_ids: List[int] = []

    class Config:
        from_attributes = True

class PermissionResponse(BaseModel):
    id: int
    action: str

    class Config:
        from_attributes = True

class ProjectTypeCreate(BaseModel):
    name: str = Field(..., min_length=2)

class ProjectTypeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class PhaseCommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1)

class PhaseCommentResponse(BaseModel):
    id: int
    phase_id: int
    user_id: int
    user_name: str
    role_name: Optional[str] = None
    profile_picture: Optional[str] = None
    comment_text: str
    created_at: str

    class Config:
        from_attributes = True


class ProjectCommentResponse(BaseModel):
    """Representación de un comentario con el nombre de la fase a la que pertenece."""
    id: int
    phase_id: int
    phase_name: str
    user_id: int
    user_name: str
    role_name: Optional[str] = None
    profile_picture: Optional[str] = None
    comment_text: str
    created_at: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Payload de entrada para el Asistente IA."""
    message: str = Field(..., min_length=1, description="Pregunta en lenguaje natural para la PMO.")


class ChatResponse(BaseModel):
    """Respuesta generada por el Asistente IA."""
    reply: str


# ---------------------------------------------------------------------------
# Endpoint de salud
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    tags=["Health"],
    summary="Verifica que la API está activa",
    status_code=status.HTTP_200_OK,
)
def health_check() -> dict:
    return {"status": "ok", "api": "PMO-RPA", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# POST /api/v1/auth/token
# ---------------------------------------------------------------------------

@app.post(f"{API_PREFIX}/auth/token", tags=["Auth"], summary="Obtiene token JWT de acceso")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db() as conn:
        user = conn.execute(
            """
            SELECT u.*, r.name as role
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            WHERE u.email = ? AND u.is_active = 1
            """,
            (form_data.username,)
        ).fetchone()

        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas (email o contraseña incorrectos)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Consultar los permisos asociados al rol del usuario via Role_Permissions → Permissions
        perm_rows = conn.execute(
            """
            SELECT p.action
            FROM Role_Permissions rp
            JOIN Permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = ?
            """,
            (user["role_id"],)
        ).fetchall()
        permissions = [row["action"] for row in perm_rows]

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "role": user["role"],
            "permissions": permissions,
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------------------------
# GET /api/v1/projects
# ---------------------------------------------------------------------------

_PROGRESS_QUERY = """
SELECT
    p.id,
    p.process_name,
    p.project_type_id,
    p.assigned_developer_id,
    p.commercial_id,
    d.name                                        AS developer_name,
    p.health_status,
    p.start_date,
    p.estimated_end_date,
    COALESCE(
        SUM(
            CASE ph.status
                WHEN 'Completed'   THEN ph.weight_percentage * 1.0
                WHEN 'In Progress' THEN ph.weight_percentage * 0.5
                ELSE                    0.0
            END
        ), 0.0
    )                                             AS progress_percentage
FROM Projects  p
JOIN Users d  ON  d.id  = p.assigned_developer_id
LEFT JOIN Phases ph ON ph.project_id = p.id
WHERE p.is_deleted = 0
GROUP BY
    p.id,
    p.process_name,
    p.project_type_id,
    p.assigned_developer_id,
    p.commercial_id,
    d.name,
    p.health_status,
    p.start_date,
    p.estimated_end_date
ORDER BY p.id;
"""


@app.get(
    f"{API_PREFIX}/projects",
    response_model=List[ProjectResponse],
    tags=["Projects"],
    summary="Lista todos los proyectos con progreso calculado",
    status_code=status.HTTP_200_OK,
)
def list_projects(current_user: dict = Depends(get_current_user)) -> List[dict]:
    """
    Devuelve todos los proyectos con `progress_percentage` calculado al vuelo.

    Regla de cálculo:
    - **Completed**   → 100 % del weight_percentage de la fase.
    - **In Progress** →  50 % del weight_percentage de la fase.
    - **Pending**     →   0 % del weight_percentage de la fase.
    """
    with get_db() as conn:
        if current_user["role"] == "Developer":
            query = _PROGRESS_QUERY.replace("WHERE p.is_deleted = 0", "WHERE p.is_deleted = 0 AND p.assigned_developer_id = ?")
            rows = conn.execute(query, (current_user["id"],)).fetchall()
        elif current_user["role"] == "Pre-sales" or "sales" in current_user["role"].lower():
            query = _PROGRESS_QUERY.replace("WHERE p.is_deleted = 0", "WHERE p.is_deleted = 0 AND p.commercial_id = ?")
            rows = conn.execute(query, (current_user["id"],)).fetchall()
        else:
            rows = conn.execute(_PROGRESS_QUERY).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# GET /api/v1/projects/backlog
# ---------------------------------------------------------------------------

@app.get(
    f"{API_PREFIX}/projects/backlog",
    response_model=List[ProjectResponse],
    tags=["Projects"],
    summary="Lista todos los proyectos eliminados lógicamente (Solo PMO/Admin)",
    status_code=status.HTTP_200_OK,
)
def list_projects_backlog(current_user: dict = Depends(get_current_user)) -> List[dict]:
    """
    Devuelve todos los proyectos eliminados lógicamente (is_deleted = 1).
    Solo accesible por usuarios con rol PMO o Admin.
    """
    if current_user["role"] not in ["Admin", "PMO"]:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Permisos insuficientes. Accesible solo para PMO o Admin."
         )
    
    query = _PROGRESS_QUERY.replace("WHERE p.is_deleted = 0", "WHERE p.is_deleted = 1")
    with get_db() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# GET /api/v1/projects/{project_id}/phases
# ---------------------------------------------------------------------------


@app.get(
    f"{API_PREFIX}/projects/{{project_id}}/phases",
    response_model=List[PhaseResponse],
    tags=["Phases"],
    summary="Obtiene todas las fases de un proyecto",
    status_code=status.HTTP_200_OK,
)
def list_phases(project_id: int) -> List[dict]:
    """Devuelve las fases de un proyecto ordenadas por su id."""
    with get_db() as conn:
        # Verificar que el proyecto existe
        project = conn.execute(
            "SELECT id FROM Projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto con id={project_id} no encontrado.",
            )

        rows = conn.execute(
            "SELECT * FROM Phases WHERE project_id = ? ORDER BY display_order ASC, start_date ASC",
            (project_id,),
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# PATCH /api/v1/phases/{phase_id}
# ---------------------------------------------------------------------------


@app.patch(
    f"{API_PREFIX}/phases/{{phase_id}}",
    response_model=PhaseResponse,
    tags=["Phases"],
    summary="Actualiza el estado de una fase",
    status_code=status.HTTP_200_OK,
)
def update_phase_status(phase_id: int, payload: PhaseUpdate) -> dict:
    """
    Actualiza el campo `status` de la fase indicada.
    Si el nuevo estado es **Completed**, registra automáticamente
    `completion_date` con la fecha de hoy. Si no, la resetea a NULL.
    """
    completion_date: Optional[str] = (
        date.today().isoformat() if payload.status == "Completed" else None
    )

    with get_db() as conn:
        phase = conn.execute(
            "SELECT id FROM Phases WHERE id = ?", (phase_id,)
        ).fetchone()
        if phase is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fase con id={phase_id} no encontrada.",
            )

        conn.execute(
            """
            UPDATE Phases
               SET status          = ?,
                   completion_date = ?
             WHERE id = ?
            """,
            (payload.status, completion_date, phase_id),
        )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM Phases WHERE id = ?", (phase_id,)
        ).fetchone()

    return dict(updated)


# ---------------------------------------------------------------------------
# POST /api/v1/blockers
# ---------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/blockers",
    response_model=BlockerResponse,
    tags=["Blockers"],
    summary="Registra un nuevo blocker para un proyecto",
    status_code=status.HTTP_201_CREATED,
)
def create_blocker(payload: BlockerCreate) -> dict:
    """
    Inserta un nuevo blocker en la base de datos.
    - `report_date` se establece automáticamente con la fecha de hoy.
    - `status` inicial siempre es **Open**.
    """
    report_date = date.today().isoformat()

    with get_db() as conn:
        # Verificar que el proyecto existe
        project = conn.execute(
            "SELECT id FROM Projects WHERE id = ?", (payload.project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto con id={payload.project_id} no encontrado.",
            )

        cursor = conn.execute(
            """
            INSERT INTO Blockers (project_id, description, report_date, resolver_owner, status)
            VALUES (?, ?, ?, ?, 'Open')
            """,
            (payload.project_id, payload.description, report_date, payload.resolver_owner),
        )
        conn.commit()
        new_id = cursor.lastrowid

        blocker = conn.execute(
            "SELECT * FROM Blockers WHERE id = ?", (new_id,)
        ).fetchone()

    return dict(blocker)


# ---------------------------------------------------------------------------
# GET /api/v1/reports/export
# ---------------------------------------------------------------------------


@app.get(
    f"{API_PREFIX}/reports/export",
    tags=["Reports"],
    summary="Exporta el estado de los proyectos en formato CSV",
)
def export_projects_csv():
    """Genera un archivo CSV en memoria con el progreso de los proyectos."""
    with get_db() as conn:
        rows = conn.execute(_PROGRESS_QUERY).fetchall()
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir cabeceras
    writer.writerow(["ID", "Proceso", "Desarrollador", "Estado de Salud", "Fecha Inicio", "Fecha Fin", "Avance (%)"])
    
    # Escribir datos
    for row in rows:
        progress_pct = round(row["progress_percentage"], 2)
        writer.writerow([
            row["id"],
            row["process_name"],
            row["developer_name"],
            row["health_status"],
            row["start_date"],
            row["estimated_end_date"],
            f"{progress_pct}%"
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": 'attachment; filename="pmo_rpa_report.csv"'}
    )


# ---------------------------------------------------------------------------
# POST /api/v1/projects
# ---------------------------------------------------------------------------


@app.post(
    f"{API_PREFIX}/projects",
    response_model=ProjectResponse,
    tags=["Projects"],
    summary="Crea un proyecto y autogenera sus 4 fases RPA",
    status_code=status.HTTP_201_CREATED,
)
def create_project(payload: ProjectCreate, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Inserta un nuevo proyecto.
    Valida que assigned_developer_id corresponda a un usuario con rol 'Developer'.
    Luego inserta en cascada las 4 fases: Discovery, Design, Development, UAT.
    """
    with get_db() as conn:
        # Validar developer
        dev = conn.execute(
            """
            SELECT u.id, r.name as role 
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            WHERE u.id = ? AND u.is_active = 1
            """,
            (payload.assigned_developer_id,)
        ).fetchone()
        
        if not dev:
            raise HTTPException(status_code=404, detail="Developer no encontrado o inactivo.")
        if dev["role"] != "Developer":
            raise HTTPException(status_code=400, detail="El usuario asignado no tiene rol 'Developer'.")

        # Insertar proyecto
        cursor = conn.execute(
            """
            INSERT INTO Projects (process_name, project_type_id, assigned_developer_id, commercial_id, start_date, estimated_end_date, health_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Green')
            """,
            (payload.process_name, payload.project_type_id, payload.assigned_developer_id, payload.commercial_id, payload.start_date, payload.estimated_end_date)
        )
        project_id = cursor.lastrowid

        # Leer plantillas de fases dinámicamente
        templates = conn.execute(
            "SELECT phase_name, weight_percentage FROM Phase_Templates WHERE project_type_id = ?",
            (payload.project_type_id,)
        ).fetchall()

        if templates:
            # Si hay plantillas, insertar fases en cascada
            phases_data = [
                (project_id, t["phase_name"], t["weight_percentage"], payload.start_date, payload.estimated_end_date, idx)
                for idx, t in enumerate(templates)
            ]
            conn.executemany(
                """
                INSERT INTO Phases (project_id, phase_name, weight_percentage, status, start_date, estimated_end_date, display_order)
                VALUES (?, ?, ?, 'Pending', ?, ?, ?)
                """,
                phases_data
            )
        # Si no hay plantillas, se crea el proyecto vacío para que el PMO agregue fases manualmente

        conn.commit()

        # Recuperar proyecto creado con progress_percentage
        row = conn.execute(
            _PROGRESS_QUERY.replace("ORDER BY p.id;", "HAVING p.id = ?;")
        , (project_id,)).fetchone()

        if not row:
            # Fallback: Construir respuesta mínima desde Projects
            p_row = conn.execute("SELECT * FROM Projects WHERE id = ?", (project_id,)).fetchone()
            dev_row = conn.execute("SELECT name FROM Users WHERE id = ?", (payload.assigned_developer_id,)).fetchone()
            row_dict = dict(p_row)
            row_dict["developer_name"] = dev_row["name"] if dev_row else "N/A"
            row_dict["progress_percentage"] = 0.0
            return row_dict

    return dict(row)

# ---------------------------------------------------------------------------
# PUT /api/v1/phases/{phase_id}/dates
# ---------------------------------------------------------------------------


@app.put(
    f"{API_PREFIX}/phases/{{phase_id}}/dates",
    response_model=PhaseResponse,
    tags=["Phases"],
    summary="Actualiza start_date y estimated_end_date de una fase",
    status_code=status.HTTP_200_OK,
)
def update_phase_dates(phase_id: int, payload: PhaseDatesUpdate) -> dict:
    with get_db() as conn:
        phase = conn.execute("SELECT id FROM Phases WHERE id = ?", (phase_id,)).fetchone()
        if not phase:
            raise HTTPException(status_code=404, detail="Fase no encontrada.")

        conn.execute(
            "UPDATE Phases SET start_date = ?, estimated_end_date = ? WHERE id = ?",
            (payload.start_date, payload.estimated_end_date, phase_id)
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM Phases WHERE id = ?", (phase_id,)).fetchone()

    return dict(updated)


# ---------------------------------------------------------------------------
# POST /api/v1/phases
# ---------------------------------------------------------------------------

@app.post(
    f"{API_PREFIX}/phases",
    response_model=PhaseResponse,
    tags=["Phases"],
    summary="Crea una nueva fase (Solo Admin/PMO)",
    status_code=status.HTTP_201_CREATED,
)
def create_phase(payload: PhaseCreate, current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] == "Developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Accesible solo para PMO o Admin."
        )
        
    with get_db() as conn:
        project = conn.execute("SELECT id FROM Projects WHERE id = ?", (payload.project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
            
        # Calcular el siguiente display_order
        order_row = conn.execute(
            "SELECT COALESCE(MAX(display_order), -1) + 1 FROM Phases WHERE project_id = ?",
            (payload.project_id,)
        ).fetchone()
        next_order = order_row[0]

        cursor = conn.execute(
            """
            INSERT INTO Phases (project_id, phase_name, weight_percentage, status, start_date, estimated_end_date, display_order)
            VALUES (?, ?, ?, 'Pending', ?, ?, ?)
            """,
            (payload.project_id, payload.phase_name, payload.weight_percentage, payload.start_date, payload.estimated_end_date, next_order)
        )
        conn.commit()
        new_id = cursor.lastrowid
        
        phase = conn.execute("SELECT * FROM Phases WHERE id = ?", (new_id,)).fetchone()
        
    return dict(phase)

# ---------------------------------------------------------------------------
# PUT /api/v1/phases/{phase_id}/details
# ---------------------------------------------------------------------------

@app.put(
    f"{API_PREFIX}/phases/{{phase_id}}/details",
    response_model=PhaseResponse,
    tags=["Phases"],
    summary="Actualiza nombre y peso de una fase (Solo Admin/PMO)",
    status_code=status.HTTP_200_OK,
)
def update_phase_details(phase_id: int, payload: PhaseDetailsUpdate, current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] == "Developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Accesible solo para PMO o Admin."
        )

    with get_db() as conn:
        phase = conn.execute("SELECT id FROM Phases WHERE id = ?", (phase_id,)).fetchone()
        if not phase:
            raise HTTPException(status_code=404, detail="Fase no encontrada.")

        conn.execute(
            "UPDATE Phases SET phase_name = ?, weight_percentage = ?, display_order = ? WHERE id = ?",
            (payload.phase_name, payload.weight_percentage, payload.display_order, phase_id)
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM Phases WHERE id = ?", (phase_id,)).fetchone()

    return dict(updated)


# ---------------------------------------------------------------------------
# DELETE /api/v1/phases/{phase_id}
# ---------------------------------------------------------------------------

@app.delete(
    f"{API_PREFIX}/phases/{{phase_id}}",
    tags=["Phases"],
    summary="Elimina una fase de un proyecto (Solo Admin/PMO)",
    status_code=status.HTTP_200_OK,
)
def delete_phase(phase_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "Developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Accesible solo para PMO o Admin."
        )

    with get_db() as conn:
        phase = conn.execute("SELECT id FROM Phases WHERE id = ?", (phase_id,)).fetchone()
        if not phase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fase no encontrada.")
        
        conn.execute("DELETE FROM Phases WHERE id = ?", (phase_id,))
        conn.commit()
    
    return {"message": f"Fase {phase_id} eliminada exitosamente."}


# ---------------------------------------------------------------------------
# POST /api/v1/users
# ---------------------------------------------------------------------------

@app.post(
    f"{API_PREFIX}/users",
    response_model=UserResponse,
    tags=["Users (Admin)"],
    summary="Crea un nuevo usuario (Solo Admin)",
    status_code=status.HTTP_201_CREATED,
)
def create_user(payload: UserCreate, _: dict = Depends(get_admin_user)) -> dict:
    hashed_password = get_password_hash(payload.password)
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO Users (name, email, hashed_password, role_id, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (payload.name, payload.email, hashed_password, payload.role_id)
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            user = conn.execute(
                """
                SELECT u.id, u.name, u.email, u.role_id, r.name as role_name, u.is_active 
                FROM Users u
                JOIN Roles r ON u.role_id = r.id
                WHERE u.id = ?
                """,
                (new_id,)
            ).fetchone()
            
            return dict(user)
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado o el rol no existe."
            )

# ---------------------------------------------------------------------------
# GET /api/v1/users
# ---------------------------------------------------------------------------

@app.get(
    f"{API_PREFIX}/users",
    response_model=List[UserResponse],
    tags=["Users (Admin)"],
    summary="Lista todos los usuarios (Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def list_users(_: dict = Depends(get_admin_user)) -> List[dict]:
    """Devuelve la lista completa de usuarios."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.email, u.role_id, r.name as role_name, u.is_active 
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            """
        ).fetchall()
    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# GET /api/v1/users/developers
# ---------------------------------------------------------------------------

@app.get(
    f"{API_PREFIX}/users/developers",
    response_model=List[UserResponse],
    tags=["Users (PMO/Admin)"],
    summary="Lista todos los desarrolladores (Solo Admin/PMO)",
    status_code=status.HTTP_200_OK,
)
def list_developers(current_user: dict = Depends(get_current_user)) -> List[dict]:
    """Devuelve la lista de desarrolladores activos."""
    if current_user["role"] == "Developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Accesible solo para PMO o Admin."
        )
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.email, u.role_id, r.name as role_name, u.is_active 
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            WHERE r.name = 'Developer' AND u.is_active = 1
            """
        ).fetchall()
    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# GET /api/v1/users/commercials
# ---------------------------------------------------------------------------

@app.get(
    f"{API_PREFIX}/users/commercials",
    response_model=List[UserResponse],
    tags=["Users (PMO/Admin)"],
    summary="Lista todos los comerciales (Solo Admin/PMO)",
    status_code=status.HTTP_200_OK,
)
def list_commercials(current_user: dict = Depends(get_current_user)) -> List[dict]:
    """Devuelve la lista de comerciales activos (rol Pre-sales o similar)."""
    if current_user["role"] == "Developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Accesible solo para PMO o Admin."
        )
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.email, u.role_id, r.name as role_name, u.is_active 
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            WHERE (r.name = 'Pre-sales' OR r.name LIKE '%sales%') AND u.is_active = 1
            """
        ).fetchall()
    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# DELETE /api/v1/users/{user_id}
# ---------------------------------------------------------------------------

@app.delete(
    f"{API_PREFIX}/users/{{user_id}}",
    tags=["Users (Admin)"],
    summary="Da de baja a un usuario (Soft Delete, Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def delete_user(user_id: int, _: dict = Depends(get_admin_user)):
    """Inactiva a un usuario sin borrarlo físicamente para no romper relaciones."""
    with get_db() as conn:
        user = conn.execute("SELECT id FROM Users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
        
        conn.execute("UPDATE Users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
    
    return {"message": f"Usuario {user_id} dado de baja exitosamente."}


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/{user_id}/reactivate
# ---------------------------------------------------------------------------

@app.patch(
    f"{API_PREFIX}/users/{{user_id}}/reactivate",
    tags=["Users (Admin)"],
    summary="Reactiva un usuario dado de baja (Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def reactivate_user(user_id: int, _: dict = Depends(get_admin_user)):
    """Reactiva a un usuario con is_active = 0, volviendo a establecerlo en is_active = 1."""
    with get_db() as conn:
        user = conn.execute("SELECT id FROM Users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

        conn.execute("UPDATE Users SET is_active = 1 WHERE id = ?", (user_id,))
        conn.commit()

    return {"message": f"Usuario {user_id} reactivado exitosamente."}


# ---------------------------------------------------------------------------
# DELETE /api/v1/projects/{project_id}
# ---------------------------------------------------------------------------

@app.delete(
    f"{API_PREFIX}/projects/{{project_id}}",
    tags=["Projects (Admin)"],
    summary="Eliminado lógico de un proyecto (Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def delete_project(project_id: int, _: dict = Depends(get_admin_user)):
    with get_db() as conn:
        project = conn.execute("SELECT id FROM Projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
        
        conn.execute("UPDATE Projects SET is_deleted = 1 WHERE id = ?", (project_id,))
        conn.commit()
    
    return {"message": f"Proyecto {project_id} eliminado lógicamente."}


# ---------------------------------------------------------------------------
# GET & POST /api/v1/roles
# ---------------------------------------------------------------------------
@app.get(
    f"{API_PREFIX}/permissions",
    response_model=List[PermissionResponse],
    tags=["Permissions (Admin)"],
    summary="Lista todos los permisos del sistema",
    status_code=status.HTTP_200_OK,
)
def list_permissions(_: dict = Depends(get_admin_user)) -> List[dict]:
    """Devuelve todos los permisos disponibles para asignar a roles."""
    with get_db() as conn:
        rows = conn.execute("SELECT id, action FROM Permissions ORDER BY id").fetchall()
    return [dict(row) for row in rows]


@app.get(
    f"{API_PREFIX}/roles",
    response_model=List[RoleResponse],
    tags=["Roles (Admin)"],
    summary="Lista todos los roles con sus permisos asignados",
    status_code=status.HTTP_200_OK,
)
def list_roles(_: dict = Depends(get_admin_user)) -> List[dict]:
    """Devuelve todos los roles incluyendo los IDs de permisos asignados."""
    with get_db() as conn:
        roles = conn.execute("SELECT id, name, description FROM Roles ORDER BY id").fetchall()
        result = []
        for role in roles:
            role_dict = dict(role)
            perm_rows = conn.execute(
                "SELECT permission_id FROM Role_Permissions WHERE role_id = ?",
                (role_dict["id"],)
            ).fetchall()
            role_dict["permission_ids"] = [r["permission_id"] for r in perm_rows]
            result.append(role_dict)
    return result


@app.post(
    f"{API_PREFIX}/roles",
    response_model=RoleResponse,
    tags=["Roles (Admin)"],
    summary="Crea un rol con permisos opcionales",
    status_code=status.HTTP_201_CREATED,
)
def create_role(payload: RoleCreate, _: dict = Depends(get_admin_user)) -> dict:
    """Inserta un nuevo rol y mapea sus permisos en Role_Permissions."""
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO Roles (name, description) VALUES (?, ?)",
                (payload.name, payload.description)
            )
            new_id = cursor.lastrowid

            # Insertar permisos en la tabla relacional si se proporcionaron
            if payload.permission_ids:
                conn.executemany(
                    "INSERT OR IGNORE INTO Role_Permissions (role_id, permission_id) VALUES (?, ?)",
                    [(new_id, pid) for pid in payload.permission_ids]
                )

            conn.commit()

            role = conn.execute("SELECT id, name, description FROM Roles WHERE id = ?", (new_id,)).fetchone()
            role_dict = dict(role)
            perm_rows = conn.execute(
                "SELECT permission_id FROM Role_Permissions WHERE role_id = ?",
                (new_id,)
            ).fetchall()
            role_dict["permission_ids"] = [r["permission_id"] for r in perm_rows]
            return role_dict
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="El nombre del rol ya existe.")

@app.put(
    f"{API_PREFIX}/roles/{{role_id}}",
    response_model=RoleResponse,
    tags=["Roles (Admin)"],
    summary="Actualiza un rol y sus permisos (Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def update_role(role_id: int, payload: RoleUpdate, _: dict = Depends(get_admin_user)) -> dict:
    """Actualiza los datos de un rol y refresca sus permisos en Role_Permissions."""
    with get_db() as conn:
        role = conn.execute("SELECT id FROM Roles WHERE id = ?", (role_id,)).fetchone()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado.")
        
        try:
            # Actualizar nombre y descripción
            conn.execute(
                "UPDATE Roles SET name = ?, description = ? WHERE id = ?",
                (payload.name, payload.description, role_id)
            )

            # Refrescar permisos: borrar e insertar
            conn.execute("DELETE FROM Role_Permissions WHERE role_id = ?", (role_id,))
            if payload.permission_ids:
                conn.executemany(
                    "INSERT INTO Role_Permissions (role_id, permission_id) VALUES (?, ?)",
                    [(role_id, pid) for pid in payload.permission_ids]
                )
            
            conn.commit()

            # Devolver el rol actualizado
            updated = conn.execute("SELECT id, name, description FROM Roles WHERE id = ?", (role_id,)).fetchone()
            role_dict = dict(updated)
            perm_rows = conn.execute(
                "SELECT permission_id FROM Role_Permissions WHERE role_id = ?",
                (role_id,)
            ).fetchall()
            role_dict["permission_ids"] = [r["permission_id"] for r in perm_rows]
            return role_dict

        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="El nombre del rol ya existe o hay un error de integridad.")

@app.delete(
    f"{API_PREFIX}/roles/{{role_id}}",
    tags=["Roles (Admin)"],
    summary="Elimina un rol (Solo Admin)",
    status_code=status.HTTP_200_OK,
)
def delete_role(role_id: int, _: dict = Depends(get_admin_user)):
    """Elimina un rol si no tiene usuarios asociados."""
    with get_db() as conn:
        role = conn.execute("SELECT id FROM Roles WHERE id = ?", (role_id,)).fetchone()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado.")

        # Regla de negocio estricta: No borrar si tiene usuarios
        count = conn.execute("SELECT count(id) FROM Users WHERE role_id = ?", (role_id,)).fetchone()[0]
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el rol: tiene {count} usuarios asignados."
            )

        # Borrar permisos asociados y luego el rol
        conn.execute("DELETE FROM Role_Permissions WHERE role_id = ?", (role_id,))
        conn.execute("DELETE FROM Roles WHERE id = ?", (role_id,))
        conn.commit()

    return {"message": f"Rol {role_id} eliminado exitosamente."}


# ---------------------------------------------------------------------------
# GET & POST /api/v1/project-types
# ---------------------------------------------------------------------------
@app.get(
    f"{API_PREFIX}/project-types",
    response_model=List[ProjectTypeResponse],
    tags=["Project Types (Admin)"],
    summary="Lista todos los tipos de proyecto",
    status_code=status.HTTP_200_OK,
)
def list_project_types(_: dict = Depends(get_admin_user)) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT id, name FROM Project_Types").fetchall()
    return [dict(row) for row in rows]


@app.post(
    f"{API_PREFIX}/project-types",
    response_model=ProjectTypeResponse,
    tags=["Project Types (Admin)"],
    summary="Crea un tipo de proyecto",
    status_code=status.HTTP_201_CREATED,
)
def create_project_type(payload: ProjectTypeCreate, _: dict = Depends(get_admin_user)) -> dict:
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO Project_Types (name) VALUES (?)",
                (payload.name,)
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            ptype = conn.execute("SELECT id, name FROM Project_Types WHERE id = ?", (new_id,)).fetchone()
            return dict(ptype)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="El tipo de proyecto ya existe.")

# ---------------------------------------------------------------------------
# Comments API
# ---------------------------------------------------------------------------

@app.get(
    f"{API_PREFIX}/phases/{{phase_id}}/comments",
    response_model=List[PhaseCommentResponse],
    tags=["Phase Comments"],
    summary="Lista comentarios de una fase",
    status_code=status.HTTP_200_OK,
)
def list_phase_comments(phase_id: int, _: dict = Depends(get_current_user)) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.phase_id, c.user_id, u.name as user_name, r.name as role_name, u.profile_picture, c.comment_text, c.created_at
            FROM Phase_Comments c
            JOIN Users u ON c.user_id = u.id
            JOIN Roles r ON u.role_id = r.id
            WHERE c.phase_id = ?
            ORDER BY c.created_at DESC
            """,
            (phase_id,)
        ).fetchall()
    return [dict(row) for row in rows]

@app.post(
    f"{API_PREFIX}/phases/{{phase_id}}/comments",
    response_model=PhaseCommentResponse,
    tags=["Phase Comments"],
    summary="Crea comentario para una fase",
    status_code=status.HTTP_201_CREATED,
)
def create_phase_comment(phase_id: int, payload: PhaseCommentCreate, current_user: dict = Depends(get_current_user)) -> dict:
    with get_db() as conn:
        phase = conn.execute("SELECT id FROM Phases WHERE id = ?", (phase_id,)).fetchone()
        if not phase:
            raise HTTPException(status_code=404, detail="Fase no encontrada")
            
        from datetime import datetime
        created_at = datetime.utcnow().isoformat() + "Z"
        
        cursor = conn.execute(
            """
            INSERT INTO Phase_Comments (phase_id, user_id, comment_text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (phase_id, current_user["id"], payload.comment_text, created_at)
        )
        conn.commit()
        new_id = cursor.lastrowid
        
        new_comment = conn.execute(
            """
            SELECT c.id, c.phase_id, c.user_id, u.name as user_name, r.name as role_name, u.profile_picture, c.comment_text, c.created_at
            FROM Phase_Comments c
            JOIN Users u ON c.user_id = u.id
            JOIN Roles r ON u.role_id = r.id
            WHERE c.id = ?
            """,
            (new_id,)
        ).fetchone()
    
    return dict(new_comment)


@app.get(
    f"{API_PREFIX}/projects/{{project_id}}/comments",
    response_model=List[ProjectCommentResponse],
    tags=["Projects"],
    summary="Lista todos los comentarios de un proyecto (todas sus fases)",
    status_code=status.HTTP_200_OK,
)
def list_project_comments(project_id: int, phase_id: Optional[int] = None, _: dict = Depends(get_current_user)) -> List[dict]:
    """
    Obtiene todos los comentarios de todas las fases asociadas a un proyecto específico.
    Incluye el nombre de la fase para contexto en la vista consolidada.
    """
    query = """
        SELECT 
            c.id, 
            c.phase_id, 
            p.phase_name, 
            c.user_id, 
            u.name as user_name, 
            r.name as role_name,
            u.profile_picture,
            c.comment_text, 
            c.created_at
        FROM Phase_Comments c
        JOIN Users u ON c.user_id = u.id
        JOIN Roles r ON u.role_id = r.id
        JOIN Phases p ON c.phase_id = p.id
        WHERE p.project_id = ?
    """
    params = [project_id]
    
    if phase_id:
        query += " AND c.phase_id = ?"
        params.append(phase_id)
        
    query += " ORDER BY c.created_at DESC"
    
    with get_db() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Self-Service Profile API
# ---------------------------------------------------------------------------

@app.get(f"{API_PREFIX}/users/me", tags=["Users"], response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Retorna el perfil del usuario autenticado actualmente."""
    # current_user ya viene de get_current_user con id, name, email, role
    # Pero necesitamos role_name e is_active para UserResponse
    with get_db() as conn:
        user = conn.execute(
            """
            SELECT u.id, u.name, u.email, u.role_id, r.name as role_name, u.is_active, u.profile_picture
            FROM Users u
            JOIN Roles r ON u.role_id = r.id
            WHERE u.id = ?
            """,
            (current_user["id"],)
        ).fetchone()
    return dict(user)

@app.put(f"{API_PREFIX}/users/me", tags=["Users"], response_model=UserResponse)
def update_me(payload: UserUpdateMe, current_user: dict = Depends(get_current_user)):
    """Permite al usuario actualizar su propio nombre, foto o contraseña."""
    updates = []
    params = []
    
    if payload.name is not None:
        updates.append("name = ?")
        params.append(payload.name)
    
    if payload.profile_picture is not None:
        updates.append("profile_picture = ?")
        params.append(payload.profile_picture)
        
    if payload.password is not None:
        updates.append("hashed_password = ?")
        params.append(get_password_hash(payload.password))
        
    if not updates:
        return get_me(current_user)
        
    params.append(current_user["id"])
    query = f"UPDATE Users SET {', '.join(updates)} WHERE id = ?"
    
    with get_db() as conn:
        conn.execute(query, params)
        conn.commit()
        
    return get_me(current_user)


# ---------------------------------------------------------------------------
# AI Assistant API (Fase 3)
# ---------------------------------------------------------------------------

@app.post(
    f"{API_PREFIX}/chat",
    response_model=ChatResponse,
    tags=["AI Assistant"],
    summary="Consulta al Asistente IA de la PMO",
    status_code=status.HTTP_200_OK,
)
def chat_with_assistant(
    payload: ChatRequest, 
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """
    Endpoint para interactuar con el 'cerebro' IA de la PMO.
    Traduce lenguaje natural a SQL y devuelve una respuesta resumida.
    Requiere autenticación JWT.
    """
    try:
        assistant = get_assistant()
        response_text = assistant.ask_bot(payload.message)
        
        # Si ask_bot devolvió un mensaje de error interno (empezando con "Error al procesar")
        # o si el LLM no está configurado, lanzamos excepción.
        if response_text.startswith("Error al procesar la consulta:"):
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response_text
            )
            
        return ChatResponse(reply=response_text)
        
    except Exception as e:
        # Manejo de fallos críticos (ej: API Key no configurada o caída de Anthropic)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"El servicio de IA no está disponible en este momento: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Frontend Static Files
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")

