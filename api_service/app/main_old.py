"""
Build State API Service
A FastAPI service for managing multi-cloud IaaS image build states.

Features:
- JWT and API key authentication
- SQLite/PostgreSQL support
- RESTful API for build state management
- Health checks and metrics
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import secrets
import sqlite3
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import jwt
from passlib.context import CryptContext
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "builds.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

API_KEYS = os.getenv("API_KEYS", "dev-key-12345").split(",")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security_bearer = HTTPBearer(auto_error=False)
security_api_key = APIKeyHeader(name="X-API-Key", auto_error=False)

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., description="Unique username")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    password: str = Field(..., description="User password")
    is_superuser: bool = False

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    employee_id: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    first_name: str
    last_name: str
    employee_id: str
    email: str
    start_date: str
    end_date: Optional[str]
    created_at: str

class APITokenCreate(BaseModel):
    name: str = Field(..., description="Token name")
    scopes: List[str] = Field(default_factory=list, description="Permission scopes")
    expires_at: Optional[datetime] = None

class APITokenResponse(BaseModel):
    id: str
    user_id: str
    name: str
    scopes: List[str]
    expires_at: Optional[str]
    is_active: bool
    created_at: str

class IDMLoginRequest(BaseModel):
    username: str
    idm_token: str  # IDM authentication token

class BuildCreate(BaseModel):
    platform: str = Field(..., description="Platform identifier (e.g., 'aws-commercial', 'azure')")
    os_version: str = Field(..., description="OS version identifier (e.g., 'rhel-8.8')")
    image_type: str = Field(..., description="Image type identifier (e.g., 'base', 'hana')")
    build_id: str = Field(..., description="Unique build identifier")
    pipeline_url: Optional[str] = None
    commit_hash: Optional[str] = None

class StateTransition(BaseModel):
    state_code: int = Field(..., ge=0, le=100, description="State code (0-100, increments of 5)")
    message: Optional[str] = None

class FailureRecord(BaseModel):
    error_message: str
    error_code: Optional[str] = None
    component: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class TokenRequest(BaseModel):
    username: str
    password: str

class BuildResponse(BaseModel):
    id: str
    platform: str
    os_version: str
    image_type: str
    build_id: str
    pipeline_url: Optional[str]
    commit_hash: Optional[str]
    current_state: Optional[int]
    created_at: str
    updated_at: str

class StateResponse(BaseModel):
    build_id: str
    current_state: int
    message: Optional[str]
    transitioned_at: str

# Database setup
def get_placeholder():
    """Get the correct SQL placeholder for the database type"""
    return "%s" if is_postgresql() else "?"

def get_db_connection():
    """Get database connection with appropriate driver"""
    if DATABASE_URL.startswith("postgresql://"):
        # PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        # SQLite connection (default)
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn

def is_postgresql():
    """Check if using PostgreSQL"""
    return DATABASE_URL.startswith("postgresql://")

def get_redis_client():
    """Get Redis client connection"""
    if not CACHE_ENABLED:
        return None
    try:
        return redis.from_url(REDIS_URL)
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return None

def cache_get(key: str) -> Optional[str]:
    """Get value from Redis cache"""
    client = get_redis_client()
    if client:
        try:
            return client.get(key)
        except Exception:
            pass
    return None

def cache_set(key: str, value: str, ttl: int = CACHE_TTL):
    """Set value in Redis cache with TTL"""
    client = get_redis_client()
    if client:
        try:
            client.setex(key, ttl, value)
        except Exception:
            pass

def cache_delete(key: str):
    """Delete key from Redis cache"""
    client = get_redis_client()
    if client:
        try:
            client.delete(key)
        except Exception:
            pass

# User management functions
def create_user(user: UserCreate) -> str:
    """Create a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    user_uuid = secrets.token_urlsafe(16)
    hashed_password = pwd_context.hash(user.password)

    cursor.execute("""
        INSERT INTO users (id, username, email, first_name, last_name, employee_id, hashed_password, is_superuser)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_uuid,
        user.username,
        user.email,
        user.first_name,
        user.last_name,
        user.employee_id,
        hashed_password,
        user.is_superuser
    ))

    # Create user profile
    profile_uuid = secrets.token_urlsafe(16)
    cursor.execute("""
        INSERT INTO user_profiles (id, user_id, first_name, last_name, employee_id, email, start_date)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
    """, (
        profile_uuid,
        user_uuid,
        user.first_name or "",
        user.last_name or "",
        user.employee_id or "",
        user.email
    ))

    conn.commit()
    conn.close()

    return user_uuid

def get_user(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, email, first_name, last_name, employee_id, is_active, is_superuser, created_at, updated_at
        FROM users
        WHERE id = %s AND deactivated_at IS NULL
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, email, first_name, last_name, employee_id, hashed_password, is_active, is_superuser, created_at, updated_at
        FROM users
        WHERE username = %s AND deactivated_at IS NULL
    """, (username,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def update_user(user_id: str, updates: UserUpdate):
    """Update user (soft delete by setting deactivated_at)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = %s AND deactivated_at IS NULL", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    update_fields = []
    update_values = []

    if updates.email is not None:
        update_fields.append("email = %s")
        update_values.append(updates.email)
    if updates.first_name is not None:
        update_fields.append("first_name = %s")
        update_values.append(updates.first_name)
    if updates.last_name is not None:
        update_fields.append("last_name = %s")
        update_values.append(updates.last_name)
    if updates.employee_id is not None:
        update_fields.append("employee_id = %s")
        update_values.append(updates.employee_id)
    if updates.is_active is not None:
        if not updates.is_active:
            # Deactivate user and set end_date in profile
            update_fields.append("is_active = %s")
            update_fields.append("deactivated_at = CURRENT_TIMESTAMP")
            update_values.append(updates.is_active)
            update_values.append(None)  # deactivated_at will be set by CURRENT_TIMESTAMP

            # Update user profile with end_date
            cursor.execute("""
                UPDATE user_profiles SET end_date = CURRENT_DATE
                WHERE user_id = %s AND end_date IS NULL
            """, (user_id,))
        else:
            update_fields.append("is_active = %s")
            update_values.append(updates.is_active)
    if updates.is_superuser is not None:
        update_fields.append("is_superuser = %s")
        update_values.append(updates.is_superuser)

    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(user_id)

        cursor.execute(query, update_values)

    conn.commit()
    conn.close()

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, first_name, last_name, employee_id, email, start_date, end_date, created_at
        FROM user_profiles
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

# API Token management functions
def create_api_token(user_id: str, token_data: APITokenCreate) -> str:
    """Create a new API token"""
    conn = get_db_connection()
    cursor = conn.cursor()

    token_uuid = secrets.token_urlsafe(16)
    token_value = secrets.token_urlsafe(32)
    token_hash = pwd_context.hash(token_value)

    scopes_str = json.dumps(token_data.scopes) if is_postgresql() else str(token_data.scopes)

    cursor.execute("""
        INSERT INTO api_tokens (id, user_id, name, token_hash, scopes, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        token_uuid,
        user_id,
        token_data.name,
        token_hash,
        scopes_str,
        token_data.expires_at
    ))

    conn.commit()
    conn.close()

    return token_value  # Return the actual token value, not the hash

def get_api_tokens(user_id: str) -> List[Dict]:
    """Get API tokens for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, name, scopes, expires_at, is_active, created_at
        FROM api_tokens
        WHERE user_id = %s AND deactivated_at IS NULL
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    tokens = []
    for row in rows:
        token = dict(row)
        if not is_postgresql():
            # Parse scopes from string in SQLite
            try:
                token['scopes'] = eval(token['scopes']) if token['scopes'] else []
            except:
                token['scopes'] = []
        tokens.append(token)

    return tokens

def deactivate_api_token(token_id: str, user_id: str):
    """Deactivate an API token (soft delete)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE api_tokens SET is_active = false, deactivated_at = CURRENT_TIMESTAMP
        WHERE id = %s AND user_id = %s AND deactivated_at IS NULL
    """, (token_id, user_id))

    conn.commit()
    conn.close()

def verify_api_token(token: str) -> Optional[Dict]:
    """Verify API token and return user info"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, token_hash, scopes, expires_at, is_active FROM api_tokens WHERE deactivated_at IS NULL")
    for row in cursor.fetchall():
        try:
            if pwd_context.verify(token, row['token_hash']):
                if not row['is_active']:
                    continue
                if row['expires_at'] and datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')) < datetime.utcnow():
                    continue

                user = get_user(row['user_id'])
                if user and user['is_active']:
                    scopes = row['scopes']
                    if not is_postgresql():
                        try:
                            scopes = eval(scopes) if scopes else []
                        except:
                            scopes = []
                    return {
                        'user_id': row['user_id'],
                        'username': user['username'],
                        'scopes': scopes,
                        'type': 'api_token'
                    }
        except:
            continue

    conn.close()
    return None

