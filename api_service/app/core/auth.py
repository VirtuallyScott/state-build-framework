"""
Authentication and authorization for the Build State API.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_db
from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


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


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate a user with username and password."""
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> models.User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Get the current active user. Inactive users are not permitted.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[models.User]:
    """Get the current user if authenticated, otherwise None."""
    if not token:
        return None
    try:
        return get_current_user(db, token)
    except HTTPException:
        return None


def verify_api_key(
    api_key: Optional[str] = Depends(api_key_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Verify API key and return associated user, or None if no key provided."""
    # If no API key provided, return None (not an error - might be using JWT instead)
    if not api_key:
        return None
    
    # Find active API tokens and check against the provided key
    api_tokens = db.query(models.APIToken).filter(models.APIToken.is_active == True).all()

    matched_user = None
    for token in api_tokens:
        if verify_password(api_key, token.token_hash):
            # Found a match, now get the user
            user = db.query(models.User).filter(
                models.User.id == token.user_id,
                models.User.is_active == True
            ).first()
            if user:
                matched_user = user
                break # Found a valid user, stop checking

    if not matched_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return matched_user


def verify_api_key_optional(
    api_key: Optional[str] = Depends(api_key_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Verify API key and return associated user, or None if no key provided or invalid."""
    try:
        return verify_api_key(api_key, db)
    except HTTPException:
        return None


def get_current_user_or_api_key(
    user: Optional[models.User] = Depends(get_current_user_optional),
    api_user: Optional[models.User] = Depends(verify_api_key_optional)
) -> models.User:
    """
    Get current user from either JWT token or API key.
    This dependency will try JWT first, then fall back to API Key.
    One of them must succeed.
    """
    # This dependency is tricky because Depends executes all sub-dependencies.
    # We need a way to make them optional and check which one succeeded.
    # A cleaner way might be a custom dependency class, but this works.
    if user:
        return user
    if api_user:
        return api_user

    # If neither worked, we re-raise the auth error.
    # We can't know which one the user *intended* to use, so we send a generic
    # 401, but include both auth methods in the header.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Use Bearer token or X-API-Key.",
        headers={"WWW-Authenticate": "Bearer, X-API-Key"},
    )


def create_api_token(db: Session, user_id: uuid.UUID, token_data: models.APITokenCreate) -> models.APIToken:
    """
    Create a new API token for a user.
    """
    token_str = secrets.token_urlsafe(32)
    hashed_token = get_password_hash(token_str)

    db_token = models.APIToken(
        user_id=user_id,
        token=hashed_token,
        name=token_data.name,
        description=token_data.description,
        scopes=token_data.scopes,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    # Return the full token string only once upon creation
    # We need to set it on the response model, not the DB model
    response_token = models.APITokenResponse.from_orm(db_token)
    response_token.token = token_str
    return response_token


def get_user_scopes(user: models.User, db: Session) -> list:
    """Get the scopes/permissions for a user. Returns scopes from their active API token."""
    # Check if this user came from an API token (look for active tokens)
    token = db.query(models.APIToken).filter(
        models.APIToken.user_id == user.id,
        models.APIToken.is_active == True
    ).first()
    
    if token and token.scopes:
        return token.scopes
    
    # Default scopes for JWT-authenticated users
    if user.is_superuser:
        return ['read', 'write', 'admin']
    return ['read', 'write']


def require_scope(required_scope: str):
    """Dependency factory to require a specific scope."""
    def scope_checker(
        current_user: models.User = Depends(get_current_user_or_api_key),
        db: Session = Depends(get_db)
    ):
        scopes = get_user_scopes(current_user, db)
        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}",
            )
        return current_user
    return scope_checker


# Convenience dependencies for common permission checks
def require_read(
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Require read permission."""
    scopes = get_user_scopes(current_user, db)
    if 'read' not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required",
        )
    return current_user


def require_write(
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Require write permission."""
    scopes = get_user_scopes(current_user, db)
    if 'write' not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required",
        )
    return current_user


def require_admin(
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Require admin permission."""
    scopes = get_user_scopes(current_user, db)
    if 'admin' not in scopes and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return current_user