# core/config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Use a fresh DB file name to avoid old schema issues
DB_PATH = os.path.join(BASE_DIR, "circle_v2.db")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
