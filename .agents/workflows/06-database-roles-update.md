---
description: Refactor the database to replace Developers with a unified Users table supporting Roles (Admin, PMO, Developer) and add CRUD endpoints.
---

1. **Update Database Schema (Users & Roles)**
   - Modify `./scripts/init_db.py`:
     - Rename `DDL_DEVELOPERS` to `DDL_USERS`.
     - Change the table name from `Developers` to `Users`.
     - Add a new column `role` TEXT NOT NULL CHECK(role IN ('Admin', 'PMO', 'Developer')).
     - Update `DDL_PROJECTS` to change `developer_id` to `assigned_developer_id` referencing `Users(id)`.
     - Update Seed Data to include 3 users: 1 Admin, 1 PMO, and 1 Developer.
     - Run the script to drop and recreate the DB with the new schema.

2. **Update Backend Models & Logic**
   - Modify `./api/main.py`:
     - Update all SQL queries that previously referenced the `Developers` table to reference the `Users` table and the new `assigned_developer_id` column.
     - Add Pydantic schemas for `ProjectCreate` (to allow adding new projects via API) and `PhaseCreate`.
     
3. **Add CRUD Endpoints for PMO**
   - In `./api/main.py` add:
     - `POST /api/v1/projects`: Inserts a new project and automatically generates the 4 default RPA phases for it in 'Pending' status.
     - `PUT /api/v1/phases/{phase_id}/dates`: Allows PMO to update `start_date` and `estimated_end_date` of a specific phase.

4. **Verify Backend**
   - Run the FastAPI server and use Swagger UI (`/docs`) to verify that the new `POST` endpoint creates a project and its 4 phases successfully.

5. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(auth): refactor DB to support users/roles and add PMO CRUD endpoints"`