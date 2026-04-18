---
description: Build the FastAPI backend MVP for the PMO-RPA system, connecting to the SQLite database.
---

1. **Define Inputs & Target Environment**
   - Confirm working directory: `C:\Users\FX516PC-HN558W\Documents\Antigravity_test\pmo-rpa`
   - Database path: `./data/pmo_rpa.db`
   - Target API file: `./api/main.py`
   - Required libraries: `fastapi`, `uvicorn`, `pydantic`

2. **Initialize Environment (if not ready)**
   - Create the `./api` directory.
   - Install dependencies:
   // turbo
   - Run `pip install fastapi uvicorn pydantic`

3. **Define Pydantic Models (Schemas)**
   - Create schemas to validate input/output data.
   - `ProjectResponse`: id, process_name, developer_name, health_status, start_date, estimated_end_date, progress_percentage.
   - `PhaseUpdate`: status (Pending, In Progress, Completed).
   - `BlockerCreate`: project_id, description, resolver_owner.

4. **Develop API Endpoints in `./api/main.py`**
   - Initialize FastAPI app.
   - Implement database connection dependency/helper.
   - **GET `/projects`**: Returns all projects. Calculate `progress_percentage` on the fly using the Phases table (e.g., sum of phase weights where status = 'Completed', plus half weight for 'In Progress').
   - **GET `/projects/{project_id}/phases`**: Returns all phases for a specific project.
   - **PATCH `/phases/{phase_id}`**: Updates the status of a phase.
   - **POST `/blockers`**: Inserts a new blocker for a project.

5. **CORS Configuration**
   - Add CORS Middleware to allow future connections from the local frontend (allow origins `["*"]` for MVP).

6. **Verify API Starts**
   // turbo
   - Run `uvicorn api.main:app --reload` (Inform the user to run this or run a quick test script to verify compilation, then shut it down).

7. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(api): build FastAPI backend MVP with project, phase, and blocker endpoints"`