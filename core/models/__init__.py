# core/__init__.py
"""
Core package for Circle.

Intentionally kept minimal – we no longer auto-import ORM models here
to avoid pulling in unused SQLAlchemy dependencies.
"""

# If you need explicit re-exports later (e.g. helper modules),
# you can add them here, but avoid importing `core.models`.
