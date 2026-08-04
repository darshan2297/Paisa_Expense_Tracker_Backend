"""Local filesystem helpers for receipt slips and similar uploads."""

from pathlib import Path

from app.core.config import get_settings

ALLOWED_RECEIPT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_RECEIPT_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}
MAX_RECEIPT_BYTES = 10 * 1024 * 1024  # 10 MB


def storage_root() -> Path:
    root = Path(get_settings().STORAGE_DIR)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def receipt_dir(user_id: str) -> Path:
    path = storage_root() / "receipts" / user_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_stored_path(relative_path: str) -> Path:
    """Resolve a stored relative path and ensure it stays under STORAGE_DIR."""
    root = storage_root().resolve()
    full = (root / relative_path).resolve()
    if not str(full).startswith(str(root)):
        raise ValueError("Invalid storage path")
    return full


def extension_for(content_type: str | None, filename: str | None) -> str:
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in ALLOWED_RECEIPT_EXTENSIONS:
            return suffix
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }
    if content_type and content_type in mapping:
        return mapping[content_type]
    return ".jpg"
