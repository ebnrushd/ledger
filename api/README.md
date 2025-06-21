# SQL Ledger API

This directory contains the FastAPI backend for the SQL Ledger application.

## Prerequisites

- Python 3.8+
- PostgreSQL server running and accessible
- Database schema applied (from `schema.sql`, `schema_updates.sql`, `auth_schema.sql`, `schema_audit.sql` in the project root)
- Environment variables for database connection set (e.g., `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). Refer to `database.py`.

## Setup

1.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    Navigate to the project root directory (the one containing this `api` folder and also `core`, `database.py` etc.).
    ```bash
    pip install -r api/requirements.txt
    ```

3.  **Set Environment Variables:**
    Ensure the database connection environment variables are set in your shell or a `.env` file (FastAPI/Pydantic can auto-load .env files if `python-dotenv` is installed, or you can manage them manually).
    Example:
    ```bash
    export DB_NAME="sql_ledger_db"
    export DB_USER="ledger_user"
    export DB_PASSWORD="securepassword123"
    export DB_HOST="localhost"
    export DB_PORT="5432"
    ```

## Running the API

Navigate to the **project root directory** (e.g., `sql-ledger/`).
Run the Uvicorn server:

```bash
uvicorn api.main:app --reload
```

This command tells Uvicorn:
-   `api.main:app`: Look for the `app` object in the `api/main.py` file.
-   `--reload`: Enable auto-reloading when code changes (useful for development).

The API will typically be available at `http://127.0.0.1:8000`.

## API Documentation

Once the API is running, interactive OpenAPI documentation (Swagger UI) is available at:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Alternative ReDoc documentation is available at:
[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Project Structure

-   `main.py`: FastAPI application instance, global exception handlers, router includes.
-   `models.py`: Pydantic models for request/response validation and serialization.
-   `dependencies.py`: FastAPI dependencies (e.g., for database sessions).
-   `routers/`: Directory containing API route modules (e.g., `customers.py`, `accounts.py`).
-   `requirements.txt`: Python package dependencies.

This API uses services from the `core` and `reporting` directories located in the parent project structure. Ensure your `PYTHONPATH` is set up correctly if you run `uvicorn` from a different directory, or run from the project root as described above.
```
