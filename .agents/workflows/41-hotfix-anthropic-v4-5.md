---
description: Hotfix V3 - Salto a Claude 4.5 Haiku
---

## 🎯 Objetivo
Solucionar los errores `404 not_found_error` escalando el motor de LangChain directamente a la versión más avanzada y estable de Anthropic: **Claude 4.5 Haiku**, garantizando la conexión a los servidores actuales.

## 🛠️ Tareas Arquitectónicas

1. **Actualización en el Servicio de IA (`api/services/chatbot_service.py`):**
   - Localizar la inicialización del LLM (`ChatAnthropic`).
   - Cambiar el parámetro del modelo por el identificador de la nueva generación: `model="claude-4-5-haiku-latest"` (o el string oficial de la v4.5 que soporte la librería actual).

2. **Validación:**
   - Asegurarse de no modificar el System Prompt, ni la inyección de la base de datos, ni la configuración del agente. Es un reemplazo directo del string de la versión.