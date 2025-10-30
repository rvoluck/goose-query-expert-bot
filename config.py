"""
Configuration management for Goose Slackbot
Handles environment variables and application settings
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ================================
    # SLACK CONFIGURATION
    # ================================
    # Socket Mode (optional - for internal deployment)
    slack_bot_token: Optional[str] = Field(None, env="SLACK_BOT_TOKEN")
    slack_app_token: Optional[str] = Field(None, env="SLACK_APP_TOKEN")
    
    # OAuth (for public distribution)
    slack_client_id: Optional[str] = Field(None, env="SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = Field(None, env="SLACK_CLIENT_SECRET")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    slack_app_id: Optional[str] = Field(None, env="SLACK_APP_ID")
    slack_admin_channel: Optional[str] = Field(None, env="SLACK_ADMIN_CHANNEL")
    
    # ================================
    # GOOSE INTEGRATION
    # ================================
    goose_mcp_server_url: str = Field("http://localhost:8000", env="GOOSE_MCP_SERVER_URL")
    goose_mcp_timeout: int = Field(300, env="GOOSE_MCP_TIMEOUT")
    goose_max_concurrent_queries: int = Field(10, env="GOOSE_MAX_CONCURRENT_QUERIES")
    goose_executable_path: Optional[str] = Field(None, env="GOOSE_EXECUTABLE_PATH")
    
    # ================================
    # DATABASE CONFIGURATION
    # ================================
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    redis_session_ttl: int = Field(3600, env="REDIS_SESSION_TTL")
    redis_cache_ttl: int = Field(1800, env="REDIS_CACHE_TTL")
    
    # ================================
    # SECURITY CONFIGURATION
    # ================================
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    rate_limit_per_user_per_minute: int = Field(10, env="RATE_LIMIT_PER_USER_PER_MINUTE")
    rate_limit_global_per_minute: int = Field(100, env="RATE_LIMIT_GLOBAL_PER_MINUTE")
    
    # ================================
    # USER AUTHENTICATION
    # ================================
    ldap_server: Optional[str] = Field(None, env="LDAP_SERVER")
    ldap_base_dn: Optional[str] = Field(None, env="LDAP_BASE_DN")
    ldap_bind_user: Optional[str] = Field(None, env="LDAP_BIND_USER")
    ldap_bind_password: Optional[str] = Field(None, env="LDAP_BIND_PASSWORD")
    
    user_mapping_service_url: Optional[str] = Field(None, env="USER_MAPPING_SERVICE_URL")
    user_mapping_api_key: Optional[str] = Field(None, env="USER_MAPPING_API_KEY")
    
    # ================================
    # LOGGING AND MONITORING
    # ================================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # ================================
    # APPLICATION CONFIGURATION
    # ================================
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(3000, env="PORT")
    workers: int = Field(4, env="WORKERS")
    
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("production", env="ENVIRONMENT")
    
    max_result_rows: int = Field(10000, env="MAX_RESULT_ROWS")
    max_inline_rows: int = Field(10, env="MAX_INLINE_ROWS")
    query_timeout_seconds: int = Field(300, env="QUERY_TIMEOUT_SECONDS")
    
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    allowed_file_types: List[str] = Field(["csv", "xlsx", "json"], env="ALLOWED_FILE_TYPES")
    
    # ================================
    # SNOWFLAKE CONFIGURATION
    # ================================
    snowflake_account: Optional[str] = Field(None, env="SNOWFLAKE_ACCOUNT")
    snowflake_warehouse: str = Field("COMPUTE_WH", env="SNOWFLAKE_WAREHOUSE")
    snowflake_database: str = Field("ANALYTICS", env="SNOWFLAKE_DATABASE")
    snowflake_schema: str = Field("PUBLIC", env="SNOWFLAKE_SCHEMA")
    
    # ================================
    # FEATURE FLAGS
    # ================================
    enable_query_history: bool = Field(True, env="ENABLE_QUERY_HISTORY")
    enable_query_sharing: bool = Field(True, env="ENABLE_QUERY_SHARING")
    enable_interactive_buttons: bool = Field(True, env="ENABLE_INTERACTIVE_BUTTONS")
    enable_file_uploads: bool = Field(True, env="ENABLE_FILE_UPLOADS")
    enable_thread_management: bool = Field(True, env="ENABLE_THREAD_MANAGEMENT")
    enable_user_permissions: bool = Field(True, env="ENABLE_USER_PERMISSIONS")
    
    # ================================
    # DEVELOPMENT SETTINGS
    # ================================
    mock_mode: bool = Field(False, env="MOCK_MODE")
    mock_delay_seconds: int = Field(2, env="MOCK_DELAY_SECONDS")
    auto_reload: bool = Field(False, env="AUTO_RELOAD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("allowed_file_types", pre=True)
    def parse_file_types(cls, v):
        """Parse comma-separated file types"""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of: {valid_envs}")
        return v.lower()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development" or self.debug
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    def get_database_config(self) -> dict:
        """Get database configuration for connection pool"""
        return {
            "dsn": self.database_url,
            "min_size": 1,
            "max_size": self.database_pool_size,
            "max_queries": 50000,
            "max_inactive_connection_lifetime": 300,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration"""
        return {
            "url": self.redis_url,
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
        }
    
    def get_goose_config(self) -> dict:
        """Get Goose integration configuration"""
        return {
            "mcp_server_url": self.goose_mcp_server_url,
            "timeout": self.goose_mcp_timeout,
            "max_concurrent_queries": self.goose_max_concurrent_queries,
            "executable_path": self.goose_executable_path,
            "snowflake": {
                "account": self.snowflake_account,
                "warehouse": self.snowflake_warehouse,
                "database": self.snowflake_database,
                "schema": self.snowflake_schema,
            }
        }
    
    def get_slack_config(self) -> dict:
        """Get Slack configuration"""
        return {
            "bot_token": self.slack_bot_token,
            "app_token": self.slack_app_token,
            "signing_secret": self.slack_signing_secret,
            "admin_channel": self.slack_admin_channel,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def load_settings_from_file(file_path: str) -> Settings:
    """Load settings from a specific file"""
    return Settings(_env_file=file_path)


def validate_required_settings():
    """Validate that all required settings are present"""
    required_fields = [
        "slack_bot_token",
        "slack_app_token", 
        "slack_signing_secret",
        "database_url",
        "jwt_secret_key",
        "encryption_key",
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field):
            missing_fields.append(field.upper())
    
    if missing_fields:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_fields)}\n"
            f"Please check your .env file or environment configuration."
        )


def setup_logging():
    """Setup logging configuration based on settings"""
    import logging
    import structlog
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(message)s" if settings.log_format == "json" else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


if __name__ == "__main__":
    # Test configuration loading
    try:
        validate_required_settings()
        print("✅ Configuration loaded successfully")
        print(f"Environment: {settings.environment}")
        print(f"Debug mode: {settings.debug}")
        print(f"Mock mode: {settings.mock_mode}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
