---
description: Build the Admin API endpoints to manage users (Create, Read, Soft Delete) with strict Role-Based Access Control (RBAC).
---

1. **Add Admin Role Validator**
   - Modify `./api/auth.py`:
     - Create a new dependency `def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:`
     - If `current_user["role"] != "Admin"`, raise `HTTPException(403, "Permisos insuficientes. Se requiere rol Admin.")`.
     - Return `current_user`.

2. **Define Pydantic Models for Users**
   - Modify `./api/main.py`:
     - Import `get_admin_user` and `get_password_hash` from `.auth`.
     - Create `UserCreate` schema: `name`, `email` (EmailStr validation optional for now), `password`, `role` (Literal['PMO', 'Developer']).
     - Create `UserResponse` schema: `id`, `name`, `email`, `role`, `is_active`.

3. **Develop CRUD Endpoints (Protected by Admin)**
   - Modify `./api/main.py`:
     - **POST `/api/v1/users`**: 
       - Depends on `get_admin_user`.
       - Hashes the incoming password using `get_password_hash(payload.password)`.
       - Inserts the new user into the database. Returns `UserResponse`.
       - Handle `sqlite3.IntegrityError` to return a 400 error if the email already exists.
     - **GET `/api/v1/users`**:
       - Depends on `get_admin_user`.
       - Returns a list of all users from the DB (excluding passwords).
     - **DELETE `/api/v1/users/{user_id}`**:
       - Depends on `get_admin_user`.
       - **CRITICAL:** Do NOT drop the row (to keep Foreign Key constraints on Projects intact). Instead, perform a "Soft Delete" by updating `is_active = 0`. 

4. **Verify Backend**
   - Verify that standard users cannot hit these endpoints via Swagger UI.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(api): add admin endpoints to manage users with RBAC"`