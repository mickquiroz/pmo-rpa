---
description: Interfaz Operativa (Tipos, Comerciales, Comentarios y Backlog)
---

**Objetivo:** Conectar el Frontend a las nuevas capacidades empresariales del Backend, actualizando formularios y añadiendo vistas de auditoría y papelera.

**Pasos a ejecutar por el Agente:**
1. **Backend (Ajuste Menor):** En `api/main.py`, crear un nuevo endpoint `GET /api/v1/projects/backlog` (solo accesible para Admin/PMO) que retorne los proyectos donde `is_deleted = 1`.
2. **HTML - Crear Proyecto:** Modificar el `#createProjectModal` en `index.html` para incluir dos nuevos `<select>`: uno para `project_type_id` (requerido) y otro para `commercial_id` (opcional).
3. **HTML - Backlog:** Crear un nuevo modal `#backlogModal` con una tabla para ver proyectos eliminados. Añadir un botón "Ver Backlog" en el Navbar (solo visible para Admin/PMO).
4. **HTML - Comentarios de Fase:** En el `#managePhasesModal`, añadir un botón "Comentarios" por cada fase que abra un nuevo modal o un panel desplegable donde se listen los comentarios y haya un input para agregar uno nuevo.
5. **JS - Lógica:** - En `app.js`, crear funciones para cargar los Tipos de Proyecto y los usuarios con rol "Pre-Sales Viewer" en el modal de crear proyecto.
   - Actualizar `handleCreateProject` para enviar los nuevos IDs.
   - Crear funciones `fetchBacklog()` para llenar el modal de papelera.
   - Crear funciones `fetchPhaseComments(phaseId)` y `createPhaseComment(phaseId)` para gestionar la auditoría de cada fase.