---
description: Realistic MVP Data Seeding
---

## Objetivo
Crear un script en Python (`scripts/seed_mvp_data.py`) que genere un volumen de datos realista (30 proyectos) para la presentación final del MVP, respetando la estructura de fases, roles y lógica temporal.

## Reglas de Negocio para la Generación
1. **Distribución:** Crear exactamente 10 proyectos por cada Developer activo (total 30).
2. **Asignación Comercial:** Asignar aleatoriamente uno de los comerciales (Pre-sales) a cada proyecto.
3. **Tipos de Proyecto:** Distribuir aleatoriamente entre los 4 tipos existentes (RPA, RPA + IA, Web, Chatbot IA).
4. **Nombres Realistas:** Usar un array de nombres de procesos corporativos reales (ej. "Conciliación Bancaria", "Onboarding RRHH", "Lectura Facturas OCR", "Cierre Contable", "Automatización SAP MM", etc.).
5. **Fechas y Avance:** - Las fechas de inicio deben ser aleatorias entre hace 2 meses y la fecha actual.
   - Establecer el estado de las fases en cascada (las primeras 'Completed', la actual 'In Progress', las futuras 'Pending') para simular un `% de avance` realista (ej. algunos al 10%, otros al 60%, un par al 100%).
   - Asignar `health_status` acorde a la fecha actual vs `estimated_end_date` (Green, Yellow, Red).
6. **Simulación de Comentarios (Crucial):**
   - **Pre-sales:** Solo comentan en las 2 primeras fases (ej. "Requisitos levantados con el cliente", "El cliente aprobó el presupuesto, procedemos").
   - **Developers:** Comentan en las fases de desarrollo y pruebas (ej. "Bloqueo por permisos en SAP", "Desarrollo completado, pasando a QA").
   - **PMO (Admin):** Comentan en cualquier fase (ej. "Aprobado para pase a producción", "Revisar desviación de horas").
   - Las fechas de los comentarios deben tener coherencia temporal con las fechas de la fase.

## Ejecución
- El script debe conectarse a `data/pmo_rpa.db` usando la sesión de SQLAlchemy (`api.database.SessionLocal`).
- Debe incluir un flag o confirmación para no duplicar datos si se corre dos veces.