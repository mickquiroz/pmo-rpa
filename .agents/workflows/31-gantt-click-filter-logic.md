---
description: 31-gantt-click-filter-logic
---

## Objetivo
Optimizar la interacción del Gantt a un solo click y crear la funcionalidad de filtrado dinámico de comentarios por fase con opción de retorno a vista global.

## Pasos
1. **Frontend (app.js):** Ajustar la inicialización de `Gantt` para asegurar que `on_click` capture el evento al primer toque.
2. **Frontend (app.js):** Modificar `fetchProjectComments` para que acepte un parámetro opcional `phaseId`. Si se pasa, solo muestra los de esa fase; si no, muestra todos.
3. **Frontend (index.html):** Añadir un botón `#btn-show-all-comments` (inicialmente oculto) junto al badge de la fase seleccionada.
4. **Lógica:** Al hacer click en el Gantt, mostrar el botón "Ver todos los comentarios". Al hacer click en ese botón, limpiar el filtro y ocultar el botón.