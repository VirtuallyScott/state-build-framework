"""
SQLAlchemy models and Pydantic schemas for the Build State API.
"""
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# SQLAlchemy Models
class Platform(Base):
    __tablename__ = "platforms"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    cloud_provider = Column(String, nullable=False)
    region = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    builds = relationship("Build", back_populates="platform")


class OSVersion(Base):
    __tablename__ = "os_versions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    builds = relationship("Build", back_populates="os_version")


class ImageType(Base):
    __tablename__ = "image_types"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    builds = relationship("Build", back_populates="image_type")


class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    parent_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    builds = relationship("Build", back_populates="project")
    child_projects = relationship("Project", backref="parent_project", remote_side=[id])


class Build(Base):
    __tablename__ = "builds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_number = Column(String, nullable=False, unique=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    os_version_id = Column(UUID(as_uuid=True), ForeignKey("os_versions.id"), nullable=False)
    image_type_id = Column(UUID(as_uuid=True), ForeignKey("image_types.id"), nullable=False)
    current_state = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="pending")
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    concourse_pipeline_url = Column(Text)
    concourse_job_name = Column(Text)
    ami_id = Column(Text)
    image_id = Column(Text)
    packer_manifest = Column(JSON)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="builds")
    platform = relationship("Platform", back_populates="builds")
    os_version = relationship("OSVersion", back_populates="builds")
    image_type = relationship("ImageType", back_populates="builds")
    states = relationship("BuildState", back_populates="build", cascade="all, delete-orphan")
    failures = relationship("BuildFailure", back_populates="build", cascade="all, delete-orphan")


class BuildState(Base):
    __tablename__ = "build_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_id = Column(UUID(as_uuid=True), ForeignKey("builds.id"), nullable=False)
    state = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    artifact_storage_type = Column(String(50))  # e.g., 's3', 'nfs', 'ebs', 'ceph', 'local'
    artifact_storage_path = Column(Text)  # Full path/URI to the artifact
    artifact_size_bytes = Column(Integer)  # Size of artifact in bytes
    artifact_checksum = Column(String(128))  # SHA256 or MD5 checksum
    artifact_metadata = Column(JSON)  # Additional metadata about the artifact
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    build = relationship("Build", back_populates="states")


class BuildFailure(Base):
    __tablename__ = "build_failures"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_id = Column(UUID(as_uuid=True), ForeignKey("builds.id"), nullable=False)
    state = Column(Integer, nullable=False)
    failure_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON)
    component = Column(String)
    retry_attempt = Column(Integer, default=1)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    build = relationship("Build", back_populates="failures")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    employee_id = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))

    profiles = relationship("UserProfile", back_populates="user")
    tokens = relationship("APIToken", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    email = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="profiles")



class APIToken(Base):
    __tablename__ = "api_tokens"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    scopes = Column(JSON)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="tokens")


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

class OSVersionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    version: str = Field(..., min_length=1, max_length=50)

class OSVersionCreate(OSVersionBase):
    pass

class OSVersionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    version: Optional[str] = Field(None, min_length=1, max_length=50)

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

class ImageVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ImageVariantCreate(ImageVariantBase):
    pass

class ImageVariantUpdate(ImageVariantBase):
    pass

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
    builds: List['BuildResponse'] = []

    class Config:
        from_attributes = True


class BuildResponse(BuildBase):
    id: uuid.UUID
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


ProjectResponse.model_rebuild()
BuildResponse.model_rebuild()


# Other Schemas
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserSchema(BaseModel):
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True

class UserInDB(UserSchema):
    hashed_password: str



class IDMLoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(UserSchema):
    password: str


class UserResponse(UserSchema):
    id: uuid.UUID

    class Config:
        from_attributes = True


class UserUpdate(UserSchema):
    password: Optional[str] = None


class APITokenCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scopes: Optional[List[str]] = []


class APITokenResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    scopes: Optional[List[str]] = []
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APITokenInfo(APITokenResponse):
    token: str


class UserProfileResponse(UserResponse):
    tokens: List[APITokenResponse] = []


class StateTransition(BaseModel):
    state_name: str
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    artifact_storage_type: Optional[str] = Field(None, max_length=50, description="Type of storage (s3, nfs, ebs, ceph, local, etc.)")
    artifact_storage_path: Optional[str] = Field(None, description="Full path/URI to the stored artifact")
    artifact_size_bytes: Optional[int] = Field(None, ge=0, description="Size of artifact in bytes")
    artifact_checksum: Optional[str] = Field(None, max_length=128, description="SHA256 or MD5 checksum")
    artifact_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional artifact metadata")


class FailureRecord(BaseModel):
    error_message: str
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StateResponse(BaseModel):
    build_id: uuid.UUID
    current_state: str
    status: str
    last_transition: datetime
    state_history: List[BuildStateResponse]

class DashboardSummary(BaseModel):
    total_builds: int
    active_builds: int
    completed_builds: int
    failed_builds: int
    builds_by_platform: Dict[str, int]
    builds_by_state: Dict[str, int]


class StateCode(Base):
    __tablename__ = "state_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_initial = Column(Boolean, default=False)
    is_final = Column(Boolean, default=False)
    is_error = Column(Boolean, default=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))

class StateCodeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_final: bool = False
    is_error: bool = False

class StateCodeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_initial: Optional[bool] = None
    is_final: Optional[bool] = None
    is_error: Optional[bool] = None

class StateCodeResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_initial: bool
    is_final: bool
    is_error: bool
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# RESUMABLE BUILDS MODELS
# ============================================================================

# SQLAlchemy ORM Models

class BuildArtifact(Base):
    """Tracks artifacts created during builds (snapshots, images, etc.)"""
    __tablename__ = "build_artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"), nullable=False)
    state_code = Column(Integer, nullable=False)
    
    # Artifact identification
    artifact_name = Column(String, nullable=False)
    artifact_type = Column(String, nullable=False)
    artifact_path = Column(Text, nullable=False)
    
    # Storage details
    storage_backend = Column(String, nullable=False)
    storage_region = Column(String)
    storage_bucket = Column(String)
    storage_key = Column(Text)
    
    # Artifact metadata
    size_bytes = Column(Integer)
    checksum = Column(String)
    checksum_algorithm = Column(String, default='sha256')
    
    # Lifecycle
    is_resumable = Column(Boolean, default=True)
    is_final = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Additional metadata
    artifact_metadata = Column('metadata', JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    build = relationship("Build", backref="artifacts")


class BuildVariable(Base):
    """Stores build-specific variables needed for resumption"""
    __tablename__ = "build_variables"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"), nullable=False)
    
    # Variable details
    variable_key = Column(String, nullable=False)
    variable_value = Column(Text, nullable=False)
    variable_type = Column(String, default='string')
    
    # Context
    set_at_state = Column(Integer)
    
    # Lifecycle
    is_sensitive = Column(Boolean, default=False)
    is_required_for_resume = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    build = relationship("Build", backref="variables")


class ResumableState(Base):
    """Defines which state codes are resumable and their requirements"""
    __tablename__ = "resumable_states"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    state_code = Column(Integer, nullable=False)
    
    # Resumability configuration
    is_resumable = Column(Boolean, default=True)
    resume_strategy = Column(String)  # 'from_artifact', 'rerun_state', 'skip_to_next'
    
    # Requirements
    required_artifacts = Column(JSON)
    required_variables = Column(JSON)
    
    # Resume command
    resume_command = Column(Text)
    resume_timeout_seconds = Column(Integer, default=3600)
    
    # Documentation
    description = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    project = relationship("Project", backref="resumable_states")


class ResumeRequest(Base):
    """Tracks requests to resume builds"""
    __tablename__ = "resume_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"), nullable=False)
    
    # Resume details
    resume_from_state = Column(Integer, nullable=False)
    resume_to_state = Column(Integer)
    resume_reason = Column(Text)
    
    # Request source
    requested_by = Column(String)
    request_source = Column(String)  # 'api', 'webhook', 'cli', 'auto'
    
    # Orchestration
    orchestration_job_id = Column(Text)
    orchestration_job_url = Column(Text)
    orchestration_status = Column(String)  # 'pending', 'triggered', 'running', 'completed', 'failed'
    
    # Execution tracking
    triggered_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # Metadata
    request_metadata = Column('metadata', JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    build = relationship("Build", backref="resume_requests")


class BuildJob(Base):
    """Links builds to CI/CD job information"""
    __tablename__ = "build_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id = Column(String, ForeignKey("builds.id"), nullable=False)
    
    # CI/CD platform details
    platform = Column(String, nullable=False)  # 'concourse', 'jenkins', etc.
    pipeline_name = Column(String)
    job_name = Column(String, nullable=False)
    job_url = Column(Text)
    
    # Job identification
    job_id = Column(Text)
    build_number = Column(String)
    
    # Trigger information
    triggered_by = Column(String)
    trigger_source = Column(String)  # 'manual', 'webhook', 'schedule', 'resume'
    
    # Job status
    status = Column(String)  # 'pending', 'running', 'success', 'failed', 'aborted'
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Resume context
    is_resume_job = Column(Boolean, default=False)
    resumed_from_state = Column(Integer)
    parent_job_id = Column(String, ForeignKey("build_jobs.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    build = relationship("Build", backref="jobs")
    parent_job = relationship("BuildJob", remote_side=[id], backref="child_jobs")


# Pydantic Schemas

class BuildArtifactBase(BaseModel):
    artifact_name: str
    artifact_type: str
    artifact_path: str
    storage_backend: str
    storage_region: Optional[str] = None
    storage_bucket: Optional[str] = None
    storage_key: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    checksum_algorithm: str = 'sha256'
    is_resumable: bool = True
    is_final: bool = False
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BuildArtifactCreate(BuildArtifactBase):
    state_code: int


class BuildArtifactUpdate(BaseModel):
    artifact_name: Optional[str] = None
    artifact_type: Optional[str] = None
    artifact_path: Optional[str] = None
    is_resumable: Optional[bool] = None
    is_final: Optional[bool] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BuildArtifactResponse(BuildArtifactBase):
    id: str
    build_id: str
    state_code: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BuildVariableBase(BaseModel):
    variable_key: str
    variable_value: str
    variable_type: str = 'string'
    set_at_state: Optional[int] = None
    is_sensitive: bool = False
    is_required_for_resume: bool = False


class BuildVariableCreate(BuildVariableBase):
    pass


class BuildVariableUpdate(BaseModel):
    variable_value: Optional[str] = None
    variable_type: Optional[str] = None
    is_sensitive: Optional[bool] = None
    is_required_for_resume: Optional[bool] = None


class BuildVariableResponse(BuildVariableBase):
    id: str
    build_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumableStateBase(BaseModel):
    state_code: int
    is_resumable: bool = True
    resume_strategy: Optional[str] = None
    required_artifacts: Optional[List[str]] = None
    required_variables: Optional[List[str]] = None
    resume_command: Optional[str] = None
    resume_timeout_seconds: int = 3600
    description: Optional[str] = None
    notes: Optional[str] = None


class ResumableStateCreate(ResumableStateBase):
    pass


class ResumableStateUpdate(BaseModel):
    is_resumable: Optional[bool] = None
    resume_strategy: Optional[str] = None
    required_artifacts: Optional[List[str]] = None
    required_variables: Optional[List[str]] = None
    resume_command: Optional[str] = None
    resume_timeout_seconds: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class ResumableStateResponse(ResumableStateBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeRequestBase(BaseModel):
    resume_from_state: int
    resume_to_state: Optional[int] = None
    resume_reason: Optional[str] = None
    requested_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResumeRequestCreate(ResumeRequestBase):
    request_source: str = 'api'


class ResumeRequestUpdate(BaseModel):
    orchestration_job_id: Optional[str] = None
    orchestration_job_url: Optional[str] = None
    orchestration_status: Optional[str] = None
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ResumeRequestResponse(ResumeRequestBase):
    id: str
    build_id: str
    request_source: str
    orchestration_job_id: Optional[str] = None
    orchestration_job_url: Optional[str] = None
    orchestration_status: Optional[str] = None
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuildJobBase(BaseModel):
    platform: str
    pipeline_name: Optional[str] = None
    job_name: str
    job_url: Optional[str] = None
    job_id: Optional[str] = None
    build_number: Optional[str] = None
    triggered_by: Optional[str] = None
    trigger_source: Optional[str] = None
    status: Optional[str] = None
    is_resume_job: bool = False
    resumed_from_state: Optional[int] = None


class BuildJobCreate(BuildJobBase):
    parent_job_id: Optional[str] = None


class BuildJobUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BuildJobResponse(BuildJobBase):
    id: str
    build_id: str
    parent_job_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeContext(BaseModel):
    """Complete context needed to resume a build"""
    build_id: str
    current_state: int
    last_successful_state: Optional[int] = None
    failed_state: Optional[int] = None
    resume_from_state: int
    artifacts: List[BuildArtifactResponse] = []
    variables: Dict[str, str] = {}
    resumable_state_config: Optional[ResumableStateResponse] = None
    
    class Config:
        from_attributes = True