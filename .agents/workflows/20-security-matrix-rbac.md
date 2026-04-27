---
description: Matriz de Seguridad Dinámica (RBAC)
---

**Objetivo:** Activar el modelo de permisos granulares (Muchos a Muchos) creado en la Fase 15, permitiendo al Administrador asignar capacidades específicas (ej. crear, editar, borrar) a los roles mediante checkboxes en el Frontend.

**Pasos a ejecutar por el Agente:**
1. **Backend (main.py - Permisos):** - Crear un script interno (o en el arranque de main.py) que asegure la existencia de permisos semilla en la tabla `Permissions` (ej. 'write:projects', 'delete:projects', 'edit:phases', 'add:comments').
   - Crear endpoint `GET /api/v1/permissions` para listar estos permisos.
2. **Backend (main.py - Roles):** - Actualizar el modelo `RoleCreate` para aceptar una lista opcional de `permission_ids` (List[int]).
   - Modificar `POST /api/v1/roles` para que, al insertar un rol, también inserte los registros correspondientes en la tabla relacional `Role_Permissions`.
   - Modificar `GET /api/v1/roles` para que retorne también un array con los IDs de los permisos que posee cada rol.
3. **Frontend (index.html):** - Dentro del formulario `#create-role-form`, añadir un contenedor `<div id="permissions-container" class="mb-3"></div>` para los checkboxes.
4. **Frontend (app.js):** - Crear función `fetchPermissions()` que consuma el endpoint y genere dinámicamente un `<input type="checkbox">` por cada permiso disponible dentro de `#permissions-container`.
   - Modificar `createRole(e)` para iterar sobre los checkboxes seleccionados, extraer sus valores y enviarlos como `permission_ids` en el payload JSON.