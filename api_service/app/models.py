"""
Pydantic models for the Build State API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# User models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


# API Token models
class APITokenCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)


class APITokenResponse(BaseModel):
    id: int
    user_id: int
    token: str
    description: str
    created_at: datetime
    last_used: Optional[datetime]


# Authentication models
class IDMLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Build models
class BuildCreate(BaseModel):
    platform: str = Field(..., min_length=1, max_length=50)
    image_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class StateTransition(BaseModel):
    state_code: int = Field(..., ge=0, le=100)
    message: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None


class FailureRecord(BaseModel):
    error_message: str = Field(..., max_length=1000)
    error_code: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class BuildResponse(BaseModel):
    id: str
    platform: str
    image_type: str
    description: Optional[str]
    current_state: int
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]


class StateResponse(BaseModel):
    build_id: str
    current_state: int
    status: str
    last_transition: datetime
    state_history: List[Dict[str, Any]]


# Dashboard models
class DashboardSummary(BaseModel):
    total_builds: int
    active_builds: int
    completed_builds: int
    failed_builds: int
    builds_by_platform: Dict[str, int]
    builds_by_state: Dict[str, int]


class RecentBuild(BaseModel):
    id: str
    platform: str
    image_type: str
    current_state: int
    status: str
    updated_at: datetime


# Health check models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ReadinessResponse(BaseModel):
    status: str
    database: str
    cache: str
    timestamp: datetime


class StatusResponse(BaseModel):
    status: str
    uptime: str
    version: str
    database: Dict[str, Any]
    cache: Dict[str, Any]
    timestamp: datetime