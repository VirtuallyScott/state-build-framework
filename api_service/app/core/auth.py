"""
Authentication and authorization for the Build State API.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from .config import settings
from .database import db


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security_bearer = HTTPBearer(auto_error=False)
security_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with username and password."""
    query = """
    SELECT id, username, email, full_name, password_hash, is_active, created_at, updated_at
    FROM users
    WHERE username = %s AND deleted_at IS NULL
    """ if db.db_type == "postgresql" else """
    SELECT id, username, email, full_name, password_hash, is_active, created_at, updated_at
    FROM users
    WHERE username = ? AND deleted_at IS NULL
    """

    users = db.execute_query(query, (username,))
    if not users:
        return None

    user = users[0]
    if not verify_password(password, user["password_hash"]):
        return None

    return user


def get_current_user(token: Optional[str] = Depends(security_bearer)) -> Dict[str, Any]:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    if isinstance(token, HTTPAuthorizationCredentials):
        token = token.credentials

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    query = """
    SELECT id, username, email, full_name, is_active, created_at, updated_at
    FROM users
    WHERE id = %s AND deleted_at IS NULL
    """ if db.db_type == "postgresql" else """
    SELECT id, username, email, full_name, is_active, created_at, updated_at
    FROM users
    WHERE id = ? AND deleted_at IS NULL
    """

    users = db.execute_query(query, (user_id,))
    if not users:
        raise credentials_exception

    user = users[0]
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


def get_current_user_optional(token: Optional[str] = Depends(security_bearer)) -> Optional[Dict[str, Any]]:
    """Get the current user if authenticated, otherwise None."""
    try:
        return get_current_user(token)
    except HTTPException:
        return None


def verify_api_key(api_key: Optional[str] = Depends(security_api_key)) -> Optional[Dict[str, Any]]:
    """Verify API key and return associated user."""
    if not api_key:
        return None

    if api_key not in settings.api_keys:
        # Check if it's a user token
        query = """
        SELECT t.id as token_id, t.user_id, t.description, t.created_at, t.last_used,
               u.username, u.email, u.full_name, u.is_active
        FROM api_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = %s AND t.deleted_at IS NULL AND u.deleted_at IS NULL
        """ if db.db_type == "postgresql" else """
        SELECT t.id as token_id, t.user_id, t.description, t.created_at, t.last_used,
               u.username, u.email, u.full_name, u.is_active
        FROM api_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ? AND t.deleted_at IS NULL AND u.deleted_at IS NULL
        """

        tokens = db.execute_query(query, (api_key,))
        if not tokens:
            return None

        token_data = tokens[0]
        if not token_data["is_active"]:
            return None

        # Update last_used timestamp
        update_query = """
        UPDATE api_tokens SET last_used = %s WHERE id = %s
        """ if db.db_type == "postgresql" else """
        UPDATE api_tokens SET last_used = ? WHERE id = ?
        """
        db.execute_query(update_query, (datetime.utcnow(), token_data["token_id"]), fetch=False)

        return {
            "id": token_data["user_id"],
            "username": token_data["username"],
            "email": token_data["email"],
            "full_name": token_data["full_name"],
            "is_active": token_data["is_active"],
            "token_id": token_data["token_id"]
        }

    # It's a global API key
    return {"api_key": api_key, "type": "global"}


def get_current_user_or_api_key(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    api_user: Optional[Dict[str, Any]] = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get current user from either JWT token or API key."""
    if user:
        return user
    if api_user:
        return api_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )