---
description: Panel de SuperAdmin (Frontend)
---

**Objetivo:** Actualizar `frontend/index.html` y `frontend/app.js` para consumir los nuevos endpoints administrativos (Roles y Tipos de Proyecto) creados en la Fase 16.

**Pasos a ejecutar por el Agente:**
1. **HTML - Nuevos Modales:** En `index.html`, crear dos nuevos modales de Bootstrap: uno para "Administrar Roles" y otro para "Administrar Tipos de Proyecto". Cada uno debe tener una tabla para listar y un pequeño formulario para crear nuevos.
2. **HTML - Botones de Acceso:** Añadir los botones para abrir estos modales en la barra de navegación superior (Navbar).
3. **JS - Control de Acceso UI:** En `app.js`, dentro de la función `checkAuth()` (donde decodificamos el JWT), asegurar que los botones de "Administrar Roles" y "Administrar Tipos de Proyecto" SOLO sean visibles si el rol es "Admin".
4. **JS - Lógica de Consumo (Roles):** Crear las funciones `fetchRoles()` y `createRole()` que consuman `GET` y `POST` a `/api/v1/roles`. Renderizar los resultados en su respectivo modal.
5. **JS - Lógica de Consumo (Project Types):** Crear las funciones `fetchProjectTypes()` y `createProjectType()` que consuman `GET` y `POST` a `/api/v1/project-types`. Renderizar en su modal.