import os
import shutil
import stat
from pathlib import Path
from typing import List, Dict, Union, Optional
import re

# Basic patterns for identifying sensitive keys for masking
SENSITIVE_KEY_PATTERNS = [
    "SECRET", "PASSWORD", "TOKEN", "API_KEY", "PRIVATE_KEY", "CONNECTION_STRING"
]

def _is_sensitive_key(key: str) -> bool:
    """Checks if a key name suggests sensitivity."""
    key_upper = key.upper()
    return any(pattern in key_upper for pattern in SENSITIVE_KEY_PATTERNS)

def read_env_file_structured(file_path: Path) -> List[Dict[str, Union[str, None]]]:
    """
    Reads an .env file line by line and preserves structure including comments and empty lines.
    Returns a list of dictionaries, where each dictionary represents a line.
    Types of lines: 'comment', 'empty', 'pair'.
    """
    structured_data: List[Dict[str, Union[str, None]]] = []
    if not file_path.exists():
        # If the file doesn't exist, return an empty structure.
        # It will be created on the first 'set' operation.
        return structured_data

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line_content in enumerate(f, 1):
                line = line_content.strip()
                if not line:
                    structured_data.append({'type': 'empty', 'content': '', 'line_num': line_num})
                elif line.startswith('#'):
                    structured_data.append({'type': 'comment', 'content': line_content.rstrip('\n\r'), 'line_num': line_num})
                elif '=' in line:
                    key, *value_parts = line.split('=', 1)
                    key = key.strip()
                    value = value_parts[0].strip() if value_parts else ''
                    structured_data.append({'type': 'pair', 'key': key, 'value': value, 'original_line': line_content.rstrip('\n\r'), 'line_num': line_num})
                else:
                    # Treat non-empty, non-comment, non-pair lines as 'unknown' or log a warning.
                    # For now, preserve them as 'unknown' type to avoid data loss.
                    structured_data.append({'type': 'unknown', 'content': line_content.rstrip('\n\r'), 'line_num': line_num})
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")
    return structured_data

def write_env_file_structured(file_path: Path, structured_data: List[Dict[str, Union[str, None]]], original_permissions: Optional[int] = None) -> None:
    """
    Writes structured data back to an .env file, preserving comments and empty lines.
    Uses atomic write (write to temp, backup original, then replace).
    Restores original file permissions if provided.
    """
    temp_file_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
    backup_file_path = file_path.with_suffix(f"{file_path.suffix}.bak")

    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            for item in structured_data:
                if item['type'] == 'pair':
                    # Ensure key is not None before using it
                    key = item.get('key')
                    if key is None: # Should not happen if data structure is correct
                        f.write(f"{item.get('original_line', '')}\n") # Write original if key is missing
                        continue

                    value = item.get('value', '') # Default to empty string if value is None
                    # format_value_for_env should handle quoting
                    formatted_value = format_value_for_env(str(value))
                    f.write(f"{key}={formatted_value}\n")
                elif item['type'] == 'comment' or item['type'] == 'empty' or item['type'] == 'unknown':
                    f.write(f"{item.get('content', '')}\n")
                # Other types could be handled or logged if necessary

        if file_path.exists():
            shutil.copy2(file_path, backup_file_path) # copy2 preserves metadata like permissions
            file_path.unlink() # Remove original before renaming temp

        shutil.move(str(temp_file_path), str(file_path))

        if original_permissions is not None:
            os.chmod(file_path, original_permissions)
        elif backup_file_path.exists() and not file_path.exists(): # If only .bak exists, try to use its permissions
             # This case might be tricky if original_permissions was not captured before deletion.
             # Relying on copy2 for the .bak file is better.
             pass


    except IOError as e:
        # Attempt to restore from backup if temp file failed before move
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError:
                pass # Ignore if deletion of temp file fails
        # If original was backed up but rename failed, try to restore .bak
        if backup_file_path.exists() and not file_path.exists():
            try:
                shutil.move(str(backup_file_path), str(file_path))
            except IOError:
                 raise IOError(f"Error writing to {file_path} and failed to restore backup {backup_file_path}. Manual recovery needed. Error: {e}")
        raise IOError(f"Error writing to file {file_path}: {e}")
    finally:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError:
                pass # Best effort to clean up temp file

def format_value_for_env(value: str) -> str:
    """
    Quotes the value if it contains spaces, '#', '=', or is empty,
    or if it's already quoted.
    Handles existing quotes to avoid double-quoting.
    """
    if not value:  # Empty string
        return '""'

    # Check if already properly quoted
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value

    # Characters that necessitate quoting
    if ' ' in value or '#' in value or '=' in value or '"' in value or "'" in value:
        # If it contains double quotes, use single quotes, and vice versa.
        # If it contains both, escape double quotes and use double quotes. This is simpler.
        escaped_value = value.replace('"', '\\"')
        return f'"{escaped_value}"'

    return value


def parse_env_value(value_str: Optional[str]) -> str:
    """
    Removes surrounding quotes from a value if present.
    Handles both single and double quotes.
    """
    if value_str is None:
        return ""

    value = value_str.strip()
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

```
