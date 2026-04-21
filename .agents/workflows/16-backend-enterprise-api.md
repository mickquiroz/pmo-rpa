---
description: Motor Backend API (Enterprise)
---

**Objetivo:** Actualizar `api/main.py` para soportar las nuevas tablas de la Fase 15 (Roles dinámicos, Tipos de Proyecto, Plantillas, Comentarios) y aplicar las nuevas reglas de negocio de visibilidad y borrado lógico.

**Pasos a ejecutar por el Agente:**
1. **Actualizar Modelos Pydantic:** Refactorizar los esquemas de entrada/salida para soportar `project_type_id`, `commercial_id`, `is_deleted` y crear los modelos para `PhaseComment`, `Role`, y `ProjectType`.
2. **Endpoints de Administración (Admin Only):**
   - CRUD para Roles (`/api/v1/roles`).
   - CRUD para Tipos de Proyecto (`/api/v1/project-types`).
   - Endpoint para obtener la lista de usuarios filtrada por rol (ej. listar comerciales disponibles).
3. **Refactorizar Proyectos (`GET /api/v1/projects`):**
   - Excluir siempre los proyectos donde `is_deleted == 1`.
   - Lógica de Visibilidad: Si el usuario es 'Admin' o 'PMO', ve todos. Si es 'Developer', ve donde `assigned_developer_id == user.id`. Si es 'Pre-Sales Viewer', ve SOLO donde `commercial_id == user.id`.
4. **Refactorizar Creación de Proyectos (`POST /api/v1/projects`):**
   - Recibir `project_type_id` y `commercial_id`.
   - En lugar de insertar fases hardcodeadas, leer de `Phase_Templates` usando el `project_type_id` e insertar dinámicamente las fases iniciales.
5. **Soft Delete (`DELETE /api/v1/projects/{id}`):**
   - Actualizar el endpoint para que, si el rol es Admin, haga un `UPDATE is_deleted = 1` en lugar de borrar la fila física.
6. **Endpoints de Auditoría:**
   - Crear `POST /api/v1/phases/{phase_id}/comments` y `GET /api/v1/phases/{phase_id}/comments`.