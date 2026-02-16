"""
HTTP client for Build State API.

This client provides a clean, async interface to the Build State API
with automatic authentication, error handling, and response parsing.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
import json
from pathlib import Path
import os
import uuid

import httpx
from pydantic import ValidationError, BaseModel

from .models import (
    BuildCreate, BuildResponse, BuildUpdate,
    BuildStateCreate, BuildStateResponse,
    BuildFailureCreate, BuildFailureResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    PlatformCreate, PlatformUpdate, PlatformResponse,
    OSVersionCreate, OSVersionUpdate, OSVersionResponse,
    ImageTypeCreate, ImageTypeUpdate, ImageTypeResponse,
    OSDistributionCreate, OSDistributionUpdate, OSDistributionResponse,
    CloudProviderCreate, CloudProviderUpdate, CloudProviderResponse,
    ImageVariantCreate, ImageVariantUpdate, ImageVariantResponse,
    StateCodeCreate, StateCodeUpdate, StateCodeResponse,
    TokenRequest, TokenResponse,
    UserCreate, UserUpdate, UserResponse,
)


class BuildStateClient:
    """
    Async HTTP client for Build State API.

    Supports both API key and JWT authentication.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API (e.g., 'http://localhost:8080')
            api_key: API key for authentication (for pipelines)
            jwt_token: JWT token for authentication (for interactive use)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.timeout = timeout

        # Create httpx client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self._get_default_headers(),
            follow_redirects=True
        )

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers including authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if self.api_key:
            headers['X-API-Key'] = self.api_key
        elif self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'

        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.request(method, url, json=data, params=params)

            if 200 <= response.status_code < 300:
                if response.status_code == 204:
                    return None
                return response.json()
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    pass
                detail = error_data.get('detail', response.text)
                raise BuildStateAPIError(
                    str(detail),
                    status_code=response.status_code,
                    errors=error_data
                )

        except httpx.TimeoutException as e:
            raise BuildStateAPIError(f"Request timeout: {e}", status_code=408)
        except httpx.ConnectError as e:
            raise BuildStateAPIError(f"Connection failed to {url}: {e}", status_code=503)
        except json.JSONDecodeError as e:
            raise BuildStateAPIError(f"Invalid JSON response from API: {e}", status_code=500)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # Authentication methods
    async def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate and get JWT token."""
        request = TokenRequest(username=username, password=password)
        # FastAPI's OAuth2PasswordRequestForm expects form data
        response = await self.client.post(
            f"{self.base_url}/token",
            data=request.dict()
        )
        if response.status_code != 200:
            raise BuildStateAPIError(f"Authentication failed: {response.text}", status_code=response.status_code)
        return TokenResponse(**response.json())

    # Generic CRUD methods
    async def _create_item(self, endpoint: str, create_model: BaseModel, response_model: BaseModel) -> BaseModel:
        response = await self._make_request('POST', endpoint, create_model.dict())
        return response_model(**response)

    async def _get_item(self, endpoint: str, item_id: Union[str, uuid.UUID], response_model: BaseModel) -> BaseModel:
        response = await self._make_request('GET', f"{endpoint}/{item_id}")
        return response_model(**response)

    async def _list_items(self, endpoint: str, response_model: BaseModel, skip: int = 0, limit: int = 100) -> List[BaseModel]:
        response = await self._make_request('GET', endpoint, params={"skip": skip, "limit": limit})
        return [response_model(**item) for item in response]

    async def _update_item(self, endpoint: str, item_id: Union[str, uuid.UUID], update_model: BaseModel, response_model: BaseModel) -> BaseModel:
        response = await self._make_request('PUT', f"{endpoint}/{item_id}", update_model.dict(exclude_unset=True))
        return response_model(**response)

    async def _delete_item(self, endpoint: str, item_id: Union[str, uuid.UUID]) -> None:
        await self._make_request('DELETE', f"{endpoint}/{item_id}")

    # Cloud Provider methods
    async def create_cloud_provider(self, data: CloudProviderCreate) -> CloudProviderResponse:
        return await self._create_item("/cloud-providers", data, CloudProviderResponse)
    async def get_cloud_provider(self, item_id: uuid.UUID) -> CloudProviderResponse:
        return await self._get_item("/cloud-providers", item_id, CloudProviderResponse)
    async def list_cloud_providers(self, skip: int = 0, limit: int = 100) -> List[CloudProviderResponse]:
        return await self._list_items("/cloud-providers", CloudProviderResponse, skip, limit)
    async def update_cloud_provider(self, item_id: uuid.UUID, data: CloudProviderUpdate) -> CloudProviderResponse:
        return await self._update_item("/cloud-providers", item_id, data, CloudProviderResponse)
    async def delete_cloud_provider(self, item_id: uuid.UUID) -> None:
        await self._delete_item("/cloud-providers", item_id)

    # OS Distribution methods
    async def create_os_distribution(self, data: OSDistributionCreate) -> OSDistributionResponse:
        return await self._create_item("/os-distributions", data, OSDistributionResponse)
    async def get_os_distribution(self, item_id: uuid.UUID) -> OSDistributionResponse:
        return await self._get_item("/os-distributions", item_id, OSDistributionResponse)
    async def list_os_distributions(self, skip: int = 0, limit: int = 100) -> List[OSDistributionResponse]:
        return await self._list_items("/os-distributions", OSDistributionResponse, skip, limit)
    async def update_os_distribution(self, item_id: uuid.UUID, data: OSDistributionUpdate) -> OSDistributionResponse:
        return await self._update_item("/os-distributions", item_id, data, OSDistributionResponse)
    async def delete_os_distribution(self, item_id: uuid.UUID) -> None:
        await self._delete_item("/os-distributions", item_id)

    # Image Variant methods
    async def create_image_variant(self, data: ImageVariantCreate) -> ImageVariantResponse:
        return await self._create_item("/image-variants", data, ImageVariantResponse)
    async def get_image_variant(self, item_id: uuid.UUID) -> ImageVariantResponse:
        return await self._get_item("/image-variants", item_id, ImageVariantResponse)
    async def list_image_variants(self, skip: int = 0, limit: int = 100) -> List[ImageVariantResponse]:
        return await self._list_items("/image-variants", ImageVariantResponse, skip, limit)
    async def update_image_variant(self, item_id: uuid.UUID, data: ImageVariantUpdate) -> ImageVariantResponse:
        return await self._update_item("/image-variants", item_id, data, ImageVariantResponse)
    async def delete_image_variant(self, item_id: uuid.UUID) -> None:
        await self._delete_item("/image-variants", item_id)

    # Platform methods
    async def create_platform(self, data: PlatformCreate) -> PlatformResponse:
        return await self._create_item("/platforms/", data, PlatformResponse)
    async def get_platform(self, item_id: str) -> PlatformResponse:
        return await self._get_item("/platforms", item_id, PlatformResponse)
    async def list_platforms(self, skip: int = 0, limit: int = 100) -> List[PlatformResponse]:
        return await self._list_items("/platforms/", PlatformResponse, skip, limit)
    async def update_platform(self, item_id: str, data: PlatformUpdate) -> PlatformResponse:
        return await self._update_item("/platforms", item_id, data, PlatformResponse)
    async def delete_platform(self, item_id: str) -> None:
        await self._delete_item("/platforms", item_id)

    # OS Version methods
    async def create_os_version(self, data: OSVersionCreate) -> OSVersionResponse:
        return await self._create_item("/os_versions/", data, OSVersionResponse)
    async def get_os_version(self, item_id: str) -> OSVersionResponse:
        return await self._get_item("/os_versions", item_id, OSVersionResponse)
    async def list_os_versions(self, skip: int = 0, limit: int = 100) -> List[OSVersionResponse]:
        return await self._list_items("/os_versions/", OSVersionResponse, skip, limit)
    async def update_os_version(self, item_id: str, data: OSVersionUpdate) -> OSVersionResponse:
        return await self._update_item("/os_versions", item_id, data, OSVersionResponse)
    async def delete_os_version(self, item_id: str) -> None:
        await self._delete_item("/os_versions", item_id)

    # Image Type methods
    async def create_image_type(self, data: ImageTypeCreate) -> ImageTypeResponse:
        return await self._create_item("/image_types/", data, ImageTypeResponse)
    async def get_image_type(self, item_id: str) -> ImageTypeResponse:
        return await self._get_item("/image_types", item_id, ImageTypeResponse)
    async def list_image_types(self, skip: int = 0, limit: int = 100) -> List[ImageTypeResponse]:
        return await self._list_items("/image_types/", ImageTypeResponse, skip, limit)
    async def update_image_type(self, item_id: str, data: ImageTypeUpdate) -> ImageTypeResponse:
        return await self._update_item("/image_types", item_id, data, ImageTypeResponse)
    async def delete_image_type(self, item_id: str) -> None:
        await self._delete_item("/image_types", item_id)

    # Project methods
    async def create_project(self, data: ProjectCreate) -> ProjectResponse:
        return await self._create_item("/projects", data, ProjectResponse)
    async def get_project(self, item_id: uuid.UUID) -> ProjectResponse:
        return await self._get_item("/projects", item_id, ProjectResponse)
    async def list_projects(self, skip: int = 0, limit: int = 100) -> List[ProjectResponse]:
        return await self._list_items("/projects", ProjectResponse, skip, limit)
    async def update_project(self, item_id: uuid.UUID, data: ProjectUpdate) -> ProjectResponse:
        return await self._update_item("/projects", item_id, data, ProjectResponse)
    async def delete_project(self, item_id: uuid.UUID) -> None:
        await self._delete_item("/projects", item_id)

    # Build methods
    async def create_build(self, build: BuildCreate) -> BuildResponse:
        return await self._create_item("/builds", build, BuildResponse)
    async def get_build(self, build_id: uuid.UUID) -> BuildResponse:
        return await self._get_item("/builds", build_id, BuildResponse)
    async def list_builds(self, skip: int = 0, limit: int = 100) -> List[BuildResponse]:
        return await self._list_items("/builds", BuildResponse, skip, limit)
    async def update_build(self, build_id: uuid.UUID, data: BuildUpdate) -> BuildResponse:
        return await self._update_item("/builds", build_id, data, BuildResponse)

    # Build State methods
    async def add_build_state(self, build_id: uuid.UUID, state_data: BuildStateCreate) -> BuildStateResponse:
        response = await self._make_request('POST', f'/builds/{build_id}/states', state_data.dict())
        return BuildStateResponse(**response)
    async def get_build_states(self, build_id: uuid.UUID) -> List[BuildStateResponse]:
        response = await self._make_request('GET', f'/builds/{build_id}/states')
        return [BuildStateResponse(**item) for item in response]

    # Build Failure methods
    async def add_build_failure(self, build_id: uuid.UUID, failure_data: BuildFailureCreate) -> BuildFailureResponse:
        response = await self._make_request('POST', f'/builds/{build_id}/failures', failure_data.dict())
        return BuildFailureResponse(**response)
    async def get_build_failures(self, build_id: uuid.UUID) -> List[BuildFailureResponse]:
        response = await self._make_request('GET', f'/builds/{build_id}/failures')
        return [BuildFailureResponse(**item) for item in response]

    # State Code methods
    async def create_state_code(self, data: StateCodeCreate) -> StateCodeResponse:
        return await self._create_item("/state-codes", data, StateCodeResponse)
    async def get_state_code(self, item_id: uuid.UUID) -> StateCodeResponse:
        return await self._get_item("/state-codes", item_id, StateCodeResponse)
    async def list_state_codes(self, skip: int = 0, limit: int = 100) -> List[StateCodeResponse]:
        return await self._list_items("/state-codes", StateCodeResponse, skip, limit)
    async def update_state_code(self, item_id: uuid.UUID, data: StateCodeUpdate) -> StateCodeResponse:
        return await self._update_item("/state-codes", item_id, data, StateCodeResponse)
    async def delete_state_code(self, item_id: uuid.UUID) -> None:
        await self._delete_item("/state-codes", item_id)

    # User methods
    async def create_user(self, data: UserCreate) -> UserResponse:
        return await self._create_item("/users", data, UserResponse)
    async def get_user(self, user_id: int) -> UserResponse:
        response = await self._make_request('GET', f"/users/{user_id}")
        return UserResponse(**response)
    async def get_current_user(self) -> UserResponse:
        response = await self._make_request('GET', "/users/me")
        return UserResponse(**response)
    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        response = await self._make_request('PUT', f"/users/{user_id}", data.dict(exclude_unset=True))
        return UserResponse(**response)

    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check if API is healthy."""
        return await self._make_request('GET', "/health/liveness")

    async def readiness_check(self) -> Dict[str, Any]:
        """Check if API is ready to serve traffic."""
        return await self._make_request('GET', "/health/readiness")


class BuildStateAPIError(Exception):
    """Custom exception for Build State API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        errors: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}

    def __str__(self):
        error_details = json.dumps(self.errors, indent=2)
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}\nDetails: {error_details}"
        return f"API Error: {self.message}\nDetails: {error_details}"


# Convenience functions for CLI usage
async def create_client_from_config(config_path: Optional[Path] = None) -> BuildStateClient:
    """
    Create client from configuration file or environment variables.

    Uses the Config class to load settings from:
    1. Environment variables
    2. Keyring (for API key)
    3. YAML config file
    """
    from .config import Config
    
    config = Config(config_path)
    
    api_url = config.api_url
    api_key = config.api_key
    jwt_token = config.jwt_token

    if not api_url:
        raise ValueError(
            "API URL not found. Run 'bldst config set-url <url>' to configure the API."
        )

    return BuildStateClient(
        base_url=api_url,
        api_key=api_key,
        jwt_token=jwt_token
    )