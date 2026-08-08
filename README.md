# Supply Chain IQ Pro
Multi-user Supply Chain Intelligence portfolio application.

Features:
- Register/login and per-user data isolation
- Manual CRUD and CSV upload/export
- Executive KPI command center
- Multiple chart types: line, doughnut, bar, and scatter
- Supplier risk scoring
- OTIF, stock-out, inventory value, lead-time and transport-cost analytics
- Audit log
- Rich demo dataset

Run on Windows without PowerShell activation:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```
Open http://127.0.0.1:5000

For production: PostgreSQL, CSRF protection, HTTPS, email verification, rate limiting and production WSGI are recommended.
