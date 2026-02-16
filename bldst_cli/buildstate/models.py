"""
Pydantic schemas for the Build State API.
"""
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from pydantic import BaseModel, Field


# Pydantic Schemas
# Base models for creation and updates
class PlatformBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    cloud_provider: str = Field(..., min_length=1, max_length=50)
    region: Optional[str] = Field(None, max_length=50)

class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    cloud_provider: Optional[str] = Field(None, min_length=1, max_length=50)
    region: Optional[str] = Field(None, max_length=50)

class OSDistributionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, unique=True)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class OSDistributionCreate(OSDistributionBase):
    pass

class OSDistributionUpdate(OSDistributionBase):
    pass

class OSVersionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    version: str = Field(..., min_length=1, max_length=50)

class OSVersionCreate(OSVersionBase):
    pass

class OSVersionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    version: Optional[str] = Field(None, min_length=1, max_length=50)

class CloudProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, unique=True)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class CloudProviderCreate(CloudProviderBase):
    pass

class CloudProviderUpdate(CloudProviderBase):
    pass

class ImageVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, unique=True)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ImageVariantCreate(ImageVariantBase):
    pass

class ImageVariantUpdate(ImageVariantBase):
    pass

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    parent_project_id: Optional[uuid.UUID] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ImageTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class ImageTypeCreate(ImageTypeBase):
    pass

class ImageTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class BuildBase(BaseModel):
    build_number: str
    project_id: uuid.UUID
    platform_id: uuid.UUID
    os_version_id: uuid.UUID
    image_type_id: uuid.UUID
    created_by: Optional[str] = None
    concourse_pipeline_url: Optional[str] = None
    concourse_job_name: Optional[str] = None

class BuildCreate(BuildBase):
    pass

class BuildUpdate(BaseModel):
    current_state: Optional[int] = None
    status: Optional[str] = None
    end_time: Optional[datetime] = None
    ami_id: Optional[str] = None
    image_id: Optional[str] = None
    packer_manifest: Optional[Dict[str, Any]] = None

class BuildStateBase(BaseModel):
    state: int
    status: str
    start_time: datetime
    error_message: Optional[str] = None
    retry_count: Optional[int] = 0
    artifact_storage_type: Optional[str] = Field(None, max_length=50, description="Type of storage (s3, nfs, ebs, ceph, local, etc.)")
    artifact_storage_path: Optional[str] = Field(None, description="Full path/URI to the stored artifact")
    artifact_size_bytes: Optional[int] = Field(None, ge=0, description="Size of artifact in bytes")
    artifact_checksum: Optional[str] = Field(None, max_length=128, description="SHA256 or MD5 checksum")
    artifact_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional artifact metadata")

class BuildStateCreate(BuildStateBase):
    build_id: uuid.UUID

class BuildFailureBase(BaseModel):
    state: int
    failure_type: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    component: Optional[str] = None
    retry_attempt: Optional[int] = 1

class BuildFailureCreate(BuildFailureBase):
    build_id: uuid.UUID


# Response models
class OSDistributionResponse(OSDistributionBase):
    id: uuid.UUID
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class CloudProviderResponse(CloudProviderBase):
    id: uuid.UUID
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ImageVariantResponse(ImageVariantBase):
    id: uuid.UUID
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlatformResponse(PlatformBase):
    id: str
    created_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OSVersionResponse(OSVersionBase):
    id: str
    created_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ImageTypeResponse(ImageTypeBase):
    id: str
    created_at: datetime
    deactivated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BuildStateResponse(BuildStateBase):
    id: uuid.UUID
    build_id: uuid.UUID
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class BuildFailureResponse(BuildFailureBase):
    id: uuid.UUID
    build_id: uuid.UUID
    resolved: bool
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    child_projects: List['ProjectResponse'] = []

    class Config:
        from_attributes = True

class BuildResponse(BaseModel):
    id: uuid.UUID
    build_number: str
    project_id: uuid.UUID
    platform_id: uuid.UUID
    os_version_id: uuid.UUID
    image_type_id: uuid.UUID
    created_by: Optional[str] = None
    concourse_pipeline_url: Optional[str] = None
    concourse_job_name: Optional[str] = None
    current_state: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    ami_id: Optional[str] = None
    image_id: Optional[str] = None
    packer_manifest: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    platform: PlatformResponse
    os_version: OSVersionResponse
    project: ProjectResponse
    image_type: ImageTypeResponse
    states: List[BuildStateResponse] = []
    failures: List[BuildFailureResponse] = []

    class Config:
        from_attributes = True

# Other Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str


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


# State Code models
class StateCodeBase(BaseModel):
    code: int = Field(..., ge=0, le=100)
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # Hex color
    is_terminal: bool = Field(default=False)
    sort_order: int = Field(default=0)

class StateCodeCreate(StateCodeBase):
    project_id: uuid.UUID

class StateCodeUpdate(StateCodeBase):
    pass

class StateCodeResponse(StateCodeBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True