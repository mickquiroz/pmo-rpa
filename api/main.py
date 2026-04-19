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

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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
JOIN Developers d  ON  d.id  = p.developer_id
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
def list_projects() -> List[dict]:
    """
    Devuelve todos los proyectos con `progress_percentage` calculado al vuelo.

    Regla de cálculo:
    - **Completed**   → 100 % del weight_percentage de la fase.
    - **In Progress** →  50 % del weight_percentage de la fase.
    - **Pending**     →   0 % del weight_percentage de la fase.
    """
    with get_db() as conn:
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
# Frontend Static Files
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")

