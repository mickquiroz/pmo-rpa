// app.js - PMO RPA Dashboard MVP Final — Fase 21: UI Dinámica por Permisos JWT

// 1. Variables Globales y Autenticación
let authToken = localStorage.getItem('token');
let currentUserRole = localStorage.getItem('role');
let currentUserPermissions = JSON.parse(localStorage.getItem('permissions') || '[]');
let currentManageProjectId = null;
let currentGanttProjectId = null; // ID del proyecto activo en el Gantt
let editingRoleId = null; // Estado para edición de roles
let allPermissions = [];  // Caché de permisos para mapeo de nombres

function checkAuth() {
    if (!authToken) {
        // Si no hay token, forzamos el Modal de Login
        const loginModalEl = document.getElementById('loginModal');
        if (loginModalEl) {
            const loginModal = new bootstrap.Modal(loginModalEl);
            loginModal.show();
        }
    } else {
        // Restaurar permisos desde localStorage en variable global
        currentUserPermissions = JSON.parse(localStorage.getItem('permissions') || '[]');
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
    if (btnAdminUsers) btnAdminUsers.addEventListener('click', () => {
        fetchUsers();
        populateRolesSelect();
    });

    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) createProjectForm.addEventListener('submit', handleCreateProject);

    const createPhaseForm = document.getElementById('create-phase-form');
    if (createPhaseForm) createPhaseForm.addEventListener('submit', handleCreatePhase);

    const btnAdminRoles = document.getElementById('btn-admin-roles');
    if (btnAdminRoles) btnAdminRoles.addEventListener('click', () => {
        resetRoleForm();
        fetchRoles();
        fetchPermissions();
    });

    const btnAdminProjectTypes = document.getElementById('btn-admin-project-types');
    if (btnAdminProjectTypes) btnAdminProjectTypes.addEventListener('click', fetchProjectTypes);

    const btnBacklog = document.getElementById('btn-backlog');
    if (btnBacklog) btnBacklog.addEventListener('click', fetchBacklog);

    const createRoleForm = document.getElementById('create-role-form');
    if (createRoleForm) createRoleForm.addEventListener('submit', createRole);

    const createProjectTypeForm = document.getElementById('create-project-type-form');
    if (createProjectTypeForm) createProjectTypeForm.addEventListener('submit', createProjectType);

    const createCommentForm = document.getElementById('create-comment-form');
    if (createCommentForm) createCommentForm.addEventListener('submit', createPhaseComment);

    const btnProfile = document.getElementById('btn-profile');
    if (btnProfile) btnProfile.addEventListener('click', fetchMyProfile);

    const profileForm = document.getElementById('profile-form');
    if (profileForm) profileForm.addEventListener('submit', handleUpdateProfile);

    // Chatbot Listeners (Fase 38)
    const chatToggle = document.getElementById('chatbot-toggle');
    if (chatToggle) chatToggle.addEventListener('click', toggleChat);

    const chatClose = document.getElementById('chatbot-close');
    if (chatClose) chatClose.addEventListener('click', toggleChat);

    const chatForm = document.getElementById('chatbot-form');
    if (chatForm) chatForm.addEventListener('submit', handleChatSubmit);
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

        // Decodificar JWT para obtener el rol Y los permisos granulares
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        currentUserRole = payload.role;
        currentUserPermissions = Array.isArray(payload.permissions) ? payload.permissions : [];
        localStorage.setItem('role', currentUserRole);
        localStorage.setItem('permissions', JSON.stringify(currentUserPermissions));

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
    localStorage.removeItem('permissions');
    window.location.reload();
}

