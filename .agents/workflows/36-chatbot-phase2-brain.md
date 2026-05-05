---
description: Chatbot AI PMO - Fase 2 (Motor Text-to-SQL)
---

## 🎯 Objetivo de la Fase
Construir la capa de servicio (Service Layer) que alojará la lógica de LangChain y Anthropic Claude 3 Haiku para traducir lenguaje natural a consultas SQLite y devolver respuestas analíticas. Todo esto debe ejecutarse de forma aislada sin modificar aún los endpoints de FastAPI.

## 🛠️ Tareas Arquitectónicas

1. **Crear el Servicio de Chatbot (`api/services/chatbot_service.py`):**
   - Importar las herramientas necesarias de `langchain_community.utilities` (SQLDatabase), `langchain_anthropic` (ChatAnthropic), y herramientas para agentes SQL (`create_sql_agent`, `SQLDatabaseToolkit`).
   - Crear una clase o módulo `PMOAssistant` que:
     - Inicialice la conexión a la base de datos de solo lectura de esquemas (`sqlite:///data/pmo_rpa.db`).
     - Inicialice el LLM de Anthropic (`model="claude-3-haiku-20240307"`).
     - Defina un System Prompt estricto: "Eres un Asistente Director PMO experto en RPA. Tu base de datos tiene proyectos, fases, usuarios y roles. Debes responder a las preguntas de negocio construyendo y ejecutando consultas SQL seguras (solo lectura). Responde de manera profesional y resumida."
     - Exponga un método principal, por ejemplo: `def ask_bot(question: str) -> str:` que ejecute la cadena de LangChain y retorne la respuesta en lenguaje natural.

2. **Crear un Script de Prueba Local (`scripts/test_chatbot.py`):**
   - Para evitar tocar `main.py` todavía, crear un pequeño script de Python en la carpeta `scripts/` que inicialice el `PMOAssistant` y permita hacer una pregunta de prueba por consola (ej. "¿Cuántos proyectos tenemos en total y cuántos están retrasados?").
   - Esto servirá como prueba de humo (smoke test) para validar que Haiku razona correctamente con el esquema de SQLite.

## 🛑 Restricciones y Reglas
- **Seguridad:** El agente SQL NUNCA debe ejecutar sentencias de tipo `DROP`, `DELETE`, `UPDATE` o `INSERT`. Asegurar esto a través del prompt o la configuración de LangChain.
- **Aislamiento:** NO tocar el `main.py`, NO crear rutas de FastAPI, y NO tocar el frontend en esta fase.