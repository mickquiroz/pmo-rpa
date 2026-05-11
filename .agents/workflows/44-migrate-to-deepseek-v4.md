---
description: Migración de Cerebro LLM (Anthropic -> DeepSeek-V4)
---

**Objetivo:** Cambiar el motor de Inteligencia Artificial del chatbot de Anthropic Claude a DeepSeek-V4-Flash para optimizar costos y velocidad.

## Tareas Técnicas:
1. **Dependencias:** Asegurar que `openai` esté en el `requirements.txt` (ya que DeepSeek usa su SDK).
2. **Variables de Entorno:** - Preparar el sistema para leer `DEEPSEEK_API_KEY` (puedes reutilizar la lógica de `LLM_API_KEY` del .env).
   - Configurar la URL base: `https://api.deepseek.com`.
3. **Refactorización de `chatbot_service.py`:**
   - Reemplazar `ChatAnthropic` por `ChatOpenAI`.
   - Apuntar el modelo a `deepseek-v4-flash`.
   - Ajustar el "Hotfix" de salida (DeepSeek suele devolver strings directos, no bloques de contenido como Claude 4.5).
4. **Validación:** Ejecutar `scripts/test_chatbot.py` para asegurar que el agente SQL sigue respondiendo correctamente.