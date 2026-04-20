// app.js - PMO RPA Dashboard MVP Final

// 1. Variables Globales y Autenticación
let authToken = localStorage.getItem('token');
let currentUserRole = localStorage.getItem('role');

function checkAuth() {
    if (!authToken) {
        // Si no hay token, forzamos el Modal de Login
        const loginModalEl = document.getElementById('loginModal');
        if (loginModalEl) {
            const loginModal = new bootstrap.Modal(loginModalEl);
            loginModal.show();
        }
    } else {
        // Si hay token, aplicamos UI y cargamos datos
        applyRoleUI();
        fetchProjects();
    }
}

// 2. Inicialización (DOM Loaded)
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Listeners de Botones Globales
    const btnExport = document.getElementById('btn-export');
    if (btnExport) btnExport.addEventListener('click', exportCSV);

    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) btnLogout.addEventListener('click', handleLogout);

    const loginForm = document.getElementById('login-form');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const createUserForm = document.getElementById('create-user-form');
    if (createUserForm) createUserForm.addEventListener('submit', createUser);

    const btnAdminUsers = document.getElementById('btn-admin-users');
    if (btnAdminUsers) btnAdminUsers.addEventListener('click', fetchUsers);

    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) createProjectForm.addEventListener('submit', handleCreateProject);
});

// -------------------------------------------------------------------------
// MÓDULO: Autenticación y UI
// -------------------------------------------------------------------------

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorContainer = document.getElementById('login-error-container');
    const btnSubmit = document.getElementById('btn-login-submit');

    errorContainer.innerHTML = '';
    btnSubmit.disabled = true;
    btnSubmit.innerText = 'Ingresando...';

    const params = new URLSearchParams();
    params.append('username', email); // Requerimiento OAuth2
    params.append('password', password);

    try {
        const response = await fetch('/api/v1/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
        });

        if (!response.ok) throw new Error('Credenciales incorrectas');

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('token', authToken);

        // Decodificar JWT para obtener el rol
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        currentUserRole = payload.role;
        localStorage.setItem('role', currentUserRole);

        // Ocultar Modal
        const modalEl = document.getElementById('loginModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();

        applyRoleUI();
        fetchProjects();
    } catch (error) {
        errorContainer.innerHTML = `<div class="alert alert-danger py-2 mb-3">${error.message}</div>`;
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerText = 'Ingresar';
    }
}

function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.reload();
}

function applyRoleUI() {
    const btnCreate = document.getElementById('btn-create-project');
    const btnExport = document.getElementById('btn-export');
    const btnAdminUsers = document.getElementById('btn-admin-users');
    const btnLogout = document.getElementById('btn-logout');

    if (btnLogout) btnLogout.style.display = 'inline-block';

    // UI para Admin
    if (currentUserRole === 'Admin') {
        if (btnAdminUsers) btnAdminUsers.style.display = 'inline-block';
    } else {
        if (btnAdminUsers) btnAdminUsers.style.display = 'none';
    }

    // UI para Admin y PMO
    if (currentUserRole === 'Admin' || currentUserRole === 'PMO') {
        if (btnCreate) btnCreate.style.display = 'inline-block';
        if (btnExport) btnExport.style.display = 'inline-block';
        populateDevelopersSelect();
    } else {
        if (btnCreate) btnCreate.style.display = 'none';
        if (btnExport) btnExport.style.display = 'none';
    }
}

