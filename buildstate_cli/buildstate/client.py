"""
HTTP client for Build State API.

This client provides a clean, async interface to the Build State API
with automatic authentication, error handling, and response parsing.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from .models import (
    BuildCreate, BuildResponse, StateTransition, StateResponse,
    FailureRecord, DashboardSummary, TokenRequest, TokenResponse, APIError,
    UserCreate, UserUpdate, UserResponse, UserProfileResponse,
    APITokenCreate, APITokenResponse, APITokenCreateResponse, IDMLoginRequest
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
            headers=self._get_default_headers()
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
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"

        try:
            if data:
                response = await self.client.request(method, url, json=data, params=params)
            else:
                response = await self.client.request(method, url, params=params)

            # Handle different response status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 204:
                return {}
            elif response.status_code in (400, 401, 403, 404, 422):
                error_data = response.json()
                if 'detail' in error_data:
                    raise BuildStateAPIError(
                        error_data['detail'],
                        status_code=response.status_code,
                        errors=error_data.get('errors')
                    )
                else:
                    raise BuildStateAPIError(
                        f"API error: {response.text}",
                        status_code=response.status_code
                    )
            else:
                raise BuildStateAPIError(
                    f"Unexpected status code: {response.status_code}",
                    status_code=response.status_code
                )

        except httpx.TimeoutException:
            raise BuildStateAPIError("Request timeout")
        except httpx.ConnectError:
            raise BuildStateAPIError(f"Connection failed to {url}")
        except json.JSONDecodeError:
            raise BuildStateAPIError("Invalid JSON response from API")

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
        response = await self._make_request('POST', '/token', request.dict())
        return TokenResponse(**response)

    # Build methods
    async def create_build(self, build: BuildCreate) -> str:
        """Create a new build."""
        response = await self._make_request('POST', '/builds', build.dict())
        return response['id']

    async def get_build(self, build_id: str) -> BuildResponse:
        """Get build details."""
        response = await self._make_request('GET', f'/builds/{build_id}')
        return BuildResponse(**response)

    async def list_builds_by_platform(self, platform: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List builds for a specific platform."""
        response = await self._make_request(
            'GET',
            f'/dashboard/platform/{platform}',
            params={'limit': limit}
        )
        return response.get('builds', [])

    # State methods
    async def transition_state(self, build_id: str, transition: StateTransition) -> None:
        """Transition build to new state."""
        await self._make_request(
            'POST',
            f'/builds/{build_id}/state',
            transition.dict()
        )

    async def get_current_state(self, build_id: str) -> StateResponse:
        """Get current state of a build."""
        response = await self._make_request('GET', f'/builds/{build_id}/state')
        return StateResponse(**response)

    # Failure methods
    async def record_failure(self, build_id: str, failure: FailureRecord) -> None:
        """Record a build failure."""
        await self._make_request(
            'POST',
            f'/builds/{build_id}/failure',
            failure.dict()
        )

    # Dashboard methods
    async def get_dashboard_summary(self) -> DashboardSummary:
        """Get dashboard summary."""
        response = await self._make_request('GET', '/dashboard/summary')
        return DashboardSummary(**response)

    async def get_recent_builds(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent builds."""
        response = await self._make_request('GET', '/dashboard/recent')
        return response.get('recent_builds', [])

    # Health check
    async def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    # User management methods
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        employee_id: Optional[str] = None,
        is_superuser: bool = False
    ) -> str:
        """Create a new user."""
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            employee_id=employee_id,
            is_superuser=is_superuser
        )
        response = await self._make_request('POST', '/users', user_data.dict())
        return response['id']

    async def get_user(self, user_id: str) -> UserResponse:
        """Get user details."""
        response = await self._make_request('GET', f'/users/{user_id}')
        return UserResponse(**response)

    async def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        employee_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None
    ) -> None:
        """Update user details."""
        update_data = UserUpdate(
            email=email,
            first_name=first_name,
            last_name=last_name,
            employee_id=employee_id,
            is_active=is_active,
            is_superuser=is_superuser
        )
        await self._make_request('PUT', f'/users/{user_id}', update_data.dict())

    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """Get user profile."""
        response = await self._make_request('GET', f'/users/{user_id}/profile')
        return UserProfileResponse(**response)

    # API Token methods
    async def create_api_token(
        self,
        user_id: str,
        name: str,
        scopes: list[str],
        expires_at: Optional[str] = None
    ) -> APITokenCreateResponse:
        """Create API token for user."""
        token_data = APITokenCreate(
            name=name,
            scopes=scopes,
            expires_at=expires_at
        )
        response = await self._make_request('POST', f'/users/{user_id}/tokens', token_data.dict())
        return APITokenCreateResponse(**response)

    async def get_api_tokens(self, user_id: str) -> list[APITokenResponse]:
        """Get API tokens for user."""
        response = await self._make_request('GET', f'/users/{user_id}/tokens')
        return [APITokenResponse(**token) for token in response.get('tokens', [])]

    async def revoke_api_token(self, token_id: str, user_id: str) -> None:
        """Revoke API token."""
        await self._make_request('DELETE', f'/users/{user_id}/tokens/{token_id}')

    # IDM Authentication
    async def idm_login(self, username: str, idm_token: str) -> TokenResponse:
        """Authenticate with IDM token."""
        request = IDMLoginRequest(username=username, idm_token=idm_token)
        response = await self._make_request('POST', '/auth/idm', request.dict())
        return TokenResponse(**response)


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
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


# Convenience functions for CLI usage
async def create_client_from_config(config_path: Optional[Path] = None) -> BuildStateClient:
    """
    Create client from configuration file or environment variables.

    Looks for configuration in this order:
    1. Explicit config_path
    2. .buildctl.yaml in current directory
    3. Environment variables
    """
    config = {}

    # Try to load from config file
    if config_path and config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    elif Path('.buildctl.yaml').exists():
        import yaml
        with open('.buildctl.yaml') as f:
            config = yaml.safe_load(f) or {}
    elif (Path.home() / '.buildctl.yaml').exists():
        import yaml
        with open(Path.home() / '.buildctl.yaml') as f:
            config = yaml.safe_load(f) or {}

    # Override with environment variables
    api_url = config.get('api_url') or os.getenv('BUILDCTL_API_URL')
    api_key = config.get('api_key') or os.getenv('BUILDCTL_API_KEY')
    jwt_token = config.get('jwt_token') or os.getenv('BUILDCTL_JWT_TOKEN')

    if not api_url:
        raise ValueError(
            "API URL not found. Set BUILDCTL_API_URL environment variable "
            "or add 'api_url' to .buildctl.yaml"
        )

    return BuildStateClient(
        base_url=api_url,
        api_key=api_key,
        jwt_token=jwt_token
    )


# Import os here to avoid circular imports
import os