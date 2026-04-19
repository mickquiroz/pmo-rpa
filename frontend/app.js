// app.js

document.addEventListener('DOMContentLoaded', () => {
    fetchProjects();
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
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No hay proyectos registrados.</td></tr>';
        return;
    }

    projects.forEach(project => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.onclick = () => showProjectGantt(project.id, project.process_name);
        
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

