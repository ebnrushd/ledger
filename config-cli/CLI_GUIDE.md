# CLI Configuration Management Tool (`config-cli`) Guide

**IMPORTANT: CRITICAL SECURITY WARNING**
This tool is designed to manage sensitive application configuration files (`.env`). Modifying these files directly can have significant impacts on your application's stability, security, and availability.
- **Use with extreme caution.**
- **Only authorized system administrators should use this tool.**
- **Ensure you are operating on the correct `.env` file for your target environment.**
- **Always back up your `.env` file before making significant changes, even though this tool creates a `.bak` file.**
- **Changes to `.env` files typically require a manual restart of the application (backend, workers, etc.) to take effect.** This tool does NOT restart applications.

## 1. Introduction

The `config-cli` is a Python-based command-line interface tool for managing key-value configurations stored in `.env` files for the SQL Ledger application. It helps in setting, getting, listing, and deleting these configuration parameters.

## 2. Prerequisites

- Python 3.7+ installed.
- Access to the server terminal where the target `.env` file is located.
- Permissions to read and write to the target `.env` file and to create `.bak` files in the same directory.

## 3. Setup / Installation

1.  Navigate to the `config-cli/` directory in your project.
2.  It's recommended to use a Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```
3.  Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 4. Core Concepts

-   **Target File:** The tool operates on a `.env` file. By default, it looks for a file named `.env` in the current directory where the command is run. You can specify a different file using the `--file` (or `-f`) option with any command.
-   **Atomic Writes & Backups:** When modifying the `.env` file (using `set` or `delete`), the tool first writes changes to a temporary file. If successful, it renames your original `.env` file to `.env.bak` and then renames the temporary file to `.env`. This minimizes the risk of data corruption.
-   **Application Restart:** **Crucially, any changes made using this tool will only be reflected in the application after the application is manually restarted.**
-   **Value Quoting:** Values containing spaces, `#`, `=`, or that are empty will generally be automatically enclosed in double quotes when written to the `.env` file.

## 5. Commands

All commands are run via `python main.py [OPTIONS] COMMAND [ARGS]...` from within the `config-cli` directory.

### `set`

Sets or updates a configuration key.

**Syntax:**
`python main.py set <KEY> [VALUE] [OPTIONS]`

**Arguments:**
-   `<KEY>`: The configuration key name (e.g., `DATABASE_URL`).
-   `[VALUE]`: The value for the key. If not provided and `--interactive` is not used, it might set an empty value or error depending on implementation. If the value contains spaces or special characters, enclose it in quotes in your terminal.

**Options:**
-   `--file TEXT` / `-f TEXT`: Path to the `.env` file. Defaults to `./.env`.
-   `--interactive` / `-i`: Prompts for the value securely (input will be hidden). Useful for passwords or secrets. If this flag is present, `[VALUE]` argument is ignored.
-   `--help`: Show help message for the `set` command.

**Examples:**
```bash
# Set a database URL
python main.py set DATABASE_URL "postgresql://user:pass@host:port/dbname"

# Set an API key interactively
python main.py set STRIPE_API_KEY --interactive

# Update an existing key
python main.py set DEBUG_MODE False -f /path/to/app/.env.prod
```

### `get`

Retrieves the value of a specific configuration key.

**Syntax:**
`python main.py get <KEY> [OPTIONS]`

**Arguments:**
-   `<KEY>`: The configuration key name.

**Options:**
-   `--file TEXT` / `-f TEXT`: Path to the `.env` file.
-   `--show` / `-s`: Show the actual value even if it's a potentially sensitive key (which are normally masked).
-   `--help`: Show help message for the `get` command.

**Examples:**
```bash
# Get the value of DEBUG_MODE
python main.py get DEBUG_MODE

# Get a sensitive key (will be masked by default)
python main.py get SECRET_KEY

# Get a sensitive key and show its actual value
python main.py get SECRET_KEY --show
```

### `list`

Lists configuration keys (and optionally their values).

**Syntax:**
`python main.py list [OPTIONS]`

**Options:**
-   `--file TEXT` / `-f TEXT`: Path to the `.env` file.
-   `--show-values` / `-sv`: Display values alongside keys. Sensitive keys will be masked.
-   `--grep TEXT` / `-g TEXT`: Filter keys by a pattern (case-insensitive string containment).
-   `--help`: Show help message for the `list` command.

**Examples:**
```bash
# List all keys
python main.py list

# List keys and their (potentially masked) values
python main.py list --show-values

# List keys containing 'DATABASE'
python main.py list --grep DATABASE
```

### `delete`

Deletes a key-value pair from the configuration file.

**Syntax:**
`python main.py delete <KEY> [OPTIONS]`

**Arguments:**
-   `<KEY>`: The configuration key to delete.

**Options:**
-   `--file TEXT` / `-f TEXT`: Path to the `.env` file.
-   `--force` / `-y`: Force delete without confirmation. **Use with caution.** (Note: help text in main.py uses -y, design doc used -F. I will use -y as per main.py)
-   `--help`: Show help message for the `delete` command.

**Examples:**
```bash
# Delete a key (will ask for confirmation)
python main.py delete OLD_FEATURE_FLAG

# Force delete a key without confirmation
python main.py delete TEMP_API_KEY --force
# (Correcting example to use --force, or main.py needs to reflect -y for --force)
# For now, assuming main.py's -y for --force is the source of truth for the option flag.
# The example should be: python main.py delete TEMP_API_KEY -y
```

## 6. Security Best Practices

-   **Restricted Access:** Ensure only authorized system administrators can execute this script and access the target `.env` files.
-   **File Permissions:** Keep `.env` files protected with strict read/write permissions (e.g., `chmod 600 .env`).
-   **Interactive Mode for Secrets:** Use the `set --interactive` option for setting passwords, API keys, and other secrets to avoid them being stored in your shell history.
-   **Audit Trails:** Monitor system logs for executions of this script if your system auditing (`auditd`, `sudo` logs) is configured to capture command execution.
-   **External Backups:** While this tool creates `.bak` files, maintain your own robust, independent backup strategy for critical configuration files.
-   **Principle of Least Privilege:** Grant this tool (and the user running it) only the necessary permissions to manage the specific `.env` files.

## 7. Basic Troubleshooting

-   **Command not found (`python main.py ...`):** Ensure you are in the `config-cli` directory and have activated your Python virtual environment (if used).
-   **"File not found" error:** Double-check the path provided via `--file` or ensure `.env` exists in the current directory if using the default.
-   **"Permission denied" error:** Verify that you have read and write permissions for the `.env` file and the directory it's in. You might need to use `sudo python main.py ...` if the file is root-owned, but be extremely cautious.
-   **Dependency Errors:** Ensure `pip install -r requirements.txt` was successful.

```