function applyRoleUI() {
    const btnCreate = document.getElementById('btn-create-project');
    const btnExport = document.getElementById('btn-export');
    const btnAdminUsers = document.getElementById('btn-admin-users');
    const btnAdminRoles = document.getElementById('btn-admin-roles');
    const btnAdminProjectTypes = document.getElementById('btn-admin-project-types');
    const btnBacklog = document.getElementById('btn-backlog');
    const btnLogout = document.getElementById('btn-logout');
    const btnProfile = document.getElementById('btn-profile');

    if (btnLogout) btnLogout.style.display = 'inline-block';
    if (btnProfile) btnProfile.style.display = 'inline-block';

    // ── Panel de Super-Admin (Usuarios, Roles, Tipos): sólo usuarios con rol 'Admin'.
    // Respaldo explícito por rol para el panel administrativo superior.
    const isAdmin = (currentUserRole === 'Admin');
    if (btnAdminUsers) btnAdminUsers.style.display = isAdmin ? 'inline-block' : 'none';
    if (btnAdminRoles) btnAdminRoles.style.display = isAdmin ? 'inline-block' : 'none';
    if (btnAdminProjectTypes) btnAdminProjectTypes.style.display = isAdmin ? 'inline-block' : 'none';

    // ── Acciones Operativas: COMPLETAMENTE dictadas por el array de permisos del JWT ──

    // Botón "Crear Proyecto"
    if (btnCreate) {
        btnCreate.style.display = currentUserPermissions.includes('write:projects') ? 'inline-block' : 'none';
    }

    // Botón "Exportar CSV"
    if (btnExport) {
        btnExport.style.display = currentUserPermissions.includes('write:projects') ? 'inline-block' : 'none';
    }

    // Botón "Backlog"
    if (btnBacklog) {
        btnBacklog.style.display = currentUserPermissions.includes('write:projects') ? 'inline-block' : 'none';
    }

    // Poblar selects del formulario de creación de proyecto sólo si el usuario puede crearlos
    if (currentUserPermissions.includes('write:projects')) {
        populateDevelopersSelect();
        populateProjectTypesSelect();
        populateCommercialSelect();
    }

    // ── Widget de Chat (Fase 38): Visible si está logueado
    const chatWidget = document.getElementById('chatbot-widget');
    if (chatWidget) {
        chatWidget.style.display = authToken ? 'block' : 'none';
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

async function populateProjectTypesSelect() {
    try {
        const response = await fetch('/api/v1/project-types', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!response.ok) throw new Error('Error al obtener los tipos de proyecto');

        const types = await response.json();
        const select = document.getElementById('project-type');

        if (select) {
            select.innerHTML = '<option value="">Seleccione...</option>';
            types.forEach(pt => {
                const option = document.createElement('option');
                option.value = pt.id;
                option.textContent = pt.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error(error);
    }
}

async function populateCommercialSelect() {
    try {
        const response = await fetch('/api/v1/users/commercials', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!response.ok) throw new Error('Error al obtener comerciales');

        const users = await response.json();
        const select = document.getElementById('commercial-id');

        if (select) {
            select.innerHTML = '<option value="">Seleccione un comercial...</option>';
            // Filtrado robusto como solicita la Fase 25: exacto 'Pre-sales' o que contenga 'sales' (case-insensitive)
            users.filter(u => (u.role_name === 'Pre-sales' || u.role_name.toLowerCase().includes('sales')) && u.is_active).forEach(u => {
                const option = document.createElement('option');
                option.value = u.id;
                option.textContent = `${u.name} (${u.email})`;
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

        // Botón de eliminar proyecto dictado por permiso 'delete:projects'
        const deleteBtn = currentUserPermissions.includes('delete:projects')
            ? `<button class="btn btn-sm btn-danger ms-1" onclick="deleteProject(${project.id})">Eliminar</button>`
            : '';

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
                ${currentUserPermissions.includes('read:projects')
                ? `<button class="btn btn-sm btn-outline-primary me-1" onclick="showProjectGantt(${project.id}, '${project.process_name}')">Ver Gantt</button>`
                : ''}
                ${currentUserPermissions.includes('edit:phases') || currentUserPermissions.includes('write:projects')
                ? `<button class="btn btn-sm btn-outline-secondary" onclick="openManagePhases(${project.id})">Editar Fases</button>`
                : ''}
                ${deleteBtn}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Module-level Gantt state
let currentGanttInstance = null;
let currentGanttTasks = [];
let currentGanttViewMode = 'Week';

async function showProjectGantt(projectId, projectName) {
    currentGanttProjectId = projectId;
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/phases`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        const phases = await response.json();

        const ganttTarget = document.getElementById('gantt-target');
        ganttTarget.innerHTML = '';
        currentGanttInstance = null;
        currentGanttTasks = [];

        if (phases.length === 0) {
            ganttTarget.innerHTML = '<p class="text-muted p-3">No hay fases.</p>';
        } else {
            currentGanttTasks = phases.map(p => {
                let progress = 0;
                let custom_class = 'gantt-pending';

                if (p.status === 'Completed') { progress = 100; custom_class = 'gantt-completed'; }
                else if (p.status === 'In Progress') { progress = 50; custom_class = 'gantt-progress'; }

                return {
                    id: `Phase_${p.id}`,
                    name: p.phase_name,
                    start: p.start_date,
                    end: p.estimated_end_date,
                    progress: progress,
                    custom_class: custom_class,
                    dependencies: ''
                };
            });

            currentGanttInstance = new Gantt('#gantt-target', currentGanttTasks, {
                view_mode: currentGanttViewMode,
                language: 'es',
                on_click: function (task) {
                    // task.id tiene formato "Phase_X" — extraemos el entero X
                    const phaseId = parseInt(task.id.split('_')[1], 10);
                    selectPhaseForComment(phaseId, task.name);
                }
            });
        }

        // Cargar y renderizar la comunicación integrada del proyecto
        await fetchProjectComments(projectId);

        // Resetear el estado de selección del formulario de comentarios
        document.getElementById('create-comment-container').style.display = 'none';
        document.getElementById('selected-phase-badge').style.display = 'none';
        document.getElementById('selected-phase-badge').innerText = '';

        document.getElementById('ganttModalLabel').innerText = `Gantt: ${projectName}`;

        // Sincronizar botones de escala con el estado actual
        document.querySelectorAll('.gantt-view-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.getElementById(`gantt-view-${currentGanttViewMode.toLowerCase()}`);
        if (activeBtn) activeBtn.classList.add('active');

        new bootstrap.Modal(document.getElementById('ganttModal')).show();
    } catch (error) {
        console.error(error);
        alert('Error al cargar Gantt.');
    }
}

function setGanttViewMode(mode) {
    currentGanttViewMode = mode;

    // Actualizar estado visual de los botones
    document.querySelectorAll('.gantt-view-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`gantt-view-${mode.toLowerCase()}`);
    if (activeBtn) activeBtn.classList.add('active');

    // Reconstruir el Gantt con el nuevo view_mode si hay una instancia activa
    if (currentGanttTasks.length > 0) {
        const ganttTarget = document.getElementById('gantt-target');
        ganttTarget.innerHTML = '';
        currentGanttInstance = new Gantt('#gantt-target', currentGanttTasks, {
            view_mode: mode,
            language: 'es',
            on_click: function (task) {
                const phaseId = parseInt(task.id.split('_')[1], 10);
                selectPhaseForComment(phaseId, task.name);
            }
        });
    }
}

/**
 * Activa el formulario de comentarios para una fase específica seleccionada en el Gantt.
 */
function selectPhaseForComment(phaseId, phaseName) {
    const container = document.getElementById('create-comment-container');
    const badge = document.getElementById('selected-phase-badge');
    const inputId = document.getElementById('comment-phase-id');
    const textarea = document.getElementById('new-comment-text');

    if (container && badge && inputId) {
        inputId.value = phaseId;
        badge.innerText = `Fase: ${phaseName}`;
        badge.style.display = 'inline-block';
        container.style.display = 'block';

        // Scroll suave hasta el formulario si es necesario
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        if (textarea) textarea.focus();

        // Filtrar comentarios por esta fase
        fetchProjectComments(currentGanttProjectId, phaseId);
    }
}


async function openManagePhases(projectId) {
    currentManageProjectId = projectId;
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/phases`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        const phases = await response.json();

        // Panel de creación de fases: sólo si el usuario puede escribir proyectos/fases
        const canWriteProjects = currentUserPermissions.includes('write:projects');
        const canDeleteProjects = currentUserPermissions.includes('delete:projects');
        const canEditPhases = currentUserPermissions.includes('edit:phases');

        const createPhaseContainer = document.getElementById('create-phase-container');
        if (createPhaseContainer) {
            createPhaseContainer.style.display = canWriteProjects ? 'block' : 'none';
        }

        // Mostrar/Ocultar botón "Guardar Todo"
        const btnSaveAll = document.getElementById('btn-save-all-phases');
        if (btnSaveAll) {
            btnSaveAll.style.display = (canEditPhases || canWriteProjects) ? 'inline-block' : 'none';
        }

        const tbody = document.getElementById('phases-table-body');
        tbody.innerHTML = '';

        phases.forEach(p => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-phase-id', p.id);

            // Las fechas y detalles estructurales solo editables si puede escribir proyectos
            const dateDisabled = canWriteProjects ? '' : 'disabled';
            // El estado sólo editable si tiene permiso 'edit:phases'
            const statusDisabled = canEditPhases ? '' : 'disabled';
            const detailsDisabled = canWriteProjects ? '' : 'disabled';

            tr.innerHTML = `
                <td class="drag-handle text-muted" style="cursor: grab; font-size: 1.2rem;">☰</td>
                <td><input type="text" class="form-control form-control-sm phase-name" value="${p.phase_name}" ${detailsDisabled}></td>
                <td><input type="number" class="form-control form-control-sm phase-weight" value="${p.weight_percentage || 0}" min="0" max="100" ${detailsDisabled}></td>
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
                    ${canDeleteProjects ? `<button class="btn btn-sm btn-danger" onclick="deletePhase(${p.id})">Eliminar</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Inicializar SortableJS para reordenar fases
        if (canWriteProjects || canEditPhases) {
            new Sortable(tbody, {
                handle: '.drag-handle',
                animation: 150,
                ghostClass: 'bg-light'
            });
        }

        const modalEl = document.getElementById('managePhasesModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modalInstance.show();
    } catch (error) {
        console.error(error);
    }
}

async function saveAllPhases() {
    const btnSaveAll = document.getElementById('btn-save-all-phases');
    const rows = document.querySelectorAll('#phases-table-body tr');

    if (rows.length === 0) return;

    btnSaveAll.disabled = true;
    const originalText = btnSaveAll.innerText;
    btnSaveAll.innerText = 'Guardando...';

    const promises = [];

    rows.forEach((row, index) => {
        const phaseId = row.getAttribute('data-phase-id');
        if (!phaseId) return;

        const newStart = row.querySelector('.date-start').value;
        const newEnd = row.querySelector('.date-end').value;
        const newStatus = row.querySelector('.status-select').value;
        const newName = row.querySelector('.phase-name').value;
        const newWeight = parseInt(row.querySelector('.phase-weight').value, 10);
        const displayOrder = index; // Nueva posición basada en el DOM

        // Actualizar fechas y detalles si el usuario tiene permiso 'write:projects'
        if (currentUserPermissions.includes('write:projects')) {
            promises.push(fetch(`/api/v1/phases/${phaseId}/dates`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({ start_date: newStart, estimated_end_date: newEnd })
            }));
            promises.push(fetch(`/api/v1/phases/${phaseId}/details`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({
                    phase_name: newName,
                    weight_percentage: newWeight,
                    display_order: displayOrder
                })
            }));
        }

        // Actualizar estado si el usuario tiene permiso 'edit:phases'
        if (currentUserPermissions.includes('edit:phases')) {
            promises.push(fetch(`/api/v1/phases/${phaseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                body: JSON.stringify({ status: newStatus })
            }));
        }
    });

    try {
        const results = await Promise.all(promises);
        const allOk = results.every(res => res.ok);

        if (allOk) {
            alert('Todas las fases han sido actualizadas correctamente.');
            fetchProjects();
            // Refrescar el contenido del modal para asegurar que los datos estén sincronizados
            openManagePhases(currentManageProjectId);
        } else {
            throw new Error('Algunas actualizaciones fallaron. Revisa la consola para más detalles.');
        }
    } catch (error) {
        console.error('Error en saveAllPhases:', error);
        alert('Error al guardar cambios masivos: ' + error.message);
    } finally {
        btnSaveAll.disabled = false;
        btnSaveAll.innerText = originalText;
    }
}

async function deletePhase(phaseId) {
    if (!confirm('¿Seguro que deseas eliminar esta fase?')) return;
    try {
        const response = await fetch(`/api/v1/phases/${phaseId}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al eliminar fase');

        openManagePhases(currentManageProjectId);
        fetchProjects();
    } catch (error) {
        alert(error.message);
    }
}

async function handleCreatePhase(e) {
    e.preventDefault();
    if (!currentManageProjectId) return;

    const phaseName = document.getElementById('new-phase-name').value;
    const weight = parseInt(document.getElementById('new-phase-weight').value, 10);
    const startDate = document.getElementById('new-phase-start').value;
    const endDate = document.getElementById('new-phase-end').value;

    try {
        const response = await fetch('/api/v1/phases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({
                project_id: currentManageProjectId,
                phase_name: phaseName,
                weight_percentage: weight,
                start_date: startDate,
                estimated_end_date: endDate
            })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al crear fase');

        document.getElementById('create-phase-form').reset();
        openManagePhases(currentManageProjectId);
        fetchProjects();
    } catch (error) {
        alert(error.message);
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    const processName = document.getElementById('process-name').value;
    const projectTypeId = parseInt(document.getElementById('project-type').value, 10);
    const assignedDev = parseInt(document.getElementById('assigned-developer').value, 10);
    const commercialIdVal = document.getElementById('commercial-id').value;
    const commercialId = commercialIdVal ? parseInt(commercialIdVal, 10) : null;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('estimated-end-date').value;

    try {
        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({
                process_name: processName,
                project_type_id: projectTypeId,
                assigned_developer_id: assignedDev,
                commercial_id: commercialId,
                start_date: startDate,
                estimated_end_date: endDate
            })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Error al crear proyecto');
        }

        bootstrap.Modal.getInstance(document.getElementById('createProjectModal')).hide();
        document.getElementById('create-project-form').reset();
        fetchProjects();
    } catch (error) {
        alert(error.message);
    }
}

// -------------------------------------------------------------------------
// MÓDULO: Backlog y Auditoría de Fases (Comentarios)
// -------------------------------------------------------------------------

async function fetchBacklog() {
    try {
        const response = await fetch('/api/v1/projects/backlog', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al obtener backlog');

        const projects = await response.json();
        const tbody = document.getElementById('backlog-table-body');
        tbody.innerHTML = '';

        if (projects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay proyectos eliminados.</td></tr>';
        } else {
            projects.forEach(project => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="text-decoration-line-through">${project.process_name}</td>
                    <td>${project.developer_name}</td>
                    <td>${project.health_status}</td>
                    <td>${project.start_date}</td>
                    <td>${project.estimated_end_date}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Mostrar el modal evitando instanciaciones múltiples
        const backlogEl = document.getElementById('backlogModal');
        const backlogModal = bootstrap.Modal.getInstance(backlogEl) || new bootstrap.Modal(backlogEl);
        backlogModal.show();
    } catch (error) {
        console.error(error);
    }
}

async function openPhaseComments(phaseId) {
    // Como ahora los comentarios están integrados en el Gantt, 
    // esta función podría redirigir al Gantt y seleccionar la fase.
    // Sin embargo, por simplicidad en esta fase, la hemos eliminado de los botones directos.
    console.log("openPhaseComments llamado para ID:", phaseId);
}

/**
 * Genera el HTML para el avatar del usuario (Imagen o Inicial con color).
 */
function getAvatar(user) {
    if (user.profile_picture) {
        return `<div class="comment-avatar"><img src="${user.profile_picture}" alt="${user.user_name}"></div>`;
    }
    const colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796', '#5a5c69', '#6610f2', '#6f42c1', '#e83e8c'];
    const charCode = user.user_name ? user.user_name.charCodeAt(0) : 65;
    const color = colors[charCode % colors.length];
    const initial = user.user_name ? user.user_name.charAt(0).toUpperCase() : '?';
    return `<div class="comment-avatar" style="background-color: ${color}">${initial}</div>`;
}

async function fetchProjectComments(projectId, phaseId = null) {
    const listGroup = document.getElementById('comments-list');
    const btnShowAll = document.getElementById('btn-show-all-comments');

    // Si hay phaseId, mostramos el botón de reset
    if (btnShowAll) btnShowAll.style.display = phaseId ? 'inline-block' : 'none';

    try {
        let url = `/api/v1/projects/${projectId}/comments`;
        if (phaseId) url += `?phase_id=${phaseId}`;

        const response = await fetch(url, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        const comments = await response.json();

        listGroup.innerHTML = '';

        if (comments.length === 0) {
            listGroup.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted mb-0">${phaseId ? 'No hay comentarios en esta fase.' : 'No hay comentarios en este proyecto.'}</p>
                    <small class="text-secondary">Haz clic en una fase del diagrama para iniciar una conversación.</small>
                </div>`;
            return;
        }

        comments.forEach(comment => {
            const div = document.createElement('div');
            div.className = 'comment-item';

            const dateStr = new Date(comment.created_at).toLocaleString('es-ES', {
                day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            const avatarHtml = getAvatar(comment);

            div.innerHTML = `
                ${avatarHtml}
                <div class="comment-body">
                    <div class="comment-header">
                        <div class="comment-user-info">
                            <span class="comment-user-name">${comment.user_name}</span>
                            <span class="comment-user-role">${comment.role_name || 'Usuario'}</span>
                        </div>
                        <span class="comment-date">${dateStr}</span>
                    </div>
                    <p class="comment-text">${comment.comment_text}</p>
                    ${!phaseId ? `<span class="comment-phase-tag">Fase: ${comment.phase_name}</span>` : ''}
                </div>
            `;
            listGroup.appendChild(div);
        });
    } catch (error) {
        console.error(error);
        listGroup.innerHTML = '<p class="text-danger p-3">Error al cargar la comunicación.</p>';
    }
}

function resetCommentsFilter() {
    if (!currentGanttProjectId) return;

    const badge = document.getElementById('selected-phase-badge');
    const container = document.getElementById('create-comment-container');
    const inputId = document.getElementById('comment-phase-id');
    const btnShowAll = document.getElementById('btn-show-all-comments');

    if (badge) badge.style.display = 'none';
    if (container) container.style.display = 'none';
    if (inputId) inputId.value = '';
    if (btnShowAll) btnShowAll.style.display = 'none';

    fetchProjectComments(currentGanttProjectId);
}

async function createPhaseComment(e) {
    e.preventDefault();
    const phaseId = document.getElementById('comment-phase-id').value;
    const commentTextInput = document.getElementById('new-comment-text');
    const commentText = commentTextInput.value;

    if (!phaseId) {
        alert("Por favor, selecciona una fase en el diagrama de Gantt primero.");
        return;
    }

    try {
        const response = await fetch(`/api/v1/phases/${phaseId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ comment_text: commentText })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al añadir comentario');

        commentTextInput.value = '';
        // Refrescar la vista consolidada de comentarios del proyecto (manteniendo el filtro si existe)
        const currentFilterPhaseId = document.getElementById('comment-phase-id').value;
        await fetchProjectComments(currentGanttProjectId, currentFilterPhaseId);

        // Mantener el formulario visible para permitir más comentarios seguidos
    } catch (error) {
        alert('No se pudo añadir el comentario: ' + error.message);
    }
}

// -------------------------------------------------------------------------
// MÓDULO: IAM / Admin Usuarios & Exportación
// -------------------------------------------------------------------------

async function fetchUsers() {
    if (currentUserRole !== 'Admin') return; // Panel IAM sólo Admin (respaldo por rol)
    try {
        const response = await fetch('/api/v1/users', { headers: { 'Authorization': 'Bearer ' + authToken } });
        if (response.status === 401) { handleLogout(); return; }

        const users = await response.json();
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';

        users.forEach(user => {
            const isActive = user.is_active === 1;
            const tr = document.createElement('tr');
            const roleBadge = `<span class="badge bg-secondary">${user.role_name}</span>`;
            const statusBadge = isActive ? '' : ' <span class="badge bg-danger ms-1">Inactivo</span>';
            const actionBtn = isActive
                ? `<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">Dar de baja</button>`
                : `<button class="btn btn-sm btn-outline-success" onclick="reactivateUser(${user.id})">Reactivar</button>`;
            tr.innerHTML = `
                <td>${user.id}</td>
                <td>${user.name}${statusBadge}</td>
                <td>${user.email}</td>
                <td>${roleBadge}</td>
                <td>${actionBtn}</td>
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
    const roleId = parseInt(document.getElementById('new-user-role').value, 10);

    if (!roleId) {
        alert('Por favor selecciona un rol válido.');
        return;
    }

    try {
        const response = await fetch('/api/v1/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ name, email, password, role_id: roleId })
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

async function reactivateUser(id) {
    if (!confirm('¿Reactivar a este usuario?')) return;
    try {
        const response = await fetch(`/api/v1/users/${id}/reactivate`, {
            method: 'PATCH',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al reactivar usuario');
        fetchUsers();
    } catch (error) { alert('Error al reactivar el usuario'); }
}

async function populateRolesSelect() {
    try {
        const response = await fetch('/api/v1/roles', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!response.ok) throw new Error('Error al obtener roles');

        const roles = await response.json();
        const select = document.getElementById('new-user-role');
        if (select) {
            select.innerHTML = '<option value="">Selecciona un rol...</option>';
            roles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.id;           // role_id (int) para el backend
                option.textContent = role.name;
                select.appendChild(option);
            });
        }
    } catch (error) { console.error('Error al poblar roles:', error); }
}

async function deleteProject(projectId) {
    if (!confirm('¿Eliminar este proyecto del tablero? Pasará al Backlog.')) return;
    try {
        const response = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al eliminar proyecto');
        fetchProjects();
    } catch (error) { alert('No se pudo eliminar el proyecto.'); }
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

// -------------------------------------------------------------------------
// MÓDULO: Super Admin (Roles y Tipos de Proyecto)
// -------------------------------------------------------------------------

async function fetchRoles() {
    if (currentUserRole !== 'Admin') return; // Panel Super-Admin sólo Admin (respaldo por rol)
    try {
        const response = await fetch('/api/v1/roles', { headers: { 'Authorization': 'Bearer ' + authToken } });
        if (response.status === 401) { handleLogout(); return; }

        const roles = await response.json();
        const tbody = document.getElementById('roles-table-body');
        tbody.innerHTML = '';

        roles.forEach(role => {
            const tr = document.createElement('tr');

            // Mapear IDs de permisos a nombres legibles usando la caché global
            const permBadges = role.permission_ids && role.permission_ids.length
                ? role.permission_ids.map(pid => {
                    const perm = allPermissions.find(p => p.id === pid);
                    return `<span class="badge bg-info text-dark me-1" title="ID: ${pid}">${perm ? perm.action : pid}</span>`;
                }).join('')
                : '<small class="text-muted">Sin permisos</small>';

            // Botones de acción (Editar / Eliminar)
            const actions = `
                <div class="d-flex gap-1">
                    <button class="btn btn-xs btn-outline-primary" onclick='editRole(${JSON.stringify(role)})'>
                        Editar
                    </button>
                    <button class="btn btn-xs btn-outline-danger" onclick="deleteRole(${role.id})">
                        Borrar
                    </button>
                </div>
            `;

            tr.innerHTML = `
                <td>${role.id}</td>
                <td>${role.name}</td>
                <td>${role.description || ''}</td>
                <td>${permBadges}</td>
                <td>${actions}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

async function createRole(e) {
    e.preventDefault();
    const name = document.getElementById('new-role-name').value;
    const description = document.getElementById('new-role-desc').value;
    const errorContainer = document.getElementById('roles-error-container');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    errorContainer.innerHTML = '';

    // Collect checked permission IDs
    const checkedBoxes = document.querySelectorAll('#permissions-checkboxes input[type="checkbox"]:checked');
    const permission_ids = Array.from(checkedBoxes).map(cb => parseInt(cb.value, 10));

    const method = editingRoleId ? 'PUT' : 'POST';
    const url = editingRoleId ? `/api/v1/roles/${editingRoleId}` : '/api/v1/roles';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ name, description, permission_ids })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Error al procesar rol');
        }

        resetRoleForm();
        fetchRoles();
    } catch (error) {
        errorContainer.innerHTML = `<div class="alert alert-danger py-2 mb-3">${error.message}</div>`;
    }
}

function editRole(role) {
    const formTitle = document.querySelector('#adminRolesModal .col-md-4 h6');
    if (formTitle) formTitle.innerText = 'Editar Rol';

    // Scroll al formulario (opcional)
    document.getElementById('create-role-form').scrollIntoView({ behavior: 'smooth' });

    // Llenar campos
    document.getElementById('new-role-name').value = role.name;
    document.getElementById('new-role-desc').value = role.description || '';

    // Limpiar checkboxes
    document.querySelectorAll('#permissions-checkboxes input[type="checkbox"]').forEach(cb => cb.checked = false);

    // Marcar permisos del rol
    if (role.permission_ids) {
        role.permission_ids.forEach(pid => {
            const cb = document.getElementById(`perm-check-${pid}`);
            if (cb) cb.checked = true;
        });
    }

    // Cambiar estado a edición
    submitBtn.classList.add('btn-warning');

    // Mostrar botón cancelar si no existe
    let cancelBtn = document.getElementById('btn-cancel-role-edit');
    if (cancelBtn) cancelBtn.style.display = 'inline-block';
}

function resetRoleForm() {
    editingRoleId = null;
    const form = document.getElementById('create-role-form');
    if (form) form.reset();

    const formTitle = document.querySelector('#adminRolesModal .col-md-4 h6');
    if (formTitle) formTitle.innerText = 'Crear Rol';

    const submitBtn = document.querySelector('#create-role-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerText = 'Crear Rol';
        submitBtn.classList.remove('btn-warning');
        submitBtn.classList.add('btn-primary');
    }

    // Limpiar checkboxes
    document.querySelectorAll('#permissions-checkboxes input[type="checkbox"]').forEach(cb => cb.checked = false);

    // Ocultar botón cancelar
    const cancelBtn = document.getElementById('btn-cancel-role-edit');
    if (cancelBtn) cancelBtn.style.display = 'none';

    const errorContainer = document.getElementById('roles-error-container');
    if (errorContainer) errorContainer.innerHTML = '';
}

async function deleteRole(id) {
    if (!confirm('¿Seguro que deseas eliminar este rol? Esta acción no se puede deshacer.')) return;

    const errorContainer = document.getElementById('roles-error-container');
    errorContainer.innerHTML = '';

    try {
        const response = await fetch(`/api/v1/roles/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });

        if (response.status === 401) { handleLogout(); return; }

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Error al eliminar rol');
        }

        fetchRoles();
    } catch (error) {
        errorContainer.innerHTML = `<div class="alert alert-danger py-2 mb-3">${error.message}</div>`;
    }
}

// -------------------------------------------------------------------------
// MÓDULO: fetchPermissions — genera checkboxes dinámicos de permisos
// -------------------------------------------------------------------------

async function fetchPermissions() {
    if (currentUserRole !== 'Admin') return; // Panel Super-Admin sólo Admin (respaldo por rol)
    const container = document.getElementById('permissions-checkboxes');
    if (!container) return;

    try {
        const response = await fetch('/api/v1/permissions', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('Error al obtener permisos');

        const permissions = await response.json();
        allPermissions = permissions; // Guardar en caché global
        container.innerHTML = '';

        if (permissions.length === 0) {
            container.innerHTML = '<small class="text-muted">No hay permisos definidos.</small>';
            return;
        }

        permissions.forEach(perm => {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-check';
            wrapper.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${perm.id}" id="perm-check-${perm.id}">
                <label class="form-check-label" for="perm-check-${perm.id}">
                    <code class="text-primary">${perm.action}</code>
                </label>
            `;
            container.appendChild(wrapper);
        });
    } catch (error) {
        console.error('Error al cargar permisos:', error);
        if (container) container.innerHTML = '<small class="text-danger">No se pudieron cargar los permisos.</small>';
    }
}

async function fetchProjectTypes() {
    if (currentUserRole !== 'Admin') return; // Panel Super-Admin sólo Admin (respaldo por rol)
    try {
        const response = await fetch('/api/v1/project-types', { headers: { 'Authorization': 'Bearer ' + authToken } });
        if (response.status === 401) { handleLogout(); return; }

        const projectTypes = await response.json();
        const tbody = document.getElementById('project-types-table-body');
        tbody.innerHTML = '';

        projectTypes.forEach(pt => {
            const tr = document.createElement('tr');
            const statusBadge = pt.is_active ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-danger">Inactivo</span>';
            tr.innerHTML = `
                <td>${pt.id}</td>
                <td>${pt.name}</td>
                <td>${pt.description || ''}</td>
                <td>${statusBadge}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) { console.error(error); }
}

async function createProjectType(e) {
    e.preventDefault();
    const name = document.getElementById('new-pt-name').value;
    const description = document.getElementById('new-pt-desc').value;
    const errorContainer = document.getElementById('project-types-error-container');
    errorContainer.innerHTML = '';

    try {
        const response = await fetch('/api/v1/project-types', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
            body: JSON.stringify({ name, description })
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Error al crear tipo de proyecto');
        }

        document.getElementById('create-project-type-form').reset();
        fetchProjectTypes();
    } catch (error) {
        errorContainer.innerHTML = `<div class="alert alert-danger py-2 mb-3">${error.message}</div>`;
    }
}
// -------------------------------------------------------------------------
// MÓDULO: Mi Perfil (Self-Service)
// -------------------------------------------------------------------------

async function fetchMyProfile() {
    const errorContainer = document.getElementById('profile-error-container');
    if (errorContainer) errorContainer.innerHTML = '';

    try {
        const response = await fetch('/api/v1/users/me', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) throw new Error('No se pudo cargar la información del perfil.');

        const user = await response.json();

        // Poblar formulario
        document.getElementById('profile-name').value = user.name;
        document.getElementById('profile-photo').value = user.profile_picture || '';
        document.getElementById('profile-email-display').innerText = user.email;
        document.getElementById('profile-role-display').innerText = user.role_name;
        document.getElementById('profile-password').value = ''; // Siempre vacío por seguridad

        renderProfilePreview(user);
    } catch (error) {
        console.error(error);
        if (errorContainer) errorContainer.innerHTML = '<div class="alert alert-danger py-2">' + error.message + '</div>';
    }
}

function renderProfilePreview(user) {
    const preview = document.getElementById('profile-avatar-preview');
    if (!preview) return;

    if (user.profile_picture) {
        preview.innerHTML = '<img src="' + user.profile_picture + '" alt="' + user.name + '" style="width: 100%; height: 100%; object-fit: cover;">';
    } else {
        const initial = user.name ? user.name.charAt(0).toUpperCase() : '?';
        preview.innerHTML = initial;
    }
}

async function handleUpdateProfile(e) {
    e.preventDefault();
    const btnSave = document.getElementById('btn-save-profile');
    const errorContainer = document.getElementById('profile-error-container');

    const name = document.getElementById('profile-name').value;
    const photo = document.getElementById('profile-photo').value;
    const password = document.getElementById('profile-password').value;

    const payload = {
        name: name,
        profile_picture: photo || null
    };

    if (password && password.trim().length >= 6) {
        payload.password = password;
    } else if (password && password.trim().length > 0) {
        errorContainer.innerHTML = '<div class="alert alert-warning py-2">La contraseña debe tener al menos 6 caracteres.</div>';
        return;
    }

    btnSave.disabled = true;
    const originalText = btnSave.innerText;
    btnSave.innerText = 'Actualizando...';
    if (errorContainer) errorContainer.innerHTML = '';

    try {
        const response = await fetch('/api/v1/users/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) { handleLogout(); return; }
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Error al actualizar el perfil.');
        }

        const updatedUser = await response.json();
        renderProfilePreview(updatedUser);
        alert('¡Perfil actualizado con éxito!');

        document.getElementById('profile-password').value = '';
        fetchProjects();
    } catch (error) {
        console.error(error);
        if (errorContainer) errorContainer.innerHTML = '<div class="alert alert-danger py-2">' + error.message + '</div>';
    } finally {
        btnSave.disabled = false;
        btnSave.innerText = originalText;
    }
}

// -------------------------------------------------------------------------
// MÓDULO: Asistente IA PMO (Fase 38)
// -------------------------------------------------------------------------

function toggleChat() {
    const chatWindow = document.getElementById('chatbot-window');
    if (chatWindow) {
        chatWindow.classList.toggle('d-none');
        if (!chatWindow.classList.contains('d-none')) {
            document.getElementById('chatbot-input').focus();
        }
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    if (!message) return;

    // Renderizar mensaje del usuario
    addChatMessage(message, 'user');
    input.value = '';

    // Mostrar indicador de carga
    const typingId = showChatLoading();

    try {
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            if (response.status === 401) { handleLogout(); return; }
            throw new Error('No se pudo obtener respuesta de la IA.');
        }

        const data = await response.json();
        removeChatLoading(typingId);
        addChatMessage(data.reply, 'bot');
    } catch (error) {
        removeChatLoading(typingId);
        addChatMessage(`Error: ${error.message}`, 'bot', true);
    }
}

function addChatMessage(text, sender, isError = false) {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (!messagesContainer) return;

    const div = document.createElement('div');
    div.className = `chatbot-message chatbot-message-${sender}`;
    if (isError) {
        div.classList.add('bg-danger', 'text-white');
    }

    // Aquí está la magia: si es el bot, usamos marked.parse() para crear la tabla HTML
    if (sender === 'bot' && typeof marked !== 'undefined') {
        div.innerHTML = marked.parse(text);

        // Agregar clases de Bootstrap a las tablas generadas para que se vean bien
        const tables = div.querySelectorAll('table');
        tables.forEach(table => {
            table.classList.add('table', 'table-sm', 'table-bordered', 'mt-2', 'bg-white');
        });
    } else {
        // Si es el usuario, lo mantenemos como texto plano por seguridad
        div.innerText = text;
    }

    messagesContainer.appendChild(div);
    // Scroll al final
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showChatLoading() {
    const messagesContainer = document.getElementById('chatbot-messages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'chatbot-typing px-3';
    div.innerText = 'La IA está pensando...';
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function removeChatLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

