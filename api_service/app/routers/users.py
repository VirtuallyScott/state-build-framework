"""
User management endpoints for the Build State API.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from ..models import UserCreate, UserUpdate, UserResponse, UserProfileResponse, APITokenCreate, APITokenResponse
from ..core.auth import get_current_user, get_password_hash
from ..core.database import db
from ..dependencies import get_db

router = APIRouter()


@router.post("/users", response_model=dict)
async def create_user(user: UserCreate, db_conn=Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    query = """
    SELECT id FROM users WHERE username = %s AND deleted_at IS NULL
    """ if db_conn.db_type == "postgresql" else """
    SELECT id FROM users WHERE username = ? AND deleted_at IS NULL
    """

    existing = db_conn.execute_query(query, (user.username,))
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create user
    hashed_password = get_password_hash(user.password)
    insert_query = """
    INSERT INTO users (username, email, full_name, password_hash, is_active, created_at, updated_at)
    VALUES (%s, %s, %s, %s, true, %s, %s)
    RETURNING id
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO users (username, email, full_name, password_hash, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, 1, ?, ?)
    """

    now = datetime.utcnow()
    params = (user.username, user.email, user.full_name, hashed_password, now, now)

    if db_conn.db_type == "postgresql":
        result = db_conn.execute_query(insert_query, params)
        user_id = result[0]["id"]
    else:
        db_conn.execute_query(insert_query, params, fetch=False)
        # Get the last inserted id for SQLite
        result = db_conn.execute_query("SELECT last_insert_rowid() as id")
        user_id = result[0]["id"]

    return {"id": user_id, "username": user.username, "email": user.email}


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user), db_conn=Depends(get_db)):
    """Get user by ID."""
    # Users can only see their own profile unless they're admin
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to view this user")

    query = """
    SELECT id, username, email, full_name, is_active, created_at, updated_at
    FROM users
    WHERE id = %s AND deleted_at IS NULL
    """ if db_conn.db_type == "postgresql" else """
    SELECT id, username, email, full_name, is_active, created_at, updated_at
    FROM users
    WHERE id = ? AND deleted_at IS NULL
    """

    users = db_conn.execute_query(query, (user_id,))
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user = users[0]
    return UserResponse(**user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db_conn=Depends(get_db)
):
    """Update user information."""
    # Users can only update their own profile unless they're admin
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    # Build update query dynamically
    update_fields = []
    params = []

    if user_update.email is not None:
        update_fields.append("email = %s" if db_conn.db_type == "postgresql" else "email = ?")
        params.append(user_update.email)

    if user_update.full_name is not None:
        update_fields.append("full_name = %s" if db_conn.db_type == "postgresql" else "full_name = ?")
        params.append(user_update.full_name)

    if user_update.is_active is not None:
        update_fields.append("is_active = %s" if db_conn.db_type == "postgresql" else "is_active = ?")
        params.append(user_update.is_active)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields.append("updated_at = %s" if db_conn.db_type == "postgresql" else "updated_at = ?")
    params.append(datetime.utcnow())

    params.append(user_id)

    update_query = f"""
    UPDATE users
    SET {', '.join(update_fields)}
    WHERE id = {'%s' if db_conn.db_type == 'postgresql' else '?'} AND deleted_at IS NULL
    """

    db_conn.execute_query(update_query, tuple(params), fetch=False)

    # Return updated user
    return await get_user(user_id, current_user, db_conn)


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, current_user: dict = Depends(get_current_user), db_conn=Depends(get_db)):
    """Get user profile with additional information."""
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")

    query = """
    SELECT u.id, u.username, u.email, u.full_name, u.is_active, u.created_at,
           MAX(s.created_at) as last_login
    FROM users u
    LEFT JOIN user_sessions s ON u.id = s.user_id
    WHERE u.id = %s AND u.deleted_at IS NULL
    GROUP BY u.id, u.username, u.email, u.full_name, u.is_active, u.created_at
    """ if db_conn.db_type == "postgresql" else """
    SELECT u.id, u.username, u.email, u.full_name, u.is_active, u.created_at,
           MAX(s.created_at) as last_login
    FROM users u
    LEFT JOIN user_sessions s ON u.id = s.user_id
    WHERE u.id = ? AND u.deleted_at IS NULL
    GROUP BY u.id
    """

    users = db_conn.execute_query(query, (user_id,))
    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    user = users[0]
    return UserProfileResponse(**user)


@router.post("/users/{user_id}/tokens", response_model=dict)
async def create_api_token(
    user_id: int,
    token_data: APITokenCreate,
    current_user: dict = Depends(get_current_user),
    db_conn=Depends(get_db)
):
    """Create a new API token for a user."""
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to create tokens for this user")

    import secrets
    token = secrets.token_urlsafe(32)

    insert_query = """
    INSERT INTO api_tokens (user_id, token, description, created_at)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO api_tokens (user_id, token, description, created_at)
    VALUES (?, ?, ?, ?)
    """

    now = datetime.utcnow()
    params = (user_id, token, token_data.description, now)

    if db_conn.db_type == "postgresql":
        result = db_conn.execute_query(insert_query, params)
        token_id = result[0]["id"]
    else:
        db_conn.execute_query(insert_query, params, fetch=False)
        result = db_conn.execute_query("SELECT last_insert_rowid() as id")
        token_id = result[0]["id"]

    return {
        "id": token_id,
        "token": token,
        "description": token_data.description,
        "created_at": now
    }


@router.get("/users/{user_id}/tokens", response_model=List[APITokenResponse])
async def list_api_tokens(user_id: int, current_user: dict = Depends(get_current_user), db_conn=Depends(get_db)):
    """List API tokens for a user."""
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to view tokens for this user")

    query = """
    SELECT id, user_id, token, description, created_at, last_used
    FROM api_tokens
    WHERE user_id = %s AND deleted_at IS NULL
    ORDER BY created_at DESC
    """ if db_conn.db_type == "postgresql" else """
    SELECT id, user_id, token, description, created_at, last_used
    FROM api_tokens
    WHERE user_id = ? AND deleted_at IS NULL
    ORDER BY created_at DESC
    """

    tokens = db_conn.execute_query(query, (user_id,))
    return [APITokenResponse(**token) for token in tokens]


@router.delete("/users/{user_id}/tokens/{token_id}")
async def delete_api_token(
    user_id: int,
    token_id: int,
    current_user: dict = Depends(get_current_user),
    db_conn=Depends(get_db)
):
    """Delete an API token."""
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to delete tokens for this user")

    # Soft delete the token
    update_query = """
    UPDATE api_tokens SET deleted_at = %s WHERE id = %s AND user_id = %s
    """ if db_conn.db_type == "postgresql" else """
    UPDATE api_tokens SET deleted_at = ? WHERE id = ? AND user_id = ?
    """

    db_conn.execute_query(update_query, (datetime.utcnow(), token_id, user_id), fetch=False)

    return {"message": "Token deleted successfully"}