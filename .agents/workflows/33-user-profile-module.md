---
description: User Profile Self-Service Module
---

## Objetivo
Implementar un módulo de autogestión de perfil para que cualquier usuario autenticado (independientemente de su rol) pueda actualizar su nombre, URL de foto de perfil y contraseña.

## Tareas Backend (api/main.py)
1. Crear un endpoint `GET /api/v1/users/me` que devuelva los datos del usuario logueado actualmente (extrayendo el ID del token JWT).
2. Crear un endpoint `PUT /api/v1/users/me` que reciba y actualice dinámicamente `name`, `photo_url` y `password` (hasheando la nueva contraseña si es enviada) para el usuario autenticado.

## Tareas Frontend (app.js & index.html)
1. **Navbar:** Añadir un botón o enlace "Mi Perfil" en la barra de navegación (junto al botón de Cerrar Sesión).
2. **Modal:** Crear un `#profileModal` de Bootstrap con un formulario para editar Nombre, URL de Foto y Nueva Contraseña (opcional).
3. **Lógica JS:** Programar la función para abrir el modal precargando los datos actuales (`GET /me`) y la función para enviar las actualizaciones (`PUT /me`) con manejo de errores y validación.