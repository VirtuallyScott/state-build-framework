"""
Shared Pydantic models for Build State API and CLI.

These models are used by both the FastAPI service and the CLI tool
to ensure type safety and consistency across the entire system.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class BuildCreate(BaseModel):
    """Model for creating a new build."""

    platform: str = Field(
        ...,
        description="Platform identifier (e.g., 'aws-commercial', 'azure', 'gcp')"
    )
    os_version: str = Field(
        ...,
        description="OS version identifier (e.g., 'rhel-8.8', 'ubuntu-22.04')"
    )
    image_type: str = Field(
        ...,
        description="Image type identifier (e.g., 'base', 'hana', 'sapapp')"
    )
    build_id: str = Field(
        ...,
        description="Unique build identifier across all platforms"
    )
    pipeline_url: Optional[str] = Field(
        None,
        description="URL to the CI/CD pipeline that triggered this build"
    )
    commit_hash: Optional[str] = Field(
        None,
        description="Git commit hash associated with this build"
    )

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform identifier."""
        valid_platforms = [
            'aws-commercial', 'aws-govcloud', 'azure', 'gcp',
            'openstack', 'cloud-foundry'
        ]
        if v not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v

    @validator('os_version')
    def validate_os_version(cls, v):
        """Validate OS version identifier."""
        valid_versions = [
            'rhel-8.8', 'rhel-9.2', 'ubuntu-20.04', 'ubuntu-22.04'
        ]
        if v not in valid_versions:
            raise ValueError(f"OS version must be one of: {', '.join(valid_versions)}")
        return v

    @validator('image_type')
    def validate_image_type(cls, v):
        """Validate image type identifier."""
        valid_types = ['base', 'hana', 'sapapp', 'openvpn']
        if v not in valid_types:
            raise ValueError(f"Image type must be one of: {', '.join(valid_types)}")
        return v


class StateTransition(BaseModel):
    """Model for transitioning build state."""

    state_code: int = Field(
        ...,
        ge=0,
        le=100,
        description="State code (0-100, must be multiple of 5)"
    )
    message: Optional[str] = Field(
        None,
        description="Optional message describing the state transition"
    )

    @validator('state_code')
    def validate_state_code(cls, v):
        """Validate that state code is a multiple of 5."""
        if v % 5 != 0:
            raise ValueError(
                f"State code must be a multiple of 5 (got {v}). "
                "Valid codes: 0, 5, 10, 15, ..., 100"
            )
        return v


class FailureRecord(BaseModel):
    """Model for recording build failures."""

    error_message: str = Field(
        ...,
        description="Human-readable error message"
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code (e.g., 'PACKER_TIMEOUT')"
    )
    component: Optional[str] = Field(
        None,
        description="Component that failed (e.g., 'packer', 'ansible', 'terraform')"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details as key-value pairs"
    )


class BuildResponse(BaseModel):
    """Response model for build details."""

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
    """Response model for build state."""

    build_id: str
    current_state: int
    message: Optional[str]
    transitioned_at: str


class DashboardSummary(BaseModel):
    """Response model for dashboard summary."""

    total_builds: int
    status_counts: Dict[str, int]  # completed, failed, in_progress
    recent_builds: list


class TokenRequest(BaseModel):
    """Model for JWT token requests."""

    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")


class TokenResponse(BaseModel):
    """Response model for JWT tokens."""

    access_token: str
    token_type: str = "bearer"


class APIError(BaseModel):
    """Model for API error responses."""

    detail: str
    status_code: Optional[int] = None
    errors: Optional[Dict[str, Any]] = None


class UserCreate(BaseModel):
    """Model for creating a new user."""

    username: str = Field(..., description="Unique username")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    password: str = Field(..., description="User password")
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """Model for updating user details."""

    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(BaseModel):
    """Response model for user details."""

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
    """Response model for user profile."""

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
    """Model for creating API tokens."""

    name: str = Field(..., description="Token name")
    scopes: list[str] = Field(default_factory=list, description="Permission scopes")
    expires_at: Optional[str] = None


class APITokenResponse(BaseModel):
    """Response model for API tokens."""

    id: str
    user_id: str
    name: str
    scopes: list[str]
    expires_at: Optional[str]
    is_active: bool
    created_at: str


class APITokenCreateResponse(BaseModel):
    """Response model for token creation (includes the actual token)."""

    token: str
    name: str
    status: str


class IDMLoginRequest(BaseModel):
    """Model for IDM authentication requests."""

    username: str = Field(..., description="Username for IDM authentication")
    idm_token: str = Field(..., description="IDM authentication token")