async function populateDevelopersSelect() {
    try {
        const response = await fetch('/api/v1/users/developers', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!response.ok) throw new Error('Error al obtener los desarrolladores');
        
        const developers = await response.json();
        const select = document.getElementById('assigned-developer');
        
        if (select) {
            select.innerHTML = '';
            developers.forEach(dev => {
                const option = document.createElement('option');
                option.value = dev.id;
                option.textContent = `${dev.name} (${dev.email})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error(error);
    }
}

// -------------------------------------------------------------------------
// MÓDULO: Proyectos y Fases
// -------------------------------------------------------------------------

async function fetchProjects() {
    const errorContainer = document.getElementById('error-container');
    errorContainer.innerHTML = '';

    try {
        const response = await fetch('/api/v1/projects', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error(`Error: ${response.status} ${response.statusText}`);

        const projects = await response.json();
        renderProjects(projects);
    } catch (error) {
        console.error('Error al obtener proyectos:', error);
        errorContainer.innerHTML = `<div class="alert alert-danger"><strong>Error de conexión:</strong> No se pudo cargar los datos.</div>`;
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
        let healthClass = '', healthIcon = '⚪';

        if (project.health_status === 'Green') { healthClass = 'text-success'; healthIcon = '🟢'; }
        else if (project.health_status === 'Yellow') { healthClass = 'text-warning'; healthIcon = '🟡'; }
        else if (project.health_status === 'Red') { healthClass = 'text-danger'; healthIcon = '🔴'; }

        const progress = Math.round(project.progress_percentage);
        let progressColorClass = progress === 100 ? 'bg-success' : 'bg-primary';

        tr.innerHTML = `
            <td class="fw-semibold text-dark">${project.process_name}</td>
            <td class="text-secondary">${project.developer_name}</td>
            <td class="${healthClass} fw-bold">${healthIcon} ${project.health_status}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar ${progressColorClass}" style="width: ${progress}%">${progress}%</div>
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
        const response = await fetch(`/api/v1/projects/${projectId}/phases`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        const phases = await response.json();

        const ganttTarget = document.getElementById('gantt-target');
        ganttTarget.innerHTML = '';

        if (phases.length === 0) {
            ganttTarget.innerHTML = '<p class="text-muted p-3">No hay fases.</p>';
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

            new Gantt('#gantt-target', tasks, { view_mode: 'Month', language: 'es' });
        }

        document.getElementById('ganttModalLabel').innerText = `Gantt: ${projectName}`;
        new bootstrap.Modal(document.getElementById('ganttModal')).show();
    } catch (error) {
        console.error(error);
        alert('Error al cargar Gantt.');
    }
}

async function openManagePhases(projectId) {
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/phases`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        const phases = await response.json();

        const tbody = document.getElementById('phases-table-body');
        tbody.innerHTML = '';

        phases.forEach(p => {
            const tr = document.createElement('tr');
            const isDev = currentUserRole === 'Developer';
            const isPMO = currentUserRole === 'PMO';

            const dateDisabled = isDev ? 'disabled' : '';
            const statusDisabled = isPMO ? 'disabled' : '';

            tr.innerHTML = `
                <td class="fw-bold">${p.phase_name}</td>
                <td><input type="date" class="form-control form-control-sm date-start" value="${p.start_date}" ${dateDisabled}></td>
                <td><input type="date" class="form-control form-control-sm date-end" value="${p.estimated_end_date}" ${dateDisabled}></td>
                <td>
                    <select class="form-select form-select-sm status-select" ${statusDisabled}>
                        <option value="Pending" ${p.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="In Progress" ${p.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="Completed" ${p.status === 'Completed' ? 'selected' : ''}>Completed</option>
                    </select>
                </td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="updatePhase(${p.id}, this)">Guardar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        new bootstrap.Modal(document.getElementById('managePhasesModal')).show();
    } catch (error) {
        console.error(error);
    }
}

async function updatePhase(phaseId, btnElement) {
    const row = btnElement.closest('tr');
    const newStart = row.querySelector('.date-start').value;
    const newEnd = row.querySelector('.date-end').value;
    const newStatus = row.querySelector('.status-select').value;

    try {
        if (currentUserRole === 'Admin' || currentUserRole === 'PMO') {
            await fetch(`/api/v1/phases/${phaseId}/dates`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({ start_date: newStart, estimated_end_date: newEnd })
            });
        }
        if (currentUserRole === 'Admin' || currentUserRole === 'Developer') {
            await fetch(`/api/v1/phases/${phaseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({ status: newStatus })
            });
        }
        alert('Fase actualizada correctamente');
        fetchProjects();
    } catch (error) {
        console.error(error);
        alert('Error al actualizar fase');
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    const processName = document.getElementById('process-name').value;
    const assignedDev = parseInt(document.getElementById('assigned-developer').value, 10);
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('estimated-end-date').value;

    try {
        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ process_name: processName, assigned_developer_id: assignedDev, start_date: startDate, estimated_end_date: endDate })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al crear proyecto');

        bootstrap.Modal.getInstance(document.getElementById('createProjectModal')).hide();
        document.getElementById('create-project-form').reset();
        fetchProjects();
    } catch (error) {
        alert('Error al crear proyecto');
    }
}

// -------------------------------------------------------------------------
// MÓDULO: IAM / Admin Usuarios & Exportación
// -------------------------------------------------------------------------

async function fetchUsers() {
    if (currentUserRole !== 'Admin') return;
    try {
        const response = await fetch('/api/v1/users', { headers: { 'Authorization': 'Bearer ' + authToken } });
        if (response.status === 401) { handleLogout(); return; }

        const users = await response.json();
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';

        users.forEach(user => {
            if (user.is_active === 0) return; // Ocultar Soft Deleted
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="badge bg-secondary">${user.role}</span></td>
                <td><button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">Dar de baja</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

async function createUser(e) {
    e.preventDefault();
    const name = document.getElementById('new-user-name').value;
    const email = document.getElementById('new-user-email').value;
    const password = document.getElementById('new-user-password').value;
    const role = document.getElementById('new-user-role').value;

    try {
        const response = await fetch('/api/v1/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ name, email, password, role }) // Ajustado al schema Pydantic exacto
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error de Servidor');

        document.getElementById('create-user-form').reset();
        fetchUsers();
    } catch (error) { alert('Error al crear usuario. Verifica que el email no esté repetido.'); }
}

async function deleteUser(id) {
    if (!confirm('¿Seguro que deseas dar de baja a este usuario?')) return;
    try {
        const response = await fetch(`/api/v1/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        fetchUsers();
    } catch (error) { alert('Error al procesar la baja'); }
}

async function exportCSV() {
    try {
        const response = await fetch('/api/v1/reports/export', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'pmo_rpa_report.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (err) { console.error(err); }
}