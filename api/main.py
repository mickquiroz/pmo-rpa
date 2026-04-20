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

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from datetime import timedelta

from .auth import verify_password, create_access_token, get_current_user, get_admin_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

# ---------------------------------------------------------------------------
# Configuración global
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "pmo_rpa.db"

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


class ProjectCreate(BaseModel):
    """Payload para inyectar nuevos proyectos y generar fases en cascada."""

    process_name: str = Field(..., min_length=2)
    assigned_developer_id: int = Field(..., gt=0)
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
    role: Literal['PMO', 'Developer']


class UserResponse(BaseModel):
    """Representación pública de un usuario."""
    id: int
    name: str
    email: str
    role: str
    is_active: int

    class Config:
        from_attributes = True


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
            "SELECT * FROM Users WHERE email = ? AND is_active = 1",
            (form_data.username,)
        ).fetchone()
        
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas (email o contraseña incorrectos)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------------------------
# GET /api/v1/projects
# ---------------------------------------------------------------------------

_PROGRESS_QUERY = """
SELECT
    p.id,
    p.process_name,
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
GROUP BY
    p.id,
    p.process_name,
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
            query = _PROGRESS_QUERY.replace("GROUP BY", "WHERE p.assigned_developer_id = ?\nGROUP BY")
            rows = conn.execute(query, (current_user["id"],)).fetchall()
        else:
            rows = conn.execute(_PROGRESS_QUERY).fetchall()
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
            "SELECT * FROM Phases WHERE project_id = ? ORDER BY id",
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
            "SELECT id, role FROM Users WHERE id = ? AND is_active = 1",
            (payload.assigned_developer_id,)
        ).fetchone()
        
        if not dev:
            raise HTTPException(status_code=404, detail="Developer no encontrado o inactivo.")
        if dev["role"] != "Developer":
            raise HTTPException(status_code=400, detail="El usuario asignado no tiene rol 'Developer'.")

        # Insertar proyecto
        cursor = conn.execute(
            """
            INSERT INTO Projects (process_name, assigned_developer_id, start_date, estimated_end_date, health_status)
            VALUES (?, ?, ?, ?, 'Green')
            """,
            (payload.process_name, payload.assigned_developer_id, payload.start_date, payload.estimated_end_date)
        )
        project_id = cursor.lastrowid

        # Insertar 4 fases por defecto
        # Se asumen fechas genéricas, luego la PMO puede hacer un PUT a fechas (o se calculan solapadas)
        phases_data = [
            (project_id, "Discovery", 10, payload.start_date, payload.estimated_end_date),
            (project_id, "Design", 30, payload.start_date, payload.estimated_end_date),
            (project_id, "Development", 40, payload.start_date, payload.estimated_end_date),
            (project_id, "UAT", 20, payload.start_date, payload.estimated_end_date),
        ]

        conn.executemany(
            """
            INSERT INTO Phases (project_id, phase_name, weight_percentage, status, start_date, estimated_end_date)
            VALUES (?, ?, ?, 'Pending', ?, ?)
            """,
            phases_data
        )
        conn.commit()

        # Recuperar proyecto creado con progress_percentage
        row = conn.execute(
            _PROGRESS_QUERY.replace("ORDER BY p.id;", "HAVING p.id = ?;")
        , (project_id,)).fetchone()
        
        if not row:
            # Fallback
            row = conn.execute("SELECT * FROM Projects WHERE id = ?", (project_id,)).fetchone()

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
    """Crea un usuario (rol PMO o Developer) asignándole contraseña y lo activa."""
    hashed_password = get_password_hash(payload.password)
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO Users (name, email, hashed_password, role, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (payload.name, payload.email, hashed_password, payload.role)
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            user = conn.execute(
                "SELECT id, name, email, role, is_active FROM Users WHERE id = ?",
                (new_id,)
            ).fetchone()
            
            return dict(user)
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado."
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
        rows = conn.execute("SELECT id, name, email, role, is_active FROM Users").fetchall()
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
            "SELECT id, name, email, role, is_active FROM Users WHERE role = 'Developer' AND is_active = 1"
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
# Frontend Static Files
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")

