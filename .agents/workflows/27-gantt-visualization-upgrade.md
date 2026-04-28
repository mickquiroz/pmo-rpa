---
description: gantt-visualization-upgrade
---

## Objetivo
Mejorar radicalmente la UI/UX del diagrama Gantt (Frappe Gantt) para solucionar problemas de escala (textos cortados en fases cortas) y añadir estética profesional (colores por estado y cuadrícula tipo cebra).

## Pasos
1. Modificar `frontend/index.html` para añadir un grupo de botones (Día, Semana, Mes) dentro del modal del Gantt para controlar el zoom (view_mode).
2. Modificar `frontend/app.js` en la función `showProjectGantt()` para:
   - Soportar el cambio dinámico de `view_mode` mediante los botones.
   - Asignar una clase CSS dinámica a cada tarea (task.custom_class) basada en su `status` (Completed, In Progress, Pending).
3. Modificar `frontend/style.css` (o inyectar estilos) para:
   - Crear el efecto de cuadrícula tipo "cebra" en el fondo del Gantt.
   - Definir los colores para las clases de estado (ej. verde para completado, azul para progreso, gris para pendiente).
   - Asegurar que el texto de las barras pequeñas no se oculte (overflow visible).