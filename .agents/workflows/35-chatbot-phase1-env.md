---
description: Chatbot AI PMO - Fase 1 (Dependencias y Entorno)
---

## 🎯 Objetivo de la Fase
Preparar el entorno backend (FastAPI) para soportar la integración de un motor Text-to-SQL utilizando LangChain y el LLM Anthropic Claude 3 Haiku. En esta fase NO se tocará la base de datos ni el frontend. El foco es estrictamente a nivel de dependencias e inyección de configuración segura.

## 🛠️ Tareas Arquitectónicas

1. **Actualización de Dependencias (`requirements.txt`):**
   - Añadir `langchain` y `langchain-community` (para las herramientas de conexión a SQLite).
   - Añadir `langchain-anthropic` (el SDK oficial para conectar con Claude 3 Haiku).
   - Asegurar que `python-dotenv` esté presente (para lectura segura de credenciales).

2. **Gestión de Entorno (`.env` y configuración):**
   - Actualizar el archivo de configuración central (donde se manejen las variables de entorno, por ejemplo en `api/main.py` o un archivo `config.py` si existe) para leer de forma segura la variable:
     - `LLM_API_KEY`: La llave de acceso a Anthropic.
   - Crear o actualizar un archivo `.env.example` en la raíz del proyecto para documentar esta nueva variable (`LLM_API_KEY=tu_api_key_aqui`) para el resto del equipo.

3. **Validación de Inicio (Health Check interno):**
   - Añadir un pequeño print o log de validación al arrancar el servidor (en `api/main.py` o `api/__init__.py`) que verifique la existencia de `LLM_API_KEY`.
   - Si la variable NO existe, debe imprimir un mensaje tipo WARNING indicando que el módulo de Chatbot estará inactivo, pero **sin interrumpir el arranque del servidor**.

## 🛑 Restricciones y Reglas
- **Zero-Breakage:** La aplicación actual (Rutas de proyectos, Fases, Autenticación, Gantt) debe seguir funcionando exactamente igual. No se debe modificar ninguna ruta existente.
- **Aislamiento:** No crear aún endpoints nuevos ni lógica de chat. Solo preparación de terreno.