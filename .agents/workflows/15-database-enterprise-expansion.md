---
description: Expansión Empresarial del Modelo de Datos
---

**Objetivo:** Refactorizar la base de datos relacional (SQLite) para soportar RBAC dinámico, tipos de proyectos, plantillas de fases, comentarios y borrado lógico (soft delete).

**Pasos a ejecutar por el Agente:**
1. Analizar el esquema actual en `init_db.py`.
2. Crear la tabla `Roles` y `Permissions` (relación muchos a muchos). Migrar los roles "Admin", "PMO", "Developer" a esta tabla, y añadir "Pre-Sales Viewer".
3. Crear la tabla `Project_Types` (ej. RPA, RPA + IA, Web).
4. Crear la tabla `Phase_Templates` vinculada a `Project_Types` para definir las fases estándar por tipo.
5. Modificar la tabla `Projects` para incluir `project_type_id`, `commercial_id` (foreign key a Users) y un flag `is_deleted` (booleano para el backlog).
6. Crear la tabla `Phase_Comments` vinculada a `Phases` y `Users` para el registro de auditoría y bloqueantes.
7. Actualizar los datos semilla (seed data) en `init_db.py` para reflejar la nueva estructura y ejecutar el script para recrear la base de datos localmente.