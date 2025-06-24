# SQL Ledger System - Setup Guide

## Overview

This guide provides instructions for setting up and running the SQL Ledger System, which includes:
-   **Backend:** A Python FastAPI application providing the core API.
-   **Unified Frontend:** A Vue.js 3 application (in `customer-frontend/`) serving both the customer-facing portal and the admin panel.
-   **CLI Config Tool:** A Python CLI tool (in `config-cli/`) for managing backend `.env` configurations.

## Prerequisites

Before you begin, ensure you have the following installed:
-   Python 3.9+
-   Node.js (LTS version recommended, e.g., 18.x or 20.x)
-   npm (usually comes with Node.js) or yarn
-   PostgreSQL server (e.g., version 13+)

## Backend Setup (Project Root)

1.  **Navigate to the Project Root Directory:**
    *(Ensure you are in the main project directory where `initial_db.py`, `requirements.txt` (for backend), etc., are located.)*

2.  **Create and Activate Python Virtual Environment (Recommended):**
    *(It's good practice to create this in the project root)*
    ```bash
    python -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows (cmd.exe):
    # venv\Scripts\activate.bat
    # On Windows (PowerShell):
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure `requirements.txt` at the project root is comprehensive for the backend, including `fastapi`, `uvicorn`, `psycopg2-binary`, `passlib[bcrypt]`, `python-jose[cryptography]`, `python-multipart`, `pydantic[email]`, `python-dotenv`, etc.)*

4.  **Database Setup:**
    *   **Create PostgreSQL Database & User:**
        *   Log in to your PostgreSQL server (e.g., using `psql`).
        *   Create a dedicated user (role) for the application:
            ```sql
            CREATE USER sql_ledger_user WITH PASSWORD 'your_strong_password';
            ```
        *   Create the database:
            ```sql
            CREATE DATABASE sql_ledger_db OWNER sql_ledger_user;
            ```
        *   Grant privileges:
            ```sql
            GRANT ALL PRIVILEGES ON DATABASE sql_ledger_db TO sql_ledger_user;
            ```
    *   **Configure `.env` File:**
        *   In the project root directory, create a `.env` file (or copy from `.env.example` if provided).
        *   This file stores sensitive configuration. Key variables include:
            *   `DATABASE_URL=postgresql://sql_ledger_user:your_strong_password@localhost:5432/sql_ledger_db` (Adjust host, port, user, password, dbname as needed)
            *   `JWT_SECRET_KEY=your_very_strong_jwt_secret_key_32_bytes_or_more`
            *   `JWT_ALGORITHM=HS256`
            *   `ACCESS_TOKEN_EXPIRE_MINUTES=30`
            *   `DEFAULT_CUSTOMER_ROLE_NAME=customer`
            *   *(Add any other relevant .env variables like mail server settings if implemented)*
        *   You can manage this file manually or use the `config-cli` tool (see section below). For initial setup, manual creation is common.

5.  **Database Initialization (Schema & Tables):**
    *   The database schema (tables, types, triggers, etc.) needs to be applied to your newly created database.
    *   Run the provided Python script from the project root directory:
        ```bash
        python initial_db.py
        ```
    *   This script will execute the SQL commands found in `schema.sql`, `schema_updates.sql`, `auth_schema.sql`, and `schema_audit.sql` (all located at the project root) to set up your database structure and pre-populate necessary lookup data (like roles, account statuses, transaction types).

6.  **Create First Admin User:**
    *   To create an initial administrative user for the system, run the following script from the project root directory. Replace placeholders with your desired credentials.
        ```bash
        python create_admin_user.py --username youradminloginname --password yoursecurepassword --email admincontact@example.com
        ```
    *   This user will have the 'admin' role and can be used to log into the admin panel.

7.  **Running the Backend Application:**
    *   From the project root directory (with virtual environment activated):
        ```bash
        uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   *(Note: The Uvicorn command assumes your FastAPI app instance is named `app` within a file named `main.py` inside an `api` directory, i.e. `api/main.py`. Adjust if your main backend file is at the root or named differently, e.g., `uvicorn main_backend:app` if `main_backend.py` is at root)*
    *   `--reload` enables auto-reloading on code changes, useful for development.
    *   The API should now be accessible at `http://localhost:8000`.

## Frontend Setup (`customer-frontend/` - Unified App)

1.  **Navigate to the Frontend Directory:**
    ```bash
    # From the project root
    cd customer-frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    # or if using yarn:
    # yarn install
    ```

3.  **Configure Environment Variables:**
    *   In the `customer-frontend/` directory, create a `.env.development` file (if it doesn't exist, you might copy from `.env.development.example`).
    *   Ensure it contains the following variables, pointing to your running backend:
        ```env
        VITE_API_BASE_URL=http://localhost:8000/api/v1
        VITE_ADMIN_API_BASE_URL=http://localhost:8000
        ```
        *   `VITE_API_BASE_URL` is for the customer-facing API v1.
        *   `VITE_ADMIN_API_BASE_URL` is the base URL for admin-related API calls (including `/admin/login` for sessions and `/api/admin/...` for JSON APIs).

4.  **Running the Frontend Application:**
    *   From the `customer-frontend/` directory:
        ```bash
        npm run dev
        # or if using yarn:
        # yarn dev
        ```
    *   The frontend application should be accessible at `http://localhost:5173` (or another port if 5173 is busy - check your terminal output).

## CLI Tool Setup (`config-cli/`)

The CLI tool is used for managing the backend's `.env` file. For detailed instructions:
1.  Navigate to the `config-cli/` directory.
2.  Refer to the `CLI_GUIDE.md` in that directory.
3.  Quick setup:
    ```bash
    cd config-cli
    # Create and activate a Python virtual environment (recommended)
    python -m venv venv
    source venv/bin/activate # or venv\Scripts\activate
    pip install -r requirements.txt
    # Test the tool
    python main.py --help
    ```

## Order of Operations for Full System Startup

1.  Ensure your PostgreSQL server is running.
2.  Start the Backend application.
3.  Start the Frontend application.

You should now be able to access the customer portal and the admin panel via your browser.
```
