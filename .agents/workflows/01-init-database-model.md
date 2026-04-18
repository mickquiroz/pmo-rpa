---
description: Initialize SQLite Database, define PMO-RPA schema, and insert base seed data for MVP.
---

1. **Define Inputs & Target Output**
   - Confirm working directory: `C:\Users\FX516PC-HN558W\Documents\Antigravity_test\pmo-rpa`
   - Target DB file: `./data/pmo_rpa.db`
   - Target Python script: `./scripts/init_db.py`

2. **Validate Environment**
   - Ensure the `./data` and `./scripts` directories exist. If not, create them.

3. **Define Database Schema (SQLite)**
   - Table `Developers`: `id` (PK), `name` (text), `email` (text), `is_active` (boolean).
   - Table `Projects`: `id` (PK), `process_name` (text), `developer_id` (FK), `start_date` (date), `estimated_end_date` (date), `health_status` (text: Green, Yellow, Red).
   - Table `Phases`: `id` (PK), `project_id` (FK), `phase_name` (text), `weight_percentage` (integer), `status` (text: Pending, In Progress, Completed), `completion_date` (date).
   - Table `Blockers`: `id` (PK), `project_id` (FK), `description` (text), `report_date` (date), `resolver_owner` (text), `status` (text: Open, Resolved).

4. **Generate Python Initialization Script**
   - Write `./scripts/init_db.py` using standard `sqlite3`.
   - Include `CREATE TABLE IF NOT EXISTS` for all tables.
   - Enforce Foreign Key constraints (`PRAGMA foreign_keys = ON;`).

5. **Generate Seed Data (Dummy Data)**
   - Add a function to `./scripts/init_db.py` to insert:
     - 1 Developer (e.g., "John Doe RPA").
     - 1 Project assigned to John Doe.
     - 4 standard RPA Phases for that project (Discovery 10%, Design 30%, Development 40%, UAT 20%).
   - Use `INSERT OR IGNORE` to prevent duplication on multiple runs.

6. **Execute Initialization**
   // turbo
   - Run `python ./scripts/init_db.py`

7. **Verify Database Creation**
   - Confirm `./data/pmo_rpa.db` exists and is > 0 bytes.
   - Output a success message to the terminal.

8. **Commit Artifacts (MVP Baseline)**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(db): initialize SQLite database and base schema for PMO-RPA"`