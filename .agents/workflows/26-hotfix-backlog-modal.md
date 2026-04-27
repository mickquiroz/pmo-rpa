---
description: hotfix-backlog-modal
---

## Objetivo
Solucionar el glitch visual de Bootstrap donde al hacer clic en "Ver Backlog", la pantalla despliega el backdrop (fondo oscuro) pero el modal no se muestra o queda inoperativo, bloqueando la UI.

## Pasos
1. Revisar `frontend/index.html` para asegurar que el modal del Backlog (presumiblemente `#backlogModal`) existe, tiene la estructura correcta de Bootstrap 5 y no tiene conflictos de z-index.
2. Revisar el botón `#btn-backlog`. Si tiene los atributos `data-bs-toggle="modal" data-bs-target="..."`, quitarlos para manejar la apertura 100% desde JavaScript y evitar asincronías.
3. Actualizar la función `fetchBacklog()` en `frontend/app.js`. Al final de la promesa (después de poblar la tabla), instanciar y mostrar explícitamente el modal usando: `new bootstrap.Modal(document.getElementById('ID_DEL_MODAL')).show();`