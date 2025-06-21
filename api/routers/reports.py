import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from datetime import date
import tempfile # For creating temporary files for CSV export

from ..dependencies import get_db, get_current_user_placeholder
from ..models import HttpError # Assuming HttpError is a generic error model

# Assuming core modules are importable (PYTHONPATH includes project root)
from reporting import reports as reporting_service # Alias to avoid conflict with router name
from reporting.reports import ReportingError
from core.account_management import AccountNotFoundError # If specific account is not found for filtering

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    responses={
        500: {"description": "Internal server error", "model": HttpError}
    },
)

# Placeholder for current user
CurrentUser = Depends(get_current_user_placeholder)

@router.get("/transactions/csv",
            summary="Export transactions to CSV file",
            response_description="A CSV file containing transaction records.",
            responses={
                200: {
                    "content": {"text/csv": {}},
                    "description": "CSV file with transactions.",
                },
                400: {"description": "Invalid date format or parameters", "model": HttpError},
                403: {"description": "Not authorized", "model": HttpError},
                404: {"description": "Account not found if account_id is specified and invalid", "model": HttpError},
            })
async def export_transactions_csv(
    start_date: date = Query(..., description="Start date for the report (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the report (YYYY-MM-DD)"),
    account_id: Optional[int] = Query(None, description="Optional account ID to filter transactions"),
    db_conn = Depends(get_db), # reporting_service.export_transactions_to_csv manages its own connection
    # current_user: dict = CurrentUser # TODO: Auth (e.g., admins, auditors, or customer for own account)
):
    """
    Export transaction records to a CSV file within a specified date range.
    Optionally, filter by a specific `account_id`.

    - **start_date**: The beginning of the date range for transactions.
    - **end_date**: The end of the date range for transactions.
    - **account_id** (optional): Filter transactions for this specific account.
    """
    # TODO: Authorization checks.
    # E.g., if account_id is provided, is the current_user allowed to see this account's transactions?
    # If no account_id, is current_user an admin/auditor?

    temp_file_path = None
    try:
        # Create a temporary file to store the CSV
        # tempfile.NamedTemporaryFile creates a file that is deleted once closed.
        # We need to ensure it stays for FileResponse, so manage deletion manually or use a specific directory.
        # For simplicity, let's create a named temporary file and FileResponse will handle it.
        # Suffix is important for FastAPI/browsers to suggest a filename.
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv", prefix="transactions_") as tmpfile:
            temp_file_path = tmpfile.name

        # The core service function writes to this path.
        reporting_service.export_transactions_to_csv(
            start_date_str=start_date.isoformat(),
            end_date_str=end_date.isoformat(),
            output_filepath=temp_file_path,
            account_id=account_id
        )

        # Generate a filename for the download
        filename_parts = ["transactions"]
        if account_id:
            filename_parts.append(f"acc_{account_id}")
        filename_parts.append(f"{start_date.isoformat()}_to_{end_date.isoformat()}.csv")
        download_filename = "_".join(filename_parts)

        return FileResponse(
            path=temp_file_path,
            media_type="text/csv",
            filename=download_filename,
            # After FileResponse sends the file, we might want to delete it.
            # However, FileResponse handles closing the file. If delete=False was used with NamedTemporaryFile,
            # we need a background task or a more robust cleanup for temp files.
            # For now, relying on OS to clean up /tmp or manual cleanup if issues.
            # A better approach for production: BackgroundTasks to delete the file after response.
            # from fastapi import BackgroundTasks
            # background_tasks.add_task(os.remove, temp_file_path)
        )

    except ValueError as ve: # Date format issues from core service (should be caught by FastAPI Query for `date` type)
        if temp_file_path and os.path.exists(temp_file_path): os.remove(temp_file_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except AccountNotFoundError as anf: # If account_id is provided and not found by export_transactions_to_csv
        if temp_file_path and os.path.exists(temp_file_path): os.remove(temp_file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(anf))
    except ReportingError as re:
        if temp_file_path and os.path.exists(temp_file_path): os.remove(temp_file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Reporting error: {re}")
    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path): os.remove(temp_file_path)
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during CSV export: {e}")

```
