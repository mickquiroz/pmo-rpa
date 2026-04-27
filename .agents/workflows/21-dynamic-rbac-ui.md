---
description: UI Dinámica Basada en Permisos (Token JWT)
---

**Objetivo:** Refactorizar el motor de autenticación para que el Token JWT incluya los permisos del usuario, y actualizar el Frontend para que la interfaz se construya dinámicamente evaluando estos permisos en lugar de hardcodear el nombre del rol.

**Pasos a ejecutar por el Agente:**
1. **Backend (Token JWT):** - Modificar el endpoint `POST /api/v1/auth/token` en `main.py`.
   - Antes de generar el token, hacer una consulta SQL haciendo un JOIN entre `Role_Permissions` y `Permissions` para obtener la lista de `actions` (ej. `["write:projects", "delete:projects"]`) que le corresponden al `role_id` del usuario.
   - Inyectar este array bajo la clave `"permissions"` en el payload del JWT.
2. **Frontend (Autenticación):**
   - En `app.js`, dentro de `handleLogin()`, extraer la clave `permissions` del payload decodificado y guardarla en `localStorage`.
   - Modificar `checkAuth()` para cargar estos permisos en una variable global `currentUserPermissions = []`.
3. **Frontend (UI Dinámica):**
   - Refactorizar completamente `applyRoleUI()`. Eliminar las validaciones tipo `if (currentUserRole === 'Admin')`.
   - Reemplazar por validaciones dinámicas: ej. mostrar el botón de "Crear Proyecto" SOLO si `currentUserPermissions.includes('write:projects')`.
   - Asegurarse de ocultar los botones de administración (Usuarios, Roles, Tipos) si no se tienen los permisos administrativos correspondientes (puedes asumir un permiso 'admin:all' o validar por rol 'Admin' SOLO para ese panel superior, pero para las acciones operativas usar los permisos granulares).
4. **Frontend (Restricciones en Tablas):**
   - Aplicar esta misma lógica de `includes()` para ocultar los botones de "Eliminar" en la tabla de proyectos y "Eliminar" en la tabla de fases.