import os
import time
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Resolved path to the uploads directory (project_root/uploads/)
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def load_doc_text(doc_filename: str) -> str:
    """
    Read extracted document text from the uploads directory.

    Validates the filename to prevent directory-traversal attacks,
    then returns the file contents as a string.
    """
    # Block path traversal
    if ".." in doc_filename or "/" in doc_filename or "\\" in doc_filename:
        raise HTTPException(status_code=400, detail="Invalid doc_filename")

    filepath = os.path.join(UPLOADS_DIR, doc_filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=404, detail="Document not found. Please upload a file first."
        )

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def cleanup_expired_uploads() -> None:
    """
    Delete files in the uploads directory that are older than the
    configured TTL (UPLOAD_TTL_SECONDS env var, default 3600s).
    """
    ttl = int(os.environ.get("UPLOAD_TTL_SECONDS", "3600"))
    now = time.time()
    removed = 0

    for filename in os.listdir(UPLOADS_DIR):
        filepath = os.path.join(UPLOADS_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        age = now - os.path.getmtime(filepath)
        if age > ttl:
            try:
                os.remove(filepath)
                removed += 1
            except OSError as e:
                logger.warning(f"Failed to remove expired upload {filename}: {e}")

    if removed:
        logger.info(f"Cleaned up {removed} expired upload(s)")
