import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Variables and DOMContentLoaded
new_top = """// app.js

let authToken = localStorage.getItem('token');
let currentUserRole = localStorage.getItem('role');

function checkAuth() {
    if (!authToken) {
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    } else {
        applyRoleUI();
        fetchProjects();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/v1/reports/export', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                if (response.status === 401) { handleLogout(); return; }
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'pmo_report.csv';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (err) {
                console.error(err);
            }
        });
    }

    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', handleLogout);
    }

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const createUserForm = document.getElementById('create-user-form');
    if (createUserForm) {
        createUserForm.addEventListener('submit', createUser);
    }

    const btnAdminUsers = document.getElementById('btn-admin-users');
    if (btnAdminUsers) {
        btnAdminUsers.addEventListener('click', fetchUsers);
    }

    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', handleCreateProject);
    }
});"""

content = re.sub(
    r"// app\.js.*?\}\);\n\}\);\n", 
    new_top + "\n", 
    content, 
    flags=re.DOTALL
)

# Replace plain fetches
fetch_projects_old = "const response = await fetch('/api/v1/projects');"
fetch_projects_new = "const response = await fetch('/api/v1/projects', { headers: { 'Authorization': 'Bearer ' + authToken } });\n        if (response.status === 401) { handleLogout(); return; }"
content = content.replace(fetch_projects_old, fetch_projects_new)

fetch_phases_old = "const response = await fetch(`/api/v1/projects/${projectId}/phases`);"
fetch_phases_new = "const response = await fetch(`/api/v1/projects/${projectId}/phases`, { headers: { 'Authorization': 'Bearer ' + authToken } });\n        if (response.status === 401) { handleLogout(); return; }"
content = content.replace(fetch_phases_old, fetch_phases_new)

content = content.replace(
    """        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });""",
    """        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify(projectData)
        });
        if (response.status === 401) { handleLogout(); return; }"""
)

content = content.replace(
    """            const dateResponse = await fetch(`/api/v1/phases/${phaseId}/dates`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: startDateVal,
                    estimated_end_date: endDateVal
                })
            });""",
    """            const dateResponse = await fetch(`/api/v1/phases/${phaseId}/dates`, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({
                    start_date: startDateVal,
                    estimated_end_date: endDateVal
                })
            });
            if (dateResponse.status === 401) { handleLogout(); return; }"""
)

content = content.replace(
    """            const statusResponse = await fetch(`/api/v1/phases/${phaseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: statusVal
                })
            });""",
    """            const statusResponse = await fetch(`/api/v1/phases/${phaseId}`, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({
                    status: statusVal
                })
            });
            if (statusResponse.status === 401) { handleLogout(); return; }"""
)

old_apply = """function applyRoleUI() {
    const btnCreate = document.getElementById('btn-create-project');
    const btnExport = document.getElementById('btn-export');

    if (currentRole === 'Admin' || currentRole === 'PMO') {
        if (btnCreate) btnCreate.style.display = 'inline-block';
        if (btnExport) btnExport.style.display = 'inline-block';
    } else {
        if (btnCreate) btnCreate.style.display = 'none';
        if (btnExport) btnExport.style.display = 'none';
    }
}"""
new_apply = """function applyRoleUI() {
    const btnCreate = document.getElementById('btn-create-project');
    const btnExport = document.getElementById('btn-export');
    const btnAdminUsers = document.getElementById('btn-admin-users');
    const btnLogout = document.getElementById('btn-logout');

    if (btnLogout) btnLogout.style.display = 'inline-block';

    if (currentUserRole === 'Admin') {
        if (btnAdminUsers) btnAdminUsers.style.display = 'inline-block';
    } else {
        if (btnAdminUsers) btnAdminUsers.style.display = 'none';
    }

    if (currentUserRole === 'Admin' || currentUserRole === 'PMO') {
        if (btnCreate) btnCreate.style.display = 'inline-block';
        if (btnExport) btnExport.style.display = 'inline-block';
    } else {
        if (btnCreate) btnCreate.style.display = 'none';
        if (btnExport) btnExport.style.display = 'none';
    }
}"""
content = content.replace(old_apply, new_apply)

additional_logic = """

// Auth Logic
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
    params.append('username', email); // FastAPI OAuth2 requies 'username' for the email
    params.append('password', password);

    try {
        const response = await fetch('/api/v1/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params
        });

        if (!response.ok) {
            throw new Error('Credenciales incorrectas');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        
        // Decode JWT to get role
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        currentUserRole = payload.role;
        localStorage.setItem('role', currentUserRole);

        // Hide modal
        const modalEl = document.getElementById('loginModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) {
            modalInstance.hide();
        }

        applyRoleUI();
        fetchProjects();

    } catch (error) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger py-2 mb-3" role="alert">
                ${error.message}
            </div>
        `;
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

// IAM Admin Logic
async function fetchUsers() {
    if (currentUserRole !== 'Admin') return;
    
    try {
        const response = await fetch('/api/v1/users', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        
        if (response.status === 401) { handleLogout(); return; }
        
        if (!response.ok) {
            throw new Error('Error al obtener usuarios');
        }
        
        const users = await response.json();
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';
        
        users.forEach(user => {
            if (user.is_deleted) return; // Do not show soft-deleted users
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${user.id}</td>
                <td>${user.full_name}</td>
                <td>${user.email}</td>
                <td><span class="badge bg-secondary">${user.role}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">Dar de baja</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar la lista de usuarios.');
    }
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
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify({
                full_name: name,
                email: email,
                password: password,
                role: role
            })
        });
        
        if (response.status === 401) { handleLogout(); return; }
        
        if (!response.ok) {
            throw new Error('No se pudo crear el usuario');
        }
        
        document.getElementById('create-user-form').reset();
        fetchUsers();
        
    } catch (error) {
        console.error('Error:', error);
        alert('Hubo un problema al crear al usuario. Puede que el email ya exista.');
    }
}

async function deleteUser(id) {
    if (!confirm('¿Estás seguro de que deseas dar de baja a este usuario?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        
        if (response.status === 401) { handleLogout(); return; }
        
        if (!response.ok) {
            throw new Error('Error al dar de baja el usuario');
        }
        
        fetchUsers(); // Refresh table
        
    } catch (error) {
        console.error('Error:', error);
        alert('No se pudo dar de baja al usuario.');
    }
}
"""
content = content + additional_logic

content = content.replace("currentRole === 'Developer'", "currentUserRole === 'Developer'")
content = content.replace("currentRole === 'PMO'", "currentUserRole === 'PMO'")
content = content.replace("currentRole === 'Admin'", "currentUserRole === 'Admin'")

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("App.js successfully updated!")
