---
description: social-pmo-ui
---

## Objetivo
Implementar avatares de usuario, visualización de roles en comentarios y estructura de diseño tipo red social.

## Pasos
1. **Base de Datos:** Añadir columna `profile_picture` (TEXT) a la tabla `Users`.
2. **API (main.py):** Actualizar el endpoint de comentarios del proyecto para que devuelva también el `role_name` del autor y su `profile_picture`.
3. **Frontend (app.js):** Crear una función helper `getAvatar(user)` que:
   - Devuelva un `<img>` si existe foto.
   - Devuelva un `<div>` con la inicial (ej. "E") y un color de fondo si no hay foto.
4. **Frontend (style.css):** Diseñar la clase `.comment-avatar` (circular, 40x40px) y el estilo de la inicial.
5. **UI:** Reestructurar el renderizado de comentarios para poner el avatar a la izquierda y el texto/nombre/rol a la derecha en una columna.