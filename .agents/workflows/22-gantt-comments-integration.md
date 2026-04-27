---
description: Integración Interactiva Gantt-Comentarios
---

**Objetivo:** Conectar el motor visual de la Carta Gantt con el módulo de auditoría de comentarios, permitiendo al usuario hacer clic en cualquier barra (fase) del Gantt para abrir su historial de comentarios y añadir nuevos.

**Pasos a ejecutar por el Agente:**
1. **app.js (Modificar Gantt):** En la función `showProjectGantt()`, localizar la instanciación de la clase `Gantt` (ej. `new Gantt('#gantt-target', tasks, { ... })`).
2. **app.js (Evento on_click):** Añadir la propiedad `on_click` a las opciones de configuración del Gantt. 
3. **app.js (Parsear ID):** Dentro del callback `on_click(task)`, extraer el ID real de la fase. Recordar que los IDs en el Gantt se están inyectando como `"Phase_" + p.id`. Se debe hacer un split o replace para obtener el número entero.
4. **app.js (Invocar Modal):** Llamar a la función existente `openPhaseComments(phaseId)` pasando el ID extraído. Esta función ya se encarga de hacer el fetch de los comentarios y abrir el `#phaseCommentsModal` de Bootstrap.
5. **UI Stack (Precaución):** Asegurar que Bootstrap 5 pueda abrir el modal de comentarios por encima del modal del Gantt sin romper el scroll o el backdrop oscuro.