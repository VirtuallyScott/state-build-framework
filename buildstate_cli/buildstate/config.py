"""
Configuration management for BuildState CLI.

Handles API URL, authentication, and other settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import keyring


class Config:
    """Configuration manager for BuildState CLI."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path.home() / '.buildctl.yaml'
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

    def _save_config(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    @property
    def api_url(self) -> Optional[str]:
        """Get API URL."""
        return (
            self._config.get('api_url') or
            os.getenv('BUILDCTL_API_URL')
        )

    @api_url.setter
    def api_url(self, value: str):
        """Set API URL."""
        self._config['api_url'] = value
        self._save_config()

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from config or keyring."""
        # Try environment variable first
        env_key = os.getenv('BUILDCTL_API_KEY')
        if env_key:
            return env_key

        # Try keyring (secure storage)
        keyring_key = keyring.get_password('buildstate_cli', 'api_key')
        if keyring_key:
            return keyring_key

        # Try config file (not recommended for production)
        return self._config.get('api_key')

    def set_api_key(self, api_key: str, use_keyring: bool = True):
        """Set API key."""
        if use_keyring:
            keyring.set_password('buildstate_cli', 'api_key', api_key)
            # Remove from config file if it was there
            self._config.pop('api_key', None)
        else:
            self._config['api_key'] = api_key
            # Remove from keyring if it was there
            try:
                keyring.delete_password('buildstate_cli', 'api_key')
            except Exception:
                pass
        self._save_config()

    def clear_api_key(self):
        """Clear stored API key."""
        # Remove from keyring
        try:
            keyring.delete_password('buildstate_cli', 'api_key')
        except Exception:
            pass

        # Remove from config
        self._config.pop('api_key', None)
        self._save_config()

    @property
    def jwt_token(self) -> Optional[str]:
        """Get JWT token."""
        return (
            self._config.get('jwt_token') or
            os.getenv('BUILDCTL_JWT_TOKEN')
        )

    @jwt_token.setter
    def jwt_token(self, value: str):
        """Set JWT token."""
        self._config['jwt_token'] = value
        self._save_config()

    def clear_jwt_token(self):
        """Clear stored JWT token."""
        self._config.pop('jwt_token', None)
        self._save_config()

    @property
    def default_platform(self) -> Optional[str]:
        """Get default platform."""
        return self._config.get('default_platform')

    @default_platform.setter
    def default_platform(self, value: str):
        """Set default platform."""
        self._config['default_platform'] = value
        self._save_config()

    @property
    def default_os_version(self) -> Optional[str]:
        """Get default OS version."""
        return self._config.get('default_os_version')

    @default_os_version.setter
    def default_os_version(self, value: str):
        """Set default OS version."""
        self._config['default_os_version'] = value
        self._save_config()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return {
            'api_url': self.api_url,
            'has_api_key': bool(self.api_key),
            'has_jwt_token': bool(self.jwt_token),
            'default_platform': self.default_platform,
            'default_os_version': self.default_os_version,
            'config_file': str(self.config_file),
        }

    def reset(self):
        """Reset all configuration."""
        self.clear_api_key()
        self.clear_jwt_token()
        self._config = {}
        self._save_config()


# Global config instance
config = Config()