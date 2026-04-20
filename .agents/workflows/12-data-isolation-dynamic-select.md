---
description: Implement Data Isolation for Developers and Dynamic Developer Select for PMOs
---

1. **Backend: Data Isolation (Filter Projects)**
   - Modify `./api/main.py`:
     - In `GET /api/v1/projects`, inject `current_user: dict = Depends(get_current_user)`.
     - Update `_PROGRESS_QUERY` logic. If `current_user["role"] == "Developer"`, append a `WHERE p.assigned_developer_id = ?` clause before the `GROUP BY` statement. Pass the `current_user["id"]` to the `execute()` parameters.
     - If Admin or PMO, run the query without the WHERE clause.

2. **Backend: Dynamic Developer List Endpoint**
   - Modify `./api/main.py`:
     - Create a new endpoint `GET /api/v1/users/developers` protected by `get_current_user`.
     - If the role is "Developer", raise a 403 Forbidden (Only Admin/PMO can list devs).
     - Query SQLite: `SELECT id, name, email FROM Users WHERE role = 'Developer' AND is_active = 1`.
     - Return the list.

3. **Frontend: Clean Hardcoded Select**
   - Modify `./frontend/index.html`:
     - Locate `<select class="form-select" id="assigned-developer" required>`.
     - Remove the hardcoded `<option value="3">...` inside it. Leave it empty.

4. **Frontend: Populate Select Dynamically**
   - Modify `./frontend/app.js`:
     - Create an `async function populateDevelopersSelect()`.
     - Fetch `/api/v1/users/developers` using `authToken`.
     - Get the `<select id="assigned-developer">` element.
     - Loop through the users and append: `<option value="${dev.id}">${dev.name} (${dev.email})</option>`.
     - Call this function inside `applyRoleUI()` ONLY if `currentUserRole === 'Admin' || currentUserRole === 'PMO'`.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(api): data isolation for developers and dynamic assign select"`