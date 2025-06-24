import typer
from pathlib import Path
from typing import Optional, List, cast
import os
import stat

from env_manager import (
    read_env_file_structured,
    write_env_file_structured,
    format_value_for_env,
    parse_env_value,
    _is_sensitive_key # For direct use in main for masking
)

app = typer.Typer(
    help="CLI to manage .env file configurations.",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    add_completion=False
)

def resolve_env_file_path(file_path_str: Optional[str] = None) -> Path:
    """Resolves the .env file path. Defaults to ./.env"""
    if file_path_str:
        return Path(file_path_str).resolve()
    return Path.cwd() / ".env"

def print_styled(message: str, style: Optional[str] = None, fg: Optional[str] = None, bold: Optional[bool] = None):
    """Helper for styled output with Typer."""
    params = {}
    if fg:
        params['fg'] = fg
    if bold is not None: # Allow bold=False
        params['bold'] = bold

    if style: # Predefined styles
        if style == "success":
            params.update({'fg': typer.colors.GREEN, 'bold': True})
        elif style == "error":
            params.update({'fg': typer.colors.RED, 'bold': True})
        elif style == "warning":
            params.update({'fg': typer.colors.YELLOW, 'bold': True})
        elif style == "info":
             params.update({'fg': typer.colors.BLUE})


    typer.secho(message, **params)


@app.command(name="set", help="Set or update a configuration key-value pair.")
def set_config(
    key: str = typer.Argument(..., help="The configuration key to set."),
    value: Optional[str] = typer.Argument(None, help="The value for the configuration key. Required if --interactive is not used."),
    file_path_str: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .env file. Defaults to ./.env in current directory."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt for value securely (input will be hidden).")
):
    """Set or update KEY VALUE in the .env file."""
    env_file = resolve_env_file_path(file_path_str)

    if interactive:
        final_value = typer.prompt(f"Enter value for {key}", hide_input=True)
    elif value is None: # Not interactive and value not provided
        print_styled("Error: VALUE is required if --interactive is not used.", style="error")
        raise typer.Exit(code=1)
    else:
        final_value = value

    original_permissions = None
    if env_file.exists():
        try:
            original_permissions = stat.S_IMODE(os.stat(env_file).st_mode)
        except Exception as e:
            print_styled(f"Warning: Could not read original permissions of {env_file}: {e}", style="warning")

    try:
        structured_data = read_env_file_structured(env_file)
        key_exists = False
        for item in structured_data:
            if item['type'] == 'pair' and item.get('key') == key:
                item['value'] = final_value
                key_exists = True
                break

        if not key_exists:
            structured_data.append({'type': 'pair', 'key': key, 'value': final_value})

        write_env_file_structured(env_file, structured_data, original_permissions)
        print_styled(f"Successfully set {key} in {env_file}", style="success")
        print_styled("Note: Application restart may be required for changes to take effect.", style="info")
    except IOError as e:
        print_styled(f"Error: {e}", style="error")
        raise typer.Exit(code=1)
    except Exception as e_global:
        print_styled(f"An unexpected error occurred: {e_global}", style="error")
        raise typer.Exit(code=1)


@app.command(name="get", help="Get the value of a configuration key.")
def get_config(
    key: str = typer.Argument(..., help="The configuration key to retrieve."),
    file_path_str: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .env file."),
    show_value: bool = typer.Option(False, "--show", "-s", help="Show actual value for potentially sensitive keys.")
):
    """Get KEY from the .env file. Sensitive values are masked by default."""
    env_file = resolve_env_file_path(file_path_str)
    if not env_file.exists() or not env_file.is_file():
        print_styled(f"Error: Configuration file {env_file} not found.", style="error")
        raise typer.Exit(code=1)

    try:
        structured_data = read_env_file_structured(env_file)
        found_item = None
        for item in structured_data:
            if item['type'] == 'pair' and item.get('key') == key:
                found_item = item
                break

        if found_item:
            # Value from structured_data is already raw (unquoted by parser if quoted in file)
            # but it might be string 'None' or empty string. parse_env_value handles this.
            val_from_file = cast(str, found_item.get('value', '')) # Value as it is in file (may be quoted)
            parsed_val = parse_env_value(val_from_file)

            if _is_sensitive_key(key) and not show_value:
                print_styled(f"{key}=******** (masked)")
            else:
                print_styled(f"{key}={parsed_val}")
        else:
            print_styled(f"Key '{key}' not found in {env_file}.", style="error")
            raise typer.Exit(code=1)
    except IOError as e:
        print_styled(f"Error: {e}", style="error")
        raise typer.Exit(code=1)


