// app.js

let currentRole = 'PMO';

document.addEventListener('DOMContentLoaded', () => {
    fetchProjects();

    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', () => {
            window.open('/api/v1/reports/export', '_blank');
        });
    }

    const roleSelect = document.getElementById('role-select');
    if (roleSelect) {
        roleSelect.addEventListener('change', (e) => {
            currentRole = e.target.value;
            applyRoleUI();
        });
        applyRoleUI();
    }

    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', handleCreateProject);
    }
});

async function fetchProjects() {
    const errorContainer = document.getElementById('error-container');
    errorContainer.innerHTML = '';
    
    try {
        const response = await fetch('/api/v1/projects');
        if (!response.ok) {
            throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
        }
        const projects = await response.json();
        renderProjects(projects);
    } catch (error) {
        console.error('Error al obtener los proyectos:', error);
        
        // Show error in UI
        errorContainer.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>Error de conexión:</strong> No se pudo conectar con el servidor backend o ha ocurrido un problema al cargar los datos.
            </div>
        `;
    }
}

function renderProjects(projects) {
    const tbody = document.getElementById('projects-table-body');
    tbody.innerHTML = '';

    if (!projects || projects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay proyectos registrados.</td></tr>';
        return;
    }

    projects.forEach(project => {
        const tr = document.createElement('tr');
        
        // Health Status Badge/Color formatting
        let healthClass = '';
        let healthIcon = '';
        if (project.health_status === 'Green') {
            healthClass = 'health-Green';
            healthIcon = '🟢';
        } else if (project.health_status === 'Yellow') {
            healthClass = 'health-Yellow';
            healthIcon = '🟡';
        } else if (project.health_status === 'Red') {
            healthClass = 'health-Red';
            healthIcon = '🔴';
        } else {
            healthClass = 'text-secondary';
            healthIcon = '⚪';
        }

        // Progress bar formatting
        const progressPercentage = Math.round(project.progress_percentage);
        let progressColorClass = 'bg-primary';
        if (progressPercentage === 100) {
            progressColorClass = 'bg-success';
        }

        tr.innerHTML = `
            <td class="fw-semibold text-dark">${project.process_name}</td>
            <td class="text-secondary">${project.developer_name}</td>
            <td class="${healthClass}">${healthIcon} ${project.health_status}</td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="progress flex-grow-1">
                        <div class="progress-bar ${progressColorClass}" role="progressbar" style="width: ${progressPercentage}%;" aria-valuenow="${progressPercentage}" aria-valuemin="0" aria-valuemax="100">${progressPercentage}%</div>
                    </div>
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="showProjectGantt(${project.id}, '${project.process_name}')">Ver Gantt</button>
                <button class="btn btn-sm btn-outline-secondary" onclick="openManagePhases(${project.id})">Editar Fases</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function showProjectGantt(projectId, projectName) {
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/phases`);
        if (!response.ok) {
            throw new Error('No se pudieron obtener las fases');
        }
        const phases = await response.json();

        const ganttTarget = document.getElementById('gantt-target');
        ganttTarget.innerHTML = '';

        if (!phases || phases.length === 0) {
            ganttTarget.innerHTML = '<p class="text-muted p-3">No hay fases para este proyecto.</p>';
        } else {
            const tasks = phases.map(p => {
                let progress = 0;
                if (p.status === 'Completed') progress = 100;
                else if (p.status === 'In Progress') progress = 50;
                
                return {
                    id: `Phase_${p.id}`,
                    name: p.phase_name,
                    start: p.start_date,
                    end: p.estimated_end_date,
                    progress: progress,
                    dependencies: ''
                };
            });

            new Gantt('#gantt-target', tasks, {
                view_mode: 'Month',
                language: 'es',
                custom_popup_html: function(task) {
                    return `
                        <div class="p-2 bg-white shadow-sm border rounded">
                            <h6 class="fw-bold mb-1">${task.name}</h6>
                            <p class="mb-0 text-muted small">Progreso: ${task.progress}%</p>
                        </div>
                    `;
                }
            });
        }

        document.getElementById('ganttModalLabel').innerText = `Diagrama Gantt: ${projectName}`;
        const modal = new bootstrap.Modal(document.getElementById('ganttModal'));
        modal.show();

    } catch (error) {
        console.error('Error al cargar Gantt:', error);
        alert('Ocurrió un error al cargar el diagrama de Gantt.');
    }
}

function applyRoleUI() {
    const btnCreate = document.getElementById('btn-create-project');
    const btnExport = document.getElementById('btn-export');

    if (currentRole === 'Admin' || currentRole === 'PMO') {
        if (btnCreate) btnCreate.style.display = 'inline-block';
        if (btnExport) btnExport.style.display = 'inline-block';
    } else {
        if (btnCreate) btnCreate.style.display = 'none';
        if (btnExport) btnExport.style.display = 'none';
    }
}

async function handleCreateProject(event) {
    event.preventDefault();

    const processName = document.getElementById('process-name').value;
    const assignedDeveloperId = parseInt(document.getElementById('assigned-developer').value, 10);
    const startDate = document.getElementById('start-date').value;
    const estimatedEndDate = document.getElementById('estimated-end-date').value;

    const projectData = {
        process_name: processName,
        assigned_developer_id: assignedDeveloperId,
        start_date: startDate,
        estimated_end_date: estimatedEndDate
    };

    try {
        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            throw new Error('No se pudo crear el proyecto');
        }

        // Close modal
        const modalEl = document.getElementById('createProjectModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modalInstance.hide();

        // Reset form
        document.getElementById('create-project-form').reset();

        // Show alert
        alert('Proyecto creado exitosamente.');

        // Refresh table
        fetchProjects();

    } catch (error) {
        console.error('Error al crear proyecto:', error);
        alert('Error al crear el proyecto. Revisa la consola para más detalles.');
    }
}

// Phase Management Logic
async function openManagePhases(projectId) {
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/phases`);
        if (!response.ok) {
            throw new Error('No se pudieron obtener las fases');
        }
        const phases = await response.json();

        const tbody = document.getElementById('phases-table-body');
        tbody.innerHTML = '';

        if (!phases || phases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay fases para este proyecto.</td></tr>';
        } else {
            phases.forEach(phase => {
                const tr = document.createElement('tr');
                
                const isDev = currentRole === 'Developer';
                const isPMO = currentRole === 'PMO';

                tr.innerHTML = `
                    <td class="fw-semibold">${phase.phase_name}</td>
                    <td><input type="date" class="form-control form-control-sm phase-start" value="${phase.start_date || ''}" ${isDev ? 'disabled' : ''}></td>
                    <td><input type="date" class="form-control form-control-sm phase-end" value="${phase.estimated_end_date || ''}" ${isDev ? 'disabled' : ''}></td>
                    <td>
                        <select class="form-select form-select-sm phase-status" ${isPMO ? 'disabled' : ''}>
                            <option value="Pending" ${phase.status === 'Pending' ? 'selected' : ''}>Pending</option>
                            <option value="In Progress" ${phase.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                            <option value="Completed" ${phase.status === 'Completed' ? 'selected' : ''}>Completed</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary btn-save-phase" onclick="updatePhase(${phase.id}, this.closest('tr'))">Guardar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        const modal = new bootstrap.Modal(document.getElementById('managePhasesModal'));
        modal.show();

    } catch (error) {
        console.error('Error al abrir administrar fases:', error);
        alert('Ocurrió un error al cargar las fases del proyecto.');
    }
}

async function updatePhase(phaseId, rowElement) {
    const isDev = currentRole === 'Developer';
    const isPMO = currentRole === 'PMO';
    const isAdmin = currentRole === 'Admin';
    
    const startDateVal = rowElement.querySelector('.phase-start').value || null;
    const endDateVal = rowElement.querySelector('.phase-end').value || null;
    const statusVal = rowElement.querySelector('.phase-status').value;

    const btnSave = rowElement.querySelector('.btn-save-phase');
    const originalBtnText = btnSave.innerText;
    btnSave.innerText = 'Guardando...';
    btnSave.disabled = true;

    try {
        // PMO or Admin can update dates
        if (isPMO || isAdmin) {
            const dateResponse = await fetch(`/api/v1/phases/${phaseId}/dates`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: startDateVal,
                    estimated_end_date: endDateVal
                })
            });
            if (!dateResponse.ok) {
                throw new Error('Error actualizando fechas de la fase');
            }
        }

        // Developer or Admin can update status
        if (isDev || isAdmin) {
            const statusResponse = await fetch(`/api/v1/phases/${phaseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: statusVal
                })
            });
            if (!statusResponse.ok) {
                throw new Error('Error actualizando estado de la fase');
            }
        }

        alert('Fase actualizada correctamente.');
        
        // Refresh the main table to update progress
        fetchProjects();

    } catch (error) {
        console.error('Error al actualizar fase:', error);
        alert('Error al actualizar la fase. Revisa la consola para más detalles.');
    } finally {
        btnSave.innerText = originalBtnText;
        btnSave.disabled = false;
    }
}
