---
description: bulk-save-phases
---

## Objetivo
Mejorar la UX del modal de "Administrar Fases" eliminando el guardado individual por fila e implementando un "Guardado Masivo" (Bulk Save) con un único botón en el pie del modal.

## Pasos
1. Modificar `frontend/index.html` en la sección `#managePhasesModal`: 
   - Añadir un `<button id="btn-save-all-phases" class="btn btn-primary">Guardar</button>` dentro del `.modal-footer` al lado del botón "Cerrar".
2. Modificar `frontend/app.js` en la función `openManagePhases()`:
   - Eliminar el botón `<button class="btn btn-sm btn-success" onclick="updatePhase(...)">Guardar</button>` de cada fila (`<tr>`).
   - Añadir a cada fila un atributo de datos para identificar la fase (ej: `<tr data-phase-id="${p.id}">`).
3. Modificar `frontend/app.js` para crear una nueva función asíncrona `saveAllPhases()`:
   - La función debe iterar sobre todos los `<tr>` de `#phases-table-body`.
   - Extraer los valores de inputs y selects de cada fila.
   - Construir un array de promesas (`fetch`) para ejecutar las actualizaciones (`PUT` de fechas, `PUT` de detalles, `PATCH` de estado) en paralelo.
   - Usar `Promise.all()` para esperar a que todas las fases se guarden antes de recargar la vista (`fetchProjects()`) y mostrar un único `alert('Fases actualizadas correctamente')`.
4. Añadir el Event Listener para el nuevo botón `#btn-save-all-phases` en el bloque `DOMContentLoaded`.