@app.command(name="list", help="List all configuration keys (and optionally values).")
def list_configs(
    file_path_str: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .env file."),
    show_values: bool = typer.Option(False, "--show-values", "-sv", help="Show values (masked for sensitive keys)."),
    grep: Optional[str] = typer.Option(None, "--grep", "-g", help="Filter keys by pattern (case-insensitive).")
):
    """List configurations from the .env file."""
    env_file = resolve_env_file_path(file_path_str)
    if not env_file.exists() or not env_file.is_file():
        print_styled(f"Error: Configuration file {env_file} not found.", style="error")
        raise typer.Exit(code=1)

    try:
        structured_data = read_env_file_structured(env_file)
        num_found = 0
        for item in structured_data:
            if item['type'] == 'pair':
                key = cast(str, item.get('key'))
                if grep and grep.lower() not in key.lower():
                    continue

                num_found +=1
                if show_values:
                    val_from_file = cast(str, item.get('value', ''))
                    parsed_val = parse_env_value(val_from_file)
                    if _is_sensitive_key(key):
                        typer.echo(f"{key}=******** (masked)")
                    else:
                        typer.echo(f"{key}={parsed_val}")
                else:
                    typer.echo(key)
        if num_found == 0 and grep:
            print_styled(f"No keys found matching pattern: {grep}", style="info")
        elif num_found == 0:
            print_styled(f"No configurations found in {env_file}.", style="info")

    except IOError as e:
        print_styled(f"Error: {e}", style="error")
        raise typer.Exit(code=1)


@app.command(name="delete", help="Delete a configuration key-value pair.")
def delete_config(
    key: str = typer.Argument(..., help="The configuration key to delete."),
    file_path_str: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .env file."),
    force: bool = typer.Option(False, "--force", "-y", help="Force delete without confirmation.") # Changed -f to -y for force
):
    """Delete KEY from the .env file."""
    env_file = resolve_env_file_path(file_path_str)
    if not env_file.exists() or not env_file.is_file():
        print_styled(f"Error: Configuration file {env_file} not found.", style="error")
        raise typer.Exit(code=1)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete the key '{key}' from {env_file}?")
        if not confirm:
            print_styled("Operation cancelled.", style="info")
            raise typer.Abort()

    original_permissions = None
    if env_file.exists():
        try:
            original_permissions = stat.S_IMODE(os.stat(env_file).st_mode)
        except Exception as e:
            print_styled(f"Warning: Could not read original permissions of {env_file}: {e}", style="warning")

    try:
        structured_data = read_env_file_structured(env_file)
        new_data = [item for item in structured_data if not (item['type'] == 'pair' and item.get('key') == key)]

        if len(new_data) == len(structured_data):
            print_styled(f"Key '{key}' not found in {env_file}. Nothing to delete.", style="warning")
            raise typer.Exit(code=0) # Not an error, but key wasn't there

        write_env_file_structured(env_file, new_data, original_permissions)
        print_styled(f"Successfully deleted key '{key}' from {env_file}.", style="success")
        print_styled("Note: Application restart may be required for changes to take effect.", style="info")
    except IOError as e:
        print_styled(f"Error: {e}", style="error")
        raise typer.Exit(code=1)
    except Exception as e_global:
        print_styled(f"An unexpected error occurred: {e_global}", style="error")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
```
