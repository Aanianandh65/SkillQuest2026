# Skill Quest 2026 — Render Deployment Notes

## Added in this version

1. **Student credential email**
   - When an admin registers a student, the app emails the student's username and temporary password.
   - SMTP credentials are read from environment variables.
   - No email password is hard-coded in the source.

2. **Question Bank management**
   - Edit uploaded questions.
   - Delete questions that have not yet been used in an exam.
   - Questions already linked to an exam are protected so historical exam records are not broken.

3. **Data reset controls**
   - **Clear All Results** removes exam attempts, answers and exam-question assignments.
   - **Clear All Students** removes student accounts, student profiles and their examination records.
   - Both actions require browser confirmation.

4. **Skill Quest 2026 logo**
   - Replaced the `EDU` placeholder in the login, admin, student and examination headers with the supplied Skill Quest 2026 artwork.

5. **Render readiness**
   - Added `gunicorn`.
   - Added environment-based `SECRET_KEY` and `DATABASE_URL`.
   - Added `render.yaml`.

## SMTP environment variables

Set these in Render → Environment:

- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_USE_TLS`

For Gmail, use an **App Password**, not your normal Gmail password.

Example:

```text
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=your-email@gmail.com
MAIL_USE_TLS=true
```

## Important Render database note

The application can use SQLite locally, but a normal Render web-service filesystem is not a safe place for long-term SQLite data. For a production Skill Quest system, use a persistent database (preferably a Render PostgreSQL database) or a paid persistent disk if you intentionally keep SQLite.

The application already reads `DATABASE_URL`, so the database configuration can be changed without changing the application code.

## Start command

```text
gunicorn run:app
```

## Local development

```text
pip install -r requirements.txt
python run.py
```
