---
description: Data Seeding (Preparación para Demo Ejecutiva)
---

**Objetivo:** Crear un script independiente en Python que limpie la base de datos actual (o la recree) y la pueble con datos realistas orientados a una demostración comercial.

**Pasos a ejecutar por el Agente:**
1. **Crear script `seed_demo.py`:** Este archivo debe ubicarse en la raíz del proyecto.
2. **Conexión a DB:** Conectarse a `data/pmo_rpa.db`.
3. **Limpieza (Opcional/Segura):** Borrar los proyectos, fases y comentarios existentes para empezar con un lienzo limpio, respetando a los usuarios, roles y tipos de proyecto.
4. **Inyección de Datos Realistas:**
   - Crear 1 proyecto "RPA" (ej. "Conciliación Bancaria Automática") en estado 'Green' con progreso al 50%.
   - Crear 1 proyecto "RPA + IA" (ej. "Lectura Automática de Facturas") en estado 'Yellow', con su fase de 'Design' atrasada.
   - Crear 1 proyecto "Chatbot IA" (ej. "Helpdesk Bot RRHH") en estado 'Red', apenas iniciando.
   - Inyectar fases coherentes para cada proyecto usando los tipos de proyecto existentes.
   - Inyectar al menos 3 o 4 comentarios en las fases atrasadas simulando interacción real entre el Developer y el PMO (ej. "Retraso por falta de accesos a SAP").
5. **Ejecución:** Ejecutar el script automáticamente para que la DB quede lista.