# IDM Authentication functions
def authenticate_with_idm(username: str, idm_token: str) -> Optional[Dict]:
    """Authenticate user with IDM token"""
    # This is a placeholder for IDM integration
    # In a real implementation, you would validate the IDM token with the IDM service
    # For now, we'll simulate IDM authentication

    # Check if user exists
    user = get_user_by_username(username)
    if not user or not user['is_active']:
        return None

    # Simulate IDM token validation
    # In production, this would call the IDM service
    if idm_token.startswith("idm-") and len(idm_token) > 10:
        return {
            'user_id': user['id'],
            'username': user['username'],
            'is_superuser': user['is_superuser'],
            'type': 'idm'
        }

    return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_postgresql():
        # PostgreSQL table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                first_name TEXT,
                last_name TEXT,
                employee_id TEXT,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                is_superuser BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                email TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                scopes TEXT[],
                expires_at TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cloud_provider TEXT NOT NULL,
                region TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS os_versions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_types (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id TEXT PRIMARY KEY,
                platform_id TEXT NOT NULL,
                os_version_id TEXT NOT NULL,
                image_type_id TEXT NOT NULL,
                build_id TEXT NOT NULL UNIQUE,
                pipeline_url TEXT,
                commit_hash TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY (platform_id) REFERENCES platforms (id),
                FOREIGN KEY (os_version_id) REFERENCES os_versions (id),
                FOREIGN KEY (image_type_id) REFERENCES image_types (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_states (
                id SERIAL PRIMARY KEY,
                build_id TEXT NOT NULL,
                state_code INTEGER NOT NULL,
                message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY (build_id) REFERENCES builds (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_failures (
                id SERIAL PRIMARY KEY,
                build_id TEXT NOT NULL,
                error_message TEXT NOT NULL,
                error_code TEXT,
                component TEXT,
                details TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE,
                FOREIGN KEY (build_id) REFERENCES builds (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE,
                active BOOLEAN DEFAULT true,
                deactivated_at TIMESTAMP WITH TIME ZONE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_employee_id ON user_profiles(employee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_tokens_active ON api_tokens(is_active) WHERE is_active = true")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_builds_build_id ON builds(build_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_states_build_id ON build_states(build_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_failures_build_id ON build_failures(build_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(active) WHERE active = true")

    else:
        # SQLite table creation
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                first_name TEXT,
                last_name TEXT,
                employee_id TEXT,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                email TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS api_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                scopes TEXT,
                expires_at TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS platforms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cloud_provider TEXT NOT NULL,
                region TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS os_versions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS image_types (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS builds (
                id TEXT PRIMARY KEY,
                platform_id TEXT NOT NULL,
                os_version_id TEXT NOT NULL,
                image_type_id TEXT NOT NULL,
                build_id TEXT NOT NULL UNIQUE,
                pipeline_url TEXT,
                commit_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT,
                FOREIGN KEY (platform_id) REFERENCES platforms (id),
                FOREIGN KEY (os_version_id) REFERENCES os_versions (id),
                FOREIGN KEY (image_type_id) REFERENCES image_types (id)
            );

            CREATE TABLE IF NOT EXISTS build_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                state_code INTEGER NOT NULL,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT,
                FOREIGN KEY (build_id) REFERENCES builds (id)
            );

            CREATE TABLE IF NOT EXISTS build_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                error_message TEXT NOT NULL,
                error_code TEXT,
                component TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT,
                FOREIGN KEY (build_id) REFERENCES builds (id)
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                active BOOLEAN DEFAULT 1,
                deactivated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active = 1);
            CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_profiles_employee_id ON user_profiles(employee_id);
            CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_api_tokens_active ON api_tokens(is_active = 1);
            CREATE INDEX IF NOT EXISTS idx_builds_build_id ON builds(build_id);
            CREATE INDEX IF NOT EXISTS idx_build_states_build_id ON build_states(build_id);
            CREATE INDEX IF NOT EXISTS idx_build_failures_build_id ON build_failures(build_id);
        """)

    conn.commit()
    conn.close()

# Authentication functions
def verify_api_key(api_key: str) -> bool:
    """Verify API key"""
    return api_key in API_KEYS

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    api_key: Optional[str] = Depends(security_api_key)
):
    """Get current authenticated user"""
    # Check API tokens first (new system)
    if api_key:
        token_info = verify_api_token(api_key)
        if token_info:
            return token_info

    # Check legacy API keys
    if api_key and verify_api_key(api_key):
        return {"type": "api_key", "key": api_key}

    # Check JWT tokens
    if bearer:
        payload = verify_token(bearer.credentials)
        return {"type": "jwt", "username": payload.get("sub")}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Database operations
def create_build(build: BuildCreate) -> str:
    """Create a new build"""
    conn = get_db_connection()
    cursor = conn.cursor()

    build_uuid = secrets.token_urlsafe(16)

    cursor.execute("""
        INSERT INTO builds (id, platform_id, os_version_id, image_type_id, build_id, pipeline_url, commit_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        build_uuid,
        build.platform,
        build.os_version,
        build.image_type,
        build.build_id,
        build.pipeline_url,
        build.commit_hash
    ))

    # Set initial state to 0
    cursor.execute("""
        INSERT INTO build_states (build_id, state_code, message)
        VALUES (%s, 0, 'Build initialized')
    """, (build_uuid,))

    conn.commit()
    conn.close()

    # Invalidate dashboard cache since we added a new build
    cache_delete("dashboard:summary")

    return build_uuid

def transition_state(build_uuid: str, transition: StateTransition):
    """Transition build to new state"""
    if transition.state_code % 5 != 0:
        raise HTTPException(status_code=400, detail="State code must be multiple of 5")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if build exists
    cursor.execute("SELECT id FROM builds WHERE id = %s", (build_uuid,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Build not found")

    # Insert new state
    cursor.execute("""
        INSERT INTO build_states (build_id, state_code, message)
        VALUES (%s, %s, %s)
    """, (build_uuid, transition.state_code, transition.message))

    # Update build timestamp
    cursor.execute("""
        UPDATE builds SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
    """, (build_uuid,))

    conn.commit()
    conn.close()

    # Invalidate dashboard cache since build state changed
    cache_delete("dashboard:summary")

def record_failure(build_uuid: str, failure: FailureRecord):
    """Record a build failure"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if build exists
    cursor.execute("SELECT id FROM builds WHERE id = ?", (build_uuid,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Build not found")

    # Insert failure record
    cursor.execute("""
        INSERT INTO build_failures (build_id, error_message, error_code, component, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        build_uuid,
        failure.error_message,
        failure.error_code,
        failure.component,
        json.dumps(failure.details) if failure.details else None
    ))

    conn.commit()
    conn.close()

    # Invalidate dashboard cache since build failed
    cache_delete("dashboard:summary")
    """Get build details"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, bs.state_code as current_state
        FROM builds b
        LEFT JOIN (
            SELECT build_id, state_code
            FROM build_states
            WHERE (build_id, created_at) IN (
                SELECT build_id, MAX(created_at)
                FROM build_states
                GROUP BY build_id
            )
        ) bs ON b.id = bs.build_id
        WHERE b.id = %s
    """, (build_uuid,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def get_current_state(build_uuid: str) -> Optional[Dict]:
    """Get current state of a build"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT state_code, message, created_at
        FROM build_states
        WHERE build_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (build_uuid,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "build_id": build_uuid,
            "current_state": row["state_code"],
            "message": row["message"],
            "transitioned_at": row["created_at"]
        }
    return None

def get_dashboard_summary() -> Dict:
    """Get dashboard summary with Redis caching"""
    cache_key = "dashboard:summary"

    # Try to get from cache first
    cached_data = cache_get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except json.JSONDecodeError:
            pass  # Cache corrupted, fetch from DB

    # Fetch from database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total builds
    cursor.execute("SELECT COUNT(*) as total FROM builds")
    total_builds = cursor.fetchone()["total"]

    # Builds by status
    cursor.execute("""
        SELECT
            CASE
                WHEN bs.state_code = 100 THEN 'completed'
                WHEN bf.id IS NOT NULL THEN 'failed'
                ELSE 'in_progress'
            END as status,
            COUNT(*) as count
        FROM builds b
        LEFT JOIN (
            SELECT build_id, state_code
            FROM build_states
            WHERE (build_id, created_at) IN (
                SELECT build_id, MAX(created_at)
                FROM build_states
                GROUP BY build_id
            )
        ) bs ON b.id = bs.build_id
        LEFT JOIN build_failures bf ON b.id = bf.build_id
        GROUP BY
            CASE
                WHEN bs.state_code = 100 THEN 'completed'
                WHEN bf.id IS NOT NULL THEN 'failed'
                ELSE 'in_progress'
            END
    """)

    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Recent builds
    cursor.execute("""
        SELECT b.build_id, b.platform_id, b.os_version_id, b.image_type_id,
               bs.state_code, b.created_at
        FROM builds b
        LEFT JOIN (
            SELECT build_id, state_code
            FROM build_states
            WHERE (build_id, created_at) IN (
                SELECT build_id, MAX(created_at)
                FROM build_states
                GROUP BY build_id
            )
        ) bs ON b.id = bs.build_id
        ORDER BY b.created_at DESC
        LIMIT 10
    """)

    recent_builds = [dict(row) for row in cursor.fetchall()]

    # Convert datetime objects to strings for JSON serialization
    for build in recent_builds:
        if 'created_at' in build and build['created_at']:
            build['created_at'] = build['created_at'].isoformat()

    conn.close()

    result = {
        "total_builds": total_builds,
        "status_counts": status_counts,
        "recent_builds": recent_builds
    }

    # Cache the result
    cache_set(cache_key, json.dumps(result))

    return result

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    init_database()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Build State API",
    description="API for managing multi-cloud IaaS image build states",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "build-state-api"}

@app.get("/health")
async def health():
    """Health check endpoint for load balancer"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness():
    """Readiness check endpoint - verifies database and Redis connectivity"""
    checks = {
        "database": False,
        "redis": False,
        "overall": False
    }

    # Check database connectivity
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        checks["database"] = True
    except Exception as e:
        print(f"Database readiness check failed: {e}")

    # Check Redis connectivity
    try:
        client = get_redis_client()
        if client:
            client.ping()
            checks["redis"] = True
    except Exception as e:
        print(f"Redis readiness check failed: {e}")

    checks["overall"] = checks["database"] and checks["redis"]

    status_code = 200 if checks["overall"] else 503
    return checks

@app.get("/status")
async def status():
    """Comprehensive status endpoint showing health of all components"""
    import httpx
    import asyncio

    async def check_service(name: str, url: str, timeout: float = 5.0) -> dict:
        """Check health of a service"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                return {
                    "name": name,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": None,  # Could add timing if needed
                    "details": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "name": name,
                "status": "unhealthy",
                "response_time": None,
                "details": str(e)
            }

    # Check local API health
    local_health = {"name": "api-local", "status": "healthy", "details": "OK"}

    # Check other API servers
    api_servers = [
        ("api01", "http://api01:8000/health"),
        ("api02", "http://api02:8000/health"),
        ("api03", "http://api03:8000/health"),
    ]

    # Check database and Redis
    db_status = "healthy"
    redis_status = "healthy"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
    except Exception as e:
        db_status = "unhealthy"
        print(f"Database status check failed: {e}")

    try:
        client = get_redis_client()
        if client:
            client.ping()
    except Exception as e:
        redis_status = "unhealthy"
        print(f"Redis status check failed: {e}")

    # Run async checks for API servers
    api_checks = await asyncio.gather(*[
        check_service(name, url) for name, url in api_servers
    ])

    components = [
        local_health,
        {"name": "database", "status": db_status, "details": "PostgreSQL connection"},
        {"name": "redis", "status": redis_status, "details": "Redis cache"},
    ] + api_checks

    # Overall status
    overall_healthy = all(comp["status"] == "healthy" for comp in components)

    return {
        "overall_status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": components
    }

@app.post("/token")
async def login(request: TokenRequest):
    """Get JWT token (simplified - in production use proper user management)"""
    # For demo purposes - accept any username/password
    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/builds", response_model=dict)
async def create_new_build(build: BuildCreate, user=Depends(get_current_user)):
    """Create a new build"""
    try:
        build_uuid = create_build(build)
        return {"id": build_uuid, "build_id": build.build_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/builds/{build_uuid}/state")
async def update_build_state(build_uuid: str, transition: StateTransition, user=Depends(get_current_user)):
    """Update build state"""
    try:
        transition_state(build_uuid, transition)
        return {"status": "updated", "build_id": build_uuid, "new_state": transition.state_code}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/builds/{build_uuid}/failure")
async def record_build_failure(build_uuid: str, failure: FailureRecord, user=Depends(get_current_user)):
    """Record build failure"""
    try:
        record_failure(build_uuid, failure)
        return {"status": "recorded", "build_id": build_uuid}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/builds/{build_uuid}")
async def get_build_details(build_uuid: str, user=Depends(get_current_user)):
    """Get build details"""
    build = get_build(build_uuid)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build

@app.get("/builds/{build_uuid}/state")
async def get_build_state(build_uuid: str, user=Depends(get_current_user)):
    """Get current build state"""
    state = get_current_state(build_uuid)
    if not state:
        raise HTTPException(status_code=404, detail="Build not found")
    return state

@app.get("/dashboard/summary")
async def dashboard_summary(user=Depends(get_current_user)):
    """Get dashboard summary"""
    return get_dashboard_summary()

@app.get("/dashboard/recent")
async def recent_builds(user=Depends(get_current_user)):
    """Get recent builds"""
    summary = get_dashboard_summary()
    return {"recent_builds": summary["recent_builds"]}

@app.get("/dashboard/platform/{platform}")
async def builds_by_platform(platform: str, user=Depends(get_current_user)):
    """Get builds by platform"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.build_id, b.os_version_id, b.image_type_id, bs.state_code, b.created_at
        FROM builds b
        LEFT JOIN (
            SELECT build_id, state_code
            FROM build_states
            WHERE (build_id, created_at) IN (
                SELECT build_id, MAX(created_at)
                FROM build_states
                GROUP BY build_id
            )
        ) bs ON b.id = bs.build_id
        WHERE b.platform_id = %s
        ORDER BY b.created_at DESC
    """, (platform,))

    builds = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"platform": platform, "builds": builds}

# User Management Endpoints
@app.post("/users", response_model=dict)
async def create_new_user(user: UserCreate, current_user=Depends(get_current_user)):
    """Create a new user (admin only)"""
    if current_user.get("type") != "api_key" and not current_user.get("is_superuser", False):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        user_id = create_user(user)
        return {"id": user_id, "username": user.username, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}")
async def get_user_details(user_id: str, current_user=Depends(get_current_user)):
    """Get user details"""
    # Users can view their own details, admins can view any
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Access denied")

    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user)

@app.put("/users/{user_id}")
async def update_user_details(user_id: str, updates: UserUpdate, current_user=Depends(get_current_user)):
    """Update user details (admin only for others, users can update themselves)"""
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        update_user(user_id, updates)
        return {"status": "updated", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/profile")
async def get_user_profile_endpoint(user_id: str, current_user=Depends(get_current_user)):
    """Get user profile"""
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Access denied")

    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return UserProfileResponse(**profile)

# API Token Management Endpoints
@app.post("/users/{user_id}/tokens", response_model=dict)
async def create_user_token(user_id: str, token_data: APITokenCreate, current_user=Depends(get_current_user)):
    """Create API token for user (admin only for others, users for themselves)"""
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        token_value = create_api_token(user_id, token_data)
        return {"token": token_value, "name": token_data.name, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/tokens")
async def get_user_tokens(user_id: str, current_user=Depends(get_current_user)):
    """Get API tokens for user"""
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Access denied")

    tokens = get_api_tokens(user_id)
    return {"tokens": [APITokenResponse(**token) for token in tokens]}

@app.delete("/users/{user_id}/tokens/{token_id}")
async def deactivate_user_token(user_id: str, token_id: str, current_user=Depends(get_current_user)):
    """Deactivate API token"""
    if (current_user.get("type") != "api_key" and
        current_user.get("user_id") != user_id and
        not current_user.get("is_superuser", False)):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        deactivate_api_token(token_id, user_id)
        return {"status": "deactivated", "token_id": token_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Authentication Endpoints
@app.post("/auth/idm")
async def idm_login(request: IDMLoginRequest):
    """Login with IDM token"""
    user_info = authenticate_with_idm(request.username, request.idm_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="IDM authentication failed")

    # Create JWT token
    access_token = create_access_token(data={
        "sub": user_info["username"],
        "user_id": user_info["user_id"],
        "type": "idm"
    })

    return {"access_token": access_token, "token_type": "bearer", "user": user_info}

@app.post("/auth/password")
async def password_login(request: TokenRequest):
    """Login with username/password"""
    user = get_user_by_username(request.username)
    if not user or not pwd_context.verify(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account deactivated")

    access_token = create_access_token(data={
        "sub": user["username"],
        "user_id": user["id"],
        "type": "password"
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_superuser": user["is_superuser"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )