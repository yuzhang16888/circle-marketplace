# core/storage.py
import os
import time
from .config import UPLOAD_DIR
from typing import Optional


def _ensure_upload_dir(subdir: Optional[str] | None = None) -> str:
    base = UPLOAD_DIR
    if subdir:
        base = os.path.join(base, subdir)
    os.makedirs(base, exist_ok=True)
    return base


def save_listing_image(user_id: int, file) -> str:
    folder = _ensure_upload_dir("listings")
    _, ext = os.path.splitext(file.name)
    ext = ext.lower() or ".jpg"
    filename = f"listing_{user_id}_{int(time.time())}{ext}"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path


def save_profile_image(user_id: int, file) -> str:
    folder = _ensure_upload_dir("profiles")
    _, ext = os.path.splitext(file.name)
    ext = ext.lower() or ".jpg"
    filename = f"profile_{user_id}_{int(time.time())}{ext}"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return path
