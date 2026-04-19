---
description: Build the CSV export feature for the PMO dashboard to download project statuses and progress.
---

1. **Define Inputs & Target Environment**
   - Working directory: `C:\Users\FX516PC-HN558W\Documents\Antigravity_test\pmo-rpa`
   - Target Backend file: `./api/main.py`
   - Target Frontend files: `./frontend/index.html`, `./frontend/app.js`

2. **Backend: Create Export Endpoint**
   - Modify `./api/main.py`:
     - Import standard libraries: `import csv`, `import io`.
     - Import `StreamingResponse` from `fastapi.responses`.
     - Create a new endpoint `GET /api/v1/reports/export`.
     - Re-use the `_PROGRESS_QUERY` logic to fetch all projects with their calculated progress.
     - Generate a CSV in memory using `io.StringIO()` and `csv.writer()`.
     - Columns should be: `ID, Proceso, Desarrollador, Estado de Salud, Fecha Inicio, Fecha Fin, Avance (%)`.
     - Return the `StreamingResponse` with `media_type="text/csv"` and header `Content-Disposition: attachment; filename="pmo_rpa_report.csv"`.

3. **Frontend: UI Button**
   - Modify `./frontend/index.html`:
     - Add a "Descargar Reporte" button (e.g., `<button id="btn-export" class="btn btn-success">...</button>`) in the header card or next to the "Resumen de Proyectos" title. Use Bootstrap utilities to align it to the right.

4. **Frontend: Logic**
   - Modify `./frontend/app.js`:
     - Add an event listener to `#btn-export`.
     - The function should call `window.open('/api/v1/reports/export', '_blank');` to trigger the browser's native file download.

5. **Verify Feature**
   - Run the FastAPI server.
   - Click the "Descargar Reporte" button and verify a valid `.csv` file is downloaded containing the seed data.

6. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(reports): add CSV export endpoint and download button"`