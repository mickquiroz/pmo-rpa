---
description: 30-gantt-integrated-comments
---

## Objetivo
Integrar la sección de comentarios directamente dentro del modal del Gantt, permitiendo una lectura global cronológica por defecto y restringiendo la escritura a la selección específica de una fase.

## Pasos
1. **Backend (`api/main.py`):** Crear un endpoint `GET /api/v1/projects/{project_id}/comments`. Debe hacer un JOIN entre `Phase_Comments`, `Users` y `Phases` para devolver todos los comentarios del proyecto ordenados cronológicamente (ASC o DESC), incluyendo el `phase_name`.
2. **Frontend (`index.html`):** - Eliminar el modal aislado `#phaseCommentsModal`.
   - Modificar el `#ganttModal`: dividir el `modal-body` en dos contenedores. El superior para `#gantt-target` y el inferior para el panel de comentarios.
   - El panel de comentarios debe tener un `max-height` (ej. 300px) y `overflow-y: auto`.
   - El formulario `#create-comment-form` debe estar aquí pero con `style="display: none;"` por defecto.
3. **Frontend (`app.js`):**
   - En `showProjectGantt()`, llamar al nuevo endpoint del proyecto y renderizar todos los comentarios. Inyectar un badge (etiqueta) con el nombre de la fase en cada comentario. Ocultar el formulario de creación.
   - En el evento `on_click` del Gantt: mostrar el formulario `#create-comment-form`, setear el `phaseId` seleccionado, y (opcionalmente) filtrar visualmente la lista de comentarios para mostrar solo los de esa fase (o resaltar el badge).