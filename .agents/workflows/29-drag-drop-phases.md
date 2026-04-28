---
description: drag-drop-phases
---

## Objetivo
Implementar la funcionalidad de Drag & Drop (Arrastrar y Soltar) en el modal de Administrar Fases para permitir a los usuarios reordenar el ciclo de vida del proyecto de forma intuitiva, guardando este orden en la base de datos.

## Pasos
1. Modificar `frontend/index.html` para incluir el CDN de SortableJS (`https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js`).
2. Modificar `frontend/app.js` (`openManagePhases`) para:
   - Añadir una nueva columna al inicio de cada fila (`<tr>`) que sirva como "Drag Handle" (ej. `<td class="drag-handle" style="cursor: grab;">☰</td>`).
   - Inicializar `new Sortable(document.getElementById('phases-table-body'), { handle: '.drag-handle', animation: 150 });`.
3. Modificar `api/main.py` para soportar el reordenamiento:
   - Asegurar que la tabla `Phases` tenga una columna `display_order INTEGER DEFAULT 0` (añadirla vía `ALTER TABLE` si no existe).
   - Actualizar el endpoint `GET /api/v1/projects/{project_id}/phases` para que ordene por `ORDER BY display_order ASC, start_date ASC`.
4. Modificar la función `saveAllPhases()` en `frontend/app.js` para que capture el nuevo índice (posición visual en la tabla) de cada fase y lo envíe al backend durante el Bulk Save.