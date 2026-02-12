"""
Common dependencies for the Build State API.
"""
from typing import Dict, Any
from fastapi import Depends

from .core.auth import get_current_user_or_api_key
from .core.database import db


def get_db():
    """Database dependency."""
    return db


def get_current_user_or_key() -> Dict[str, Any]:
    """Current user or API key dependency."""
    return get_current_user_or_api_key