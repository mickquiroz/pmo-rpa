---
description: Hotfix V4 - Aplanamiento de Salida de Anthropic
---

## 🎯 Objetivo
Solucionar el error de validación HTTP 503 en el endpoint `/api/v1/chat`. Las nuevas versiones de los modelos de Anthropic (Claude 4.5) devuelven el parámetro `output` como una lista de diccionarios (content blocks) en lugar de un string plano. FastAPI/Pydantic falla al intentar parsear esta lista.

## 🛠️ Tareas Arquitectónicas

1. **Actualización en el Servicio de IA (`api/services/chatbot_service.py`):**
   - Localizar el método `ask_bot(self, question: str) -> str`.
   - Después de obtener el output (`response.get("output", ...)`), añadir una lógica para verificar si el output es una lista (`isinstance(output, list)`).
   - Si es una lista, iterar sobre ella y extraer el valor de la clave `"text"` de cada bloque, concatenándolos en un solo string plano.
   - Retornar el string plano.

Ejemplo de la lógica a inyectar:
```python
output = response.get("output", "No se pudo generar una respuesta.")
if isinstance(output, list):
    output = "".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in output])
return str(output)