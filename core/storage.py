# core/storage.py
import os
import time
from .config import UPLOAD_DIR

def save_listing_image(user_id, file):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    _, ext = os.path.splitext(file.name)
    filename = f"listing_{user_id}_{int(time.time())}{ext.lower()}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(file.getbuffer())

    return path
