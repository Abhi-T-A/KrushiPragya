# KrushiPragya - Backend Foundation

## 1. Project Name
**KrushiPragya Backend**

## 2. Purpose
KrushiPragya is an AI-powered agriculture platform designed to empower farmers with hyper-local weather advisories, crop health and disease diagnosis, market price insights, government schemes, verified agricultural advisories, and bilingual (Kannada/English) AI assistance.

This repository component houses the modular monolithic FastAPI backend foundation.

## 3. Tech Stack
- **Runtime**: Python 3.11+ (Tested on Python 3.12)
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Data Validation & Settings**: Pydantic v2 & Pydantic Settings
- **ORM & Database Toolkit**: SQLAlchemy 2.x
- **Database Driver**: psycopg2-binary (PostgreSQL / Supabase)
- **Database Migrations**: Alembic
- **Testing**: pytest & HTTPX
- **Configuration Management**: python-dotenv

## 4. Project Structure
```text
backend/
├── alembic/              # Alembic database migration environment
│   ├── versions/         # Migration script versions
│   └── env.py            # Migration runtime configuration
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entrypoint, CORS, exception handlers
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py # Health and database connectivity routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py     # Pydantic Settings and environment variable management
│   │   └── logging.py    # Structured centralized application logging
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py       # SQLAlchemy 2.0 DeclarativeBase
│   │   └── connection.py # Engine, SessionLocal, and get_db dependency
│   ├── models/           # SQLAlchemy database models (placeholder)
│   ├── schemas/          # Pydantic validation schemas
│   │   └── health.py
│   └── services/         # Business logic layer (placeholder)
├── tests/
│   ├── __init__.py
│   └── test_health.py    # Health & database test suite
├── .env                  # Local environment file (DO NOT commit credentials)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules for Python / virtualenv
├── alembic.ini           # Alembic configuration file
├── requirements.txt      # Python dependencies
└── README.md             # Backend documentation
```

## 5. Local Setup & Prerequisites
Ensure you have Python 3.11 or higher installed on your system.
Verify in PowerShell:
```powershell
python --version
```

## 6. Virtual Environment Setup
From the `backend` directory, create a virtual environment:
```powershell
python -m venv .venv
```

Activate the virtual environment:
- **Windows PowerShell**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Command Prompt**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

## 7. Dependency Installation
Ensure the virtual environment is activated, then install all dependencies:
```powershell
pip install -r requirements.txt
```

## 8. Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Configure your variables in `.env`:
```env
APP_NAME=KrushiPragya
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# Add your Supabase PostgreSQL connection string below:
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
```

> **Security Note**: Never commit `.env` or hardcode database passwords in version control.

## 9. Running FastAPI
Start the local development server with auto-reload:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will start listening at: `http://127.0.0.1:8000`

## 10. Running Tests
Run the automated test suite with pytest:
```powershell
pytest -v
```

## 11. Running Alembic Migrations
When your database credentials are set in `.env`:
- Check current migration status:
  ```powershell
  alembic current
  ```
- Generate a new migration:
  ```powershell
  alembic revision --autogenerate -m "initial_schema"
  ```
- Apply migrations to the database:
  ```powershell
  alembic upgrade head
  ```

## 12. Interactive API Documentation (Swagger & ReDoc)
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
