# core/config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "circle_dev.db")  # <- any name, just keep it here
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
