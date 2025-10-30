"""
Unit tests for configuration management
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from config import Settings, get_settings, validate_required_settings


class TestSettings:
    """Test Settings class"""
    
    def test_settings_with_valid_env(self, monkeypatch):
        """Test settings loading with valid environment variables"""
        # Set required environment variables
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        
        settings = Settings()
        
        assert settings.slack_bot_token == "xoxb-test-token"
        assert settings.slack_app_token == "xapp-test-token"
        assert settings.database_url == "postgresql://localhost/test"
    
    def test_settings_with_defaults(self, monkeypatch):
        """Test settings with default values"""
        # Set only required fields
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        
        settings = Settings()
        
        # Check defaults
        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.port == 3000
        assert settings.workers == 4
    
    def test_settings_validation_log_level(self, monkeypatch):
        """Test log level validation"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        with pytest.raises(ValidationError):
            Settings()
    
    def test_settings_validation_environment(self, monkeypatch):
        """Test environment validation"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("ENVIRONMENT", "invalid")
        
        with pytest.raises(ValidationError):
            Settings()
    
    def test_is_development_property(self, monkeypatch):
        """Test is_development property"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False
    
    def test_is_production_property(self, monkeypatch):
        """Test is_production property"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        settings = Settings()
        assert settings.is_production is True
        assert settings.is_development is False
    
    def test_get_database_config(self, monkeypatch):
        """Test database configuration getter"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("DATABASE_POOL_SIZE", "20")
        
        settings = Settings()
        db_config = settings.get_database_config()
        
        assert db_config["dsn"] == "postgresql://localhost/test"
        assert db_config["max_size"] == 20
        assert "min_size" in db_config
    
    def test_get_redis_config(self, monkeypatch):
        """Test Redis configuration getter"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
        
        settings = Settings()
        redis_config = settings.get_redis_config()
        
        assert redis_config["url"] == "redis://localhost:6379/1"
        assert redis_config["encoding"] == "utf-8"
        assert redis_config["decode_responses"] is True
    
    def test_get_goose_config(self, monkeypatch):
        """Test Goose configuration getter"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("GOOSE_MCP_SERVER_URL", "http://goose:8000")
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-account")
        
        settings = Settings()
        goose_config = settings.get_goose_config()
        
        assert goose_config["mcp_server_url"] == "http://goose:8000"
        assert goose_config["snowflake"]["account"] == "test-account"
    
    def test_get_slack_config(self, monkeypatch):
        """Test Slack configuration getter"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("SLACK_ADMIN_CHANNEL", "C123456789")
        
        settings = Settings()
        slack_config = settings.get_slack_config()
        
        assert slack_config["bot_token"] == "xoxb-test-token"
        assert slack_config["app_token"] == "xapp-test-token"
        assert slack_config["signing_secret"] == "test-secret"
        assert slack_config["admin_channel"] == "C123456789"
    
    def test_parse_file_types(self, monkeypatch):
        """Test file types parsing"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        monkeypatch.setenv("ALLOWED_FILE_TYPES", "csv,xlsx,json,parquet")
        
        settings = Settings()
        
        assert settings.allowed_file_types == ["csv", "xlsx", "json", "parquet"]


class TestValidateRequiredSettings:
    """Test validate_required_settings function"""
    
    def test_validate_with_all_required_fields(self, monkeypatch):
        """Test validation with all required fields present"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
        
        # Should not raise an exception
        validate_required_settings()
    
    def test_validate_with_missing_fields(self, monkeypatch):
        """Test validation with missing required fields"""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        # Missing other required fields
        
        with pytest.raises(ValueError) as exc_info:
            Settings()
        
        assert "field required" in str(exc_info.value).lower()


class TestGetSettings:
    """Test get_settings function"""
    
    def test_get_settings_returns_singleton(self):
        """Test that get_settings returns the same instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
