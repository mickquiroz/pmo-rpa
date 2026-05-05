---
description: Chatbot AI PMO - Fase 3 (API Endpoint Seguro)
---

## 🎯 Objetivo de la Fase
Exponer el motor de Inteligencia Artificial (`chatbot_service.py`) a través de un endpoint REST en FastAPI. Este endpoint debe estar estrictamente protegido por el sistema de autenticación JWT existente para garantizar que solo los miembros autorizados de la PMO interactúen con la base de datos.

## 🛠️ Tareas Arquitectónicas

1. **Modelos de Datos (Pydantic):**
   - En `api/main.py`, crear los esquemas de entrada y salida para el chat:
     - `ChatRequest`: Modelo que reciba un campo `message` (str).
     - `ChatResponse`: Modelo que devuelva un campo `reply` (str).

2. **Creación del Endpoint en `api/main.py`:**
   - Importar la función `get_assistant` desde `api.services.chatbot_service`.
   - Añadir una nueva ruta: `POST /api/v1/chat`
   - Etiquetar la ruta con `tags=["AI Assistant"]`.
   - **Seguridad Obligatoria:** Inyectar la dependencia `current_user: dict = Depends(get_current_user)` en los parámetros de la función para asegurar que solo usuarios logueados (con token JWT válido) puedan consumir el servicio.

3. **Lógica del Endpoint:**
   - Instanciar el asistente llamando a `get_assistant()`.
   - Ejecutar `assistant.ask_bot(payload.message)`.
   - Manejar posibles excepciones (por ejemplo, si la API Key de Anthropic no está configurada o hay un error de conexión) devolviendo un `HTTPException` con status `503 Service Unavailable` o `500 Internal Server Error`.

## 🛑 Restricciones y Reglas
- **Zero-Breakage:** No modificar ninguna ruta existente de proyectos, fases o usuarios.
- **Seguridad:** Bajo ninguna circunstancia este endpoint debe ser público. 
- **Aislamiento Frontend:** NO tocar `app.js`, `index.html` ni CSS en esta fase. Solo inyectar el endpoint backend.