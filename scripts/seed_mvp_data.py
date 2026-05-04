# -*- coding: utf-8 -*-
"""
scripts/seed_mvp_data.py
-----------------------
Poblamiento de datos ultra-realistas para el MVP PMO-RPA.
Genera 30 proyectos distribuidos entre los desarrolladores activos.
"""

import sqlite3
import random
import sys
from datetime import date, timedelta, datetime

DB_PATH = "data/pmo_rpa.db"

# ---------------------------------------------------------------------------
# Datos Maestros Realistas
# ---------------------------------------------------------------------------

PROCESS_NAMES = [
    "Conciliación Bancaria Mensual", "Onboarding RRHH - Nuevos Ingresos",
    "Lectura de Facturas OCR", "Cierre Contable Trimestral",
    "Automatización SAP MM", "Validación de Documentos de Identidad",
    "Carga Masiva de Datos CRM", "Reporte de Ventas Consolidado",
    "Gestión de Préstamos Automáticos", "Monitorización de Precios",
    "Automatización de Reclamos", "Procesamiento de Órdenes de Compra",
    "Generación de Certificados Digitales", "Auditoría de Gastos de Viaje",
    "Integración de Sistemas Legacy", "Bots de Atención a Clientes",
    "Analítica Predictiva de Bajas", "Automatización de Nómina",
    "Gestión de Inventario", "Soporte Técnico Nivel 1",
    "Extracción de Datos Portales Gov", "Seguimiento de Logística",
    "Flujo de Aprobaciones Internas", "Consolidación Financiera",
    "Validación de Compliance", "Generación de Leads B2B",
    "Análisis de Sentimiento RRSS", "Automatización de Backups",
    "Gestión de Vacaciones", "Actualización Precios E-commerce"
]

CLIENTS = [
    "Banco de la Nación", "Retail S.A.", "Seguros Horizonte", "Minería del Sur",
    "Logística Express", "TecnoMundo", "Farmacias Vida", "Energía Global",
    "Inmobiliaria Futuro", "Telecomunicaciones Unidas"
]

COMMENTS_PRESALES = [
    "Requisitos levantados con el cliente satisfactoriamente.",
    "El cliente aprobó el presupuesto inicial, procedemos con el diseño.",
    "Validada la factibilidad técnica con el equipo de TI del cliente.",
    "Documentación de preventa entregada al PMO.",
    "Kickoff agendado para la próxima semana."
]

COMMENTS_DEVS = [
    "Bloqueo por permisos en el servidor de base de datos SAP.",
    "Desarrollo de los primeros 3 flujos completado.",
    "Pasando a QA después de pruebas unitarias exitosas.",
    "Ajuste en la lógica de extracción por cambio en el portal web.",
    "Enviada solicitud de credenciales para ambiente de UAT.",
    "Refactorización del módulo de logs para mejorar performance."
]

COMMENTS_PMO = [
    "Revisar desviación de horas en la fase de desarrollo.",
    "Aprobado el pase a producción tras UAT exitoso.",
    "Cliente solicita cambio de alcance menor, evaluando impacto.",
    "Status semanal: Proyecto en curso según cronograma.",
    "Escalación de bloqueo de accesos a la gerencia de TI."
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def d(days_offset):
    return (date.today() + timedelta(days=days_offset)).isoformat()

# ---------------------------------------------------------------------------
# Main Script
# ---------------------------------------------------------------------------

def main():
    print("🚀 Iniciando Seed de Datos Realistas para el MVP...")
    
    conn = get_db()
    cursor = conn.cursor()

    # 1. Validar pre-requisitos
    try:
        # Obtener Developers
        cursor.execute("SELECT u.id, u.name FROM Users u JOIN Roles r ON u.role_id = r.id WHERE r.name = 'Developer' AND u.is_active = 1")
        devs = cursor.fetchall()
        
        # Obtener Pre-sales (buscamos por nombre de rol exacto o que contenga 'sales')
        cursor.execute("SELECT u.id, u.name FROM Users u JOIN Roles r ON u.role_id = r.id WHERE (r.name = 'Pre-sales' OR r.name LIKE '%sales%') AND u.is_active = 1")
        presales = cursor.fetchall()
        
        # Obtener Project Types
        cursor.execute("SELECT id, name FROM Project_Types")
        types = cursor.fetchall()
        
        # Obtener PMO (para comentarios)
        cursor.execute("SELECT u.id, u.name FROM Users u JOIN Roles r ON u.role_id = r.id WHERE r.name = 'PMO' AND u.is_active = 1")
        pmos = cursor.fetchall()

        if len(devs) < 3 or len(presales) < 2 or len(types) < 4:
            print("\n❌ ERROR: Faltan datos base en la base de datos.")
            print(f"   - Developers encontrados: {len(devs)} (se requieren 3)")
            print(f"   - Pre-sales encontrados: {len(presales)} (se requieren 2)")
            print(f"   - Project Types encontrados: {len(types)} (se requieren 4)")
            print("\n💡 Por favor, crea los usuarios y tipos de proyecto faltantes desde la interfaz de administración antes de ejecutar este script.")
            return

    except sqlite3.Error as e:
        print(f"❌ Error al consultar la base de datos: {e}")
        return

    # 2. Confirmación de no duplicidad
    cursor.execute("SELECT COUNT(*) FROM Projects WHERE is_deleted = 0")
    count = cursor.fetchone()[0]
    if count > 10:
        confirm = input(f"⚠️ Ya existen {count} proyectos activos en la base de datos. ¿Deseas continuar inyectando 30 más? (s/n): ")
        if confirm.lower() != 's':
            print("Operación cancelada.")
            return

    print(f"✅ Pre-requisitos cumplidos. Generando 30 proyectos para {len(devs)} desarrolladores...")

    # 3. Generación de Proyectos
    project_count = 0
    random.shuffle(PROCESS_NAMES)
    
    # Repartir 10 proyectos por cada uno de los 3 primeros devs
    target_devs = devs[:3]
    
    for dev in target_devs:
        print(f"   - Creando proyectos para {dev['name']}...")
        for i in range(10):
            process_base = PROCESS_NAMES[project_count]
            client = random.choice(CLIENTS)
            process_name = f"{process_base} — {client}"
            
            p_type = random.choice(types)
            p_commercial = random.choice(presales)
            
            # Lógica de fechas
            start_offset = random.randint(-60, 0)
            duration = random.randint(30, 90)
            start_date = d(start_offset)
            end_date = d(start_offset + duration)
            
            # Health status aleatorio pero con tendencia a Green
            health = random.choices(["Green", "Yellow", "Red"], weights=[70, 20, 10])[0]
            
            cursor.execute(
                """INSERT INTO Projects (process_name, project_type_id, assigned_developer_id, commercial_id, start_date, estimated_end_date, health_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (process_name, p_type['id'], dev['id'], p_commercial['id'], start_date, end_date, health)
            )
            project_id = cursor.lastrowid
            
            # 4. Inyectar fases según plantilla
            cursor.execute("SELECT phase_name, weight_percentage FROM Phase_Templates WHERE project_type_id = ? ORDER BY id", (p_type['id'],))
            templates = cursor.fetchall()
            
            if not templates:
                # Fallback si no hay plantillas
                templates = [
                    {"phase_name": "Discovery", "weight_percentage": 20},
                    {"phase_name": "Diseño", "weight_percentage": 20},
                    {"phase_name": "Desarrollo", "weight_percentage": 40},
                    {"phase_name": "UAT", "weight_percentage": 20}
                ]
            
            num_phases = len(templates)
            # Decidir cuantas fases están completadas para el avance realista
            # Proyectos más viejos tienden a estar más avanzados
            if start_offset < -45:
                completed_up_to = random.randint(num_phases // 2, num_phases)
            elif start_offset < -20:
                completed_up_to = random.randint(1, num_phases // 2)
            else:
                completed_up_to = 0
            
            phase_ids = []
            for idx, temp in enumerate(templates):
                status = "Pending"
                completion_date = None
                
                if idx < completed_up_to:
                    status = "Completed"
                    # Fecha de término aproximada
                    comp_offset = start_offset + (idx + 1) * (duration // num_phases)
                    completion_date = d(min(comp_offset, 0))
                elif idx == completed_up_to:
                    status = "In Progress"
                
                # Fechas de fase
                p_start = start_offset + idx * (duration // num_phases)
                p_end = start_offset + (idx + 1) * (duration // num_phases)
                
                cursor.execute(
                    """INSERT INTO Phases (project_id, phase_name, weight_percentage, status, start_date, estimated_end_date, completion_date, display_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (project_id, temp['phase_name'], temp['weight_percentage'], status, d(p_start), d(p_end), completion_date, idx)
                )
                phase_ids.append((cursor.lastrowid, temp['phase_name'], status, p_start, p_end))

            # 5. Añadir comentarios realistas
            for ph_id, ph_name, ph_status, ph_start, ph_end in phase_ids:
                # 10% de probabilidad de tener comentario en cualquier fase
                if random.random() < 0.3:
                    # Comentario de Pre-sales (solo en las 2 primeras fases)
                    if ph_id == phase_ids[0][0] or ph_id == phase_ids[1][0]:
                        comment_text = random.choice(COMMENTS_PRESALES)
                        comment_date = d(ph_start + 1) + "T10:00:00"
                        cursor.execute("INSERT INTO Phase_Comments (phase_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
                                     (ph_id, p_commercial['id'], comment_text, comment_date))
                    
                    # Comentario de Dev (en fases de Desarrollo/QA/UAT)
                    if any(x in ph_name.lower() for x in ["desarrollo", "pruebas", "qa", "uat"]):
                        if ph_status != "Pending":
                            comment_text = random.choice(COMMENTS_DEVS)
                            comment_date = d(ph_start + 2) + "T15:30:00"
                            cursor.execute("INSERT INTO Phase_Comments (phase_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
                                         (ph_id, dev['id'], comment_text, comment_date))
                    
                    # Comentario de PMO (en cualquier fase)
                    if random.random() < 0.2 and pmos:
                        pmo = random.choice(pmos)
                        comment_text = random.choice(COMMENTS_PMO)
                        comment_date = d(ph_start + 3) + "T09:00:00"
                        cursor.execute("INSERT INTO Phase_Comments (phase_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
                                     (ph_id, pmo['id'], comment_text, comment_date))

            project_count += 1
            if project_count >= 30:
                break
        if project_count >= 30:
            break

    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ SEED EXITOSO: 30 Proyectos inyectados correctamente.")
    print(f"   - Proyectos totales: {project_count}")
    print("   - Fases y comentarios generados según reglas de negocio.")
    print("="*50)
    print("\nYa puedes ver los datos actualizados en el Dashboard.")

if __name__ == "__main__":
    main()
