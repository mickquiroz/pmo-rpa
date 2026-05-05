---
description: Hotfix - Actualización de Modelo Anthropic
---

## 🎯 Objetivo
Solucionar el error `404 not_found_error` en la API de Anthropic. El modelo `claude-3-haiku-20240307` ha sido retirado oficialmente por el proveedor, por lo que el sistema debe migrar a la versión más reciente compatible.

## 🛠️ Tareas Arquitectónicas

1. **Actualización en el Servicio de IA (`api/services/chatbot_service.py`):**
   - Localizar la inicialización del LLM (`ChatAnthropic`).
   - Cambiar el parámetro `model="claude-3-haiku-20240307"` por el modelo vigente: `model="claude-3-5-haiku-20241022"`.

2. **Validación:**
   - Asegurarse de que no se modifique nada más en el agente de LangChain ni en los prompts. Es estrictamente un cambio en el nombre de la variable del modelo.