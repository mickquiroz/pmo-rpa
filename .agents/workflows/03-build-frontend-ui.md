---
description: Build the Vanilla HTML/JS Frontend MVP and mount it on FastAPI.
---

1. **Define Inputs & Target Environment**
   - Working directory: `C:\Users\FX516PC-HN558W\Documents\Antigravity_test\pmo-rpa`
   - Target Frontend folder: `./frontend`
   - Target files: `./frontend/index.html`, `./frontend/app.js`, `./frontend/style.css`

2. **Update Backend to Serve Static Files**
   - Modify `./api/main.py`:
     - Import: `from fastapi.staticfiles import StaticFiles`
     - Add the mount point at the bottom of the file (before any `if __name__` block): 
       `app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")`

3. **Initialize Frontend Directory**
   - Create the `./frontend` directory.

4. **Develop HTML Structure (`index.html`)**
   - Use Bootstrap 5 via CDN for professional PMO styling.
   - Include a Navbar with title "PMO RPA Dashboard".
   - Create a Main Container.
   - Add a section for the "Projects Overview" (a table or grid).
   - Link `style.css` and `app.js`.

5. **Develop Styles (`style.css`)**
   - Add minimal custom CSS to ensure a clean, corporate look (e.g., subtle shadows, status colors: green/yellow/red).

6. **Develop Frontend Logic (`app.js`)**
   - Create a function `fetchProjects()` that calls `/api/v1/projects`.
   - Create a function `renderProjects(projects)` that dynamically populates the HTML table/grid with the data. 
   - Display the `process_name`, `developer_name`, `health_status`, and a Bootstrap Progress Bar utilizing the `progress_percentage`.

7. **Verify Frontend Integration**
   - Ensure that when the FastAPI server runs, navigating to `http://127.0.0.1:8000/` loads the UI and displays the seed project.

8. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(ui): build frontend base with Bootstrap and integrate with FastAPI backend"`