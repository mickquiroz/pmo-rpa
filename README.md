# 🚀 PMO-RPA Dashboard

![Status](https://img.shields.io/badge/Status-Development-orange)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A premium, state-of-the-art Project Management Office (PMO) dashboard specifically designed for **RPA (Robotic Process Automation)** operations. This platform provides real-time visibility into project lifecycles, phase-level tracking, and automated progress calculation.

---

## ✨ Key Features

- **📊 Real-time Progress Tracking**: Automated percentage calculation based on phase status (Pending, In Progress, Completed).
- **📅 Interactive Gantt Chart**: Built-in Frappe Gantt integration for visual timeline management.
- **🔐 Enterprise RBAC**: Dynamic Role-Based Access Control (Admin, PMO, Developer, Pre-Sales) with JWT-secured endpoints.
- **🛠️ Dynamic Phase Management**: Customizable project templates and phase-level granular control.
- **💬 Collaboration Hub**: Phase-specific audit comments for seamless communication between developers and PMOs.
- **📈 Executive Reporting**: One-click CSV export for offline project status analysis.
- **🛡️ Data Isolation**: Role-specific data filtering (Developers only see their tasks, PMOs see everything).

---

## 🛠️ Technology Stack

### Backend
- **Core**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database**: SQLite (Optimized with Foreign Keys & WAL)
- **Security**: OAuth2 with Password Hashing (bcrypt) & JWT Tokens
- **Validation**: Pydantic v2

### Frontend
- **Logic**: Vanilla JavaScript (ES6+)
- **Styling**: Bootstrap 5 with custom "Glassmorphism" components
- **Visualization**: Frappe Gantt
- **Communication**: Fetch API with interceptors for Auth headers

---

## 🚀 Quick Start

### 1. Backend Setup
1. Navigate to the `api` directory.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic python-multipart python-jose[cryptography] passlib[bcrypt]
   ```
3. Initialize the database (if not present):
   ```bash
   python scripts/init_db.py  # Use your specific init script
   ```
4. Run the server:
   ```bash
   uvicorn api.main:app --reload
   ```

### 2. Frontend Access
Simply open `frontend/index.html` in your browser or serve it via a local server (e.g., Live Server).

---

## 📂 Project Structure

```text
pmo-rpa/
├── api/                # FastAPI Backend logic
│   ├── auth.py         # JWT & Security logic
│   └── main.py         # REST Endpoints
├── data/               # SQLite Database storage
├── frontend/           # Vanilla JS Web Interface
│   ├── app.js          # Core UI Logic
│   ├── index.html      # Main Dashboard
│   └── style.css       # Custom premium styles
├── scripts/            # Database initialization and migration scripts
└── .gitignore          # Environment protection
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Developed with ❤️ by the Antigravity Team
</p>
