"""
Common dependencies for the Build State API.
"""
from typing import Dict, Any
from fastapi import Depends

from .core.database import db
# from .core.auth import get_current_user_or_api_key


def get_db():
    """Database dependency that yields a session."""
    db_session = db.get_session()
    try:
        yield db_session
    finally:
        db_session.close()


def get_current_user_or_key() -> Dict[str, Any]:
    """Current user or API key dependency."""
    from .core.auth import get_current_user_or_api_key
    return get_current_user_or_api_key