---
description: Chatbot AI PMO - Fase 4 (Frontend UI)
---

## 🎯 Objetivo de la Fase
Construir la interfaz gráfica para el Asistente IA de la PMO. Se implementará como un widget flotante en la esquina inferior derecha de la aplicación web, permitiendo a los usuarios autenticados interactuar con el endpoint `/api/v1/chat` sin abandonar la vista del dashboard o Gantt.

## 🛠️ Tareas Arquitectónicas

1. **Estructura HTML (`frontend/index.html`):**
   - Añadir un contenedor flotante (Widget) justo antes de cerrar el `</body>`.
   - El widget debe tener dos estados: 
     - Contraído: Un botón circular flotante con un ícono de chat o robot.
     - Expandido: Una ventana de chat tipo panel con un header (título y botón de cerrar), un área de historial de mensajes (scrollable) y un área de input (campo de texto y botón de enviar).

2. **Estilos CSS (`frontend/style.css`):**
   - Estilizar el botón flotante (posición fija abajo a la derecha, z-index alto para no ser tapado por modales o el Gantt).
   - Estilizar la ventana de chat (sombra, bordes redondeados, altura máxima).
   - Crear estilos visuales distintos para las burbujas de mensaje del Usuario (ej. alineado a la derecha, color primario) y las burbujas del Asistente (ej. alineado a la izquierda, color gris claro).

3. **Lógica JavaScript (`frontend/app.js`):**
   - **UI Toggle:** Función para abrir y cerrar la ventana de chat al hacer clic en el botón flotante.
   - **Renderizado de Mensajes:** Función para inyectar mensajes en el contenedor de historial.
   - **Integración API:** Función para enviar el mensaje del usuario al backend:
     - Debe hacer un `fetch` a `POST /api/v1/chat`.
     - **Crítico:** Debe incluir el header `Authorization: Bearer ${localStorage.getItem('token')}`.
     - Mostrar un indicador de "Pensando..." o un spinner en el chat mientras el backend responde.
     - Capturar la respuesta y renderizarla. Manejar también posibles errores (ej. mostrar en rojo "Error de conexión" si el backend falla).

## 🛑 Restricciones y Reglas
- **No Intrusivo:** El widget de chat no debe romper el layout actual del Gantt ni de las tablas.
- **Seguridad Frontend:** Solo debe mostrarse/funcionar si el usuario está logueado (si hay token).