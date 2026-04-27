---
description: Gestión Completa de Roles (Edición y Eliminación)
---

**Objetivo:** Completar el ciclo CRUD para la gestión de roles en el panel SuperAdmin, permitiendo modificar los permisos de un rol existente y eliminar roles que no estén en uso.

**Pasos a ejecutar por el Agente:**
1. **Backend (Edición - PUT):**
   - Crear endpoint `PUT /api/v1/roles/{role_id}` en `main.py`.
   - Lógica: Actualizar `name` y `description` en la tabla `Roles`. 
   - Lógica Permisos: Borrar los registros anteriores en `Role_Permissions` para ese `role_id` e insertar los nuevos `permission_ids` recibidos en el payload.
2. **Backend (Eliminación - DELETE):**
   - Crear endpoint `DELETE /api/v1/roles/{role_id}` en `main.py`.
   - Lógica de Protección: Verificar si existen usuarios (activos o inactivos) que tengan asignado este `role_id`. Si existen, rechazar la petición (HTTP 400) para mantener la integridad referencial. Si no, borrar el rol (sus permisos en `Role_Permissions` se borrarán por la cascada configurada en SQLite).
3. **Frontend (UI - index.html):**
   - Añadir una columna "Acciones" en la tabla `#roles-table-body`.
4. **Frontend (Lógica - app.js):**
   - Inyectar botones "Editar" y "Eliminar" en cada fila de la tabla de roles.
   - **Función Editar:** Al hacer clic, cambiar el título del formulario a "Editar Rol", poblar los inputs con los datos del rol, marcar automáticamente los checkboxes correspondientes a sus permisos actuales, y cambiar el comportamiento del *submit* para hacer un `PUT` en lugar de un `POST`.
   - **Función Eliminar:** Al hacer clic, pedir confirmación y hacer un `DELETE`, manejando correctamente el error si el backend informa que el rol está en uso.