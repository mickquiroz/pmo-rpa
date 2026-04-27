---
description: Bugfixing Crítico y Sincronización UI
---

**Objetivo:** Reparar errores de integración entre el Frontend y el Backend detectados en la Fase 18 (Roles undefined, selects hardcodeados, soft-delete de usuarios, botón eliminar, backlog gris y error de plantillas).

**Pasos a ejecutar por el Agente:**
1. **app.js (Tabla Usuarios):** Cambiar `user.role` por `user.role_name` en la renderización de la tabla. Mostrar también los usuarios con `is_active === 0` pero con un badge rojo "Inactivo" y cambiar el botón de acción a "Reactivar".
2. **app.js (Creación Usuarios):** Crear una función `populateRolesSelect()` que consuma `GET /api/v1/roles` y llene el `<select>` del formulario de usuarios. Actualizar el POST para enviar `role_id` (int) en lugar de un string.
3. **api/main.py (Reactivar Usuario):** Crear un endpoint `PATCH /api/v1/users/{user_id}/reactivate` que haga `UPDATE is_active = 1`.
4. **index.html (Navbar):** Mover el botón `<button id="btn-admin-users">` al Navbar, al lado de "Administrar Roles".
5. **index.html & app.js (Eliminar Proyectos):** Añadir un botón "Eliminar" en la tabla principal de proyectos (solo visible para Admin). Enlazarlo a `DELETE /api/v1/projects/{id}` y actualizar el DOM.
6. **api/main.py (Fases por Defecto):** En `POST /projects`, si no existen `Phase_Templates` para el tipo de proyecto seleccionado, **NO** lanzar error 400. En su lugar, crear el proyecto vacío (sin fases) para que el PMO las agregue manualmente después.
7. **index.html (Backlog Fix):** Asegurar que `#backlogModal` no se congele.