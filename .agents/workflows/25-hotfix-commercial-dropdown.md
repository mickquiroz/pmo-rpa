---
description: hotfix-commercial-dropdown
---

## Objetivo
Actualizar la lógica del frontend (app.js) y/o backend (main.py) para que el dropdown de "Comercial Asignado (Opcional)" en el modal de creación de proyectos se pueble correctamente con los usuarios activos que poseen el rol de "Pre-sales".

## Pasos
1. Analizar cómo se está poblando actualmente el campo de comerciales en el modal `#createProjectModal`.
2. Identificar si el filtro se hace en el backend (ej. endpoint GET /api/v1/users/commercials) o en el frontend (filtrando un GET /api/v1/users general).
3. Actualizar la condición de filtrado para que coincida exactamente con el nombre de rol "Pre-sales" (o que incluya la palabra "sales" para ser más flexible).
4. Guardar los cambios y garantizar que no se rompa la creación de proyectos.