---
description: Implement JWT authentication, password hashing, and secure endpoints for the PMO-RPA API.
---

1. **Install Security Dependencies**
   // turbo
   - Run `pip install passlib[bcrypt] python-jose python-multipart`

2. **Update Database Schema for Passwords**
   - Modify `./scripts/init_db.py`:
     - Add a `hashed_password` TEXT NOT NULL column to the `Users` table.
     - Import `from passlib.context import CryptContext` at the top.
     - Setup `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`.
     - Update the `SEED_USERS` to include a plain password (e.g., "admin123", "pmo123", "dev123").
     - When inserting users, hash the plain password using `pwd_context.hash(pwd)` and insert it into `hashed_password`.
     - Run the script to recreate the database.

3. **Create Security Module**
   - Create a new file `./api/auth.py`:
     - Configure OAuth2 using `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")`.
     - Set a `SECRET_KEY` (use a static string for MVP like "super-secret-pmo-key") and `ALGORITHM = "HS256"`.
     - Implement `verify_password(plain, hashed)` and `get_password_hash(password)`.
     - Implement `create_access_token(data: dict)`.
     - Implement the `get_current_user` dependency that reads the token, decodes it, queries the DB, and returns the User record.

4. **Add Login Endpoint**
   - Modify `./api/main.py`:
     - Import `OAuth2PasswordRequestForm` from `fastapi.security`.
     - Add the `POST /api/v1/auth/token` endpoint. It should verify the email (username) and password, and return `{"access_token": token, "token_type": "bearer", "role": user_role}`.

5. **Protect Endpoints**
   - Modify `./api/main.py`:
     - Add `current_user: dict = Depends(get_current_user)` to `POST /api/v1/projects` as a test to ensure it's protected. (We will protect all others in the next phase to avoid breaking the current UI simulator).

6. **Commit Artifacts**
   // turbo
   - Run `git add .`
   // turbo
   - Run `git commit -m "feat(auth): implement JWT authentication, password hashing, and login endpoint"`