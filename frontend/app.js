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
