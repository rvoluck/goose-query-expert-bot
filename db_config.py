"""
Database configuration and connection management for the Slackbot application.

This module provides:
- Environment-based configuration
- Connection string management
- Database pool configuration
- Health monitoring settings
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    
    # Connection settings
    host: str = "localhost"
    port: int = 5432
    database: str = "slackbot_db"
    username: str = "slackbot_user"
    password: str = ""
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600  # 1 hour
    pool_timeout: int = 30
    
    # Query settings
    query_timeout: int = 300  # 5 minutes
    statement_timeout: int = 600  # 10 minutes
    
    # Async settings
    async_driver: str = "postgresql+asyncpg"
    sync_driver: str = "postgresql"
    
    # SSL settings
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    
    # Logging and debugging
    echo_sql: bool = False
    log_level: str = "INFO"
    
    # Cache settings
    cache_ttl_seconds: int = 3600  # 1 hour default cache TTL
    max_cache_entries: int = 1000
    
    # Session settings
    session_timeout_hours: int = 24
    inactive_session_cleanup_hours: int = 48
    
    # Maintenance settings
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24
    audit_log_retention_days: int = 90
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            # Connection settings
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'slackbot_db'),
            username=os.getenv('DB_USER', 'slackbot_user'),
            password=os.getenv('DB_PASSWORD', ''),
            
            # Pool settings
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_pre_ping=os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true',
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            
            # Query settings
            query_timeout=int(os.getenv('DB_QUERY_TIMEOUT', '300')),
            statement_timeout=int(os.getenv('DB_STATEMENT_TIMEOUT', '600')),
            
            # SSL settings
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer'),
            ssl_cert=os.getenv('DB_SSL_CERT'),
            ssl_key=os.getenv('DB_SSL_KEY'),
            ssl_ca=os.getenv('DB_SSL_CA'),
            
            # Logging
            echo_sql=os.getenv('DB_ECHO_SQL', 'false').lower() == 'true',
            log_level=os.getenv('DB_LOG_LEVEL', 'INFO'),
            
            # Cache settings
            cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '3600')),
            max_cache_entries=int(os.getenv('MAX_CACHE_ENTRIES', '1000')),
            
            # Session settings
            session_timeout_hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '24')),
            inactive_session_cleanup_hours=int(os.getenv('INACTIVE_SESSION_CLEANUP_HOURS', '48')),
            
            # Maintenance settings
            auto_cleanup_enabled=os.getenv('AUTO_CLEANUP_ENABLED', 'true').lower() == 'true',
            cleanup_interval_hours=int(os.getenv('CLEANUP_INTERVAL_HOURS', '24')),
            audit_log_retention_days=int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '90')),
        )
    
    @classmethod
    def from_url(cls, database_url: str) -> 'DatabaseConfig':
        """Create configuration from database URL."""
        parsed = urlparse(database_url)
        
        config = cls.from_env()
        config.host = parsed.hostname or 'localhost'
        config.port = parsed.port or 5432
        config.database = parsed.path.lstrip('/') if parsed.path else 'slackbot_db'
        config.username = parsed.username or 'slackbot_user'
        config.password = parsed.password or ''
        
        return config
    
    def get_async_url(self) -> str:
        """Get async database URL."""
        return self._build_url(self.async_driver)
    
    def get_sync_url(self) -> str:
        """Get sync database URL."""
        return self._build_url(self.sync_driver)
    
    def _build_url(self, driver: str) -> str:
        """Build database URL with the specified driver."""
        # Build base URL
        if self.password:
            auth = f"{self.username}:{self.password}"
        else:
            auth = self.username
        
        url = f"{driver}://{auth}@{self.host}:{self.port}/{self.database}"
        
        # Add SSL parameters if configured
        params = []
        if self.ssl_mode != "prefer":
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            params.append(f"sslrootcert={self.ssl_ca}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def get_sqlalchemy_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_pre_ping': self.pool_pre_ping,
            'pool_recycle': self.pool_recycle,
            'pool_timeout': self.pool_timeout,
            'echo': self.echo_sql,
            'connect_args': {
                'statement_timeout': self.statement_timeout * 1000,  # Convert to milliseconds
                'command_timeout': self.query_timeout,
            }
        }
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        if not self.host:
            errors.append("Database host is required")
        
        if not self.database:
            errors.append("Database name is required")
        
        if not self.username:
            errors.append("Database username is required")
        
        if self.port < 1 or self.port > 65535:
            errors.append("Database port must be between 1 and 65535")
        
        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")
        
        if self.max_overflow < 0:
            errors.append("Max overflow cannot be negative")
        
        if self.query_timeout < 1:
            errors.append("Query timeout must be at least 1 second")
        
        if errors:
            raise ValueError("Configuration validation failed: " + "; ".join(errors))
        
        return True


class EnvironmentConfig:
    """Environment-specific database configurations."""
    
    @staticmethod
    def development() -> DatabaseConfig:
        """Development environment configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="slackbot_dev",
            username="dev_user",
            password="dev_password",
            pool_size=5,
            max_overflow=10,
            echo_sql=True,
            log_level="DEBUG",
            ssl_mode="disable",
        )
    
    @staticmethod
    def testing() -> DatabaseConfig:
        """Testing environment configuration."""
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="slackbot_test",
            username="test_user",
            password="test_password",
            pool_size=2,
            max_overflow=5,
            echo_sql=False,
            log_level="WARNING",
            ssl_mode="disable",
            cache_ttl_seconds=60,  # Shorter cache for testing
        )
    
    @staticmethod
    def staging() -> DatabaseConfig:
        """Staging environment configuration."""
        return DatabaseConfig(
            host=os.getenv('STAGING_DB_HOST', 'staging-db.example.com'),
            port=int(os.getenv('STAGING_DB_PORT', '5432')),
            database=os.getenv('STAGING_DB_NAME', 'slackbot_staging'),
            username=os.getenv('STAGING_DB_USER', 'staging_user'),
            password=os.getenv('STAGING_DB_PASSWORD', ''),
            pool_size=8,
            max_overflow=15,
            echo_sql=False,
            log_level="INFO",
            ssl_mode="require",
        )
    
    @staticmethod
    def production() -> DatabaseConfig:
        """Production environment configuration."""
        return DatabaseConfig(
            host=os.getenv('PROD_DB_HOST', 'prod-db.example.com'),
            port=int(os.getenv('PROD_DB_PORT', '5432')),
            database=os.getenv('PROD_DB_NAME', 'slackbot_prod'),
            username=os.getenv('PROD_DB_USER', 'prod_user'),
            password=os.getenv('PROD_DB_PASSWORD', ''),
            pool_size=20,
            max_overflow=30,
            echo_sql=False,
            log_level="WARNING",
            ssl_mode="verify-full",
            ssl_ca=os.getenv('PROD_DB_SSL_CA'),
            pool_recycle=1800,  # 30 minutes for production
            query_timeout=180,  # 3 minutes for production
        )


def get_database_config(environment: Optional[str] = None) -> DatabaseConfig:
    """
    Get database configuration based on environment.
    
    Args:
        environment: Environment name (development, testing, staging, production)
                    If None, uses DATABASE_URL or defaults to from_env()
    
    Returns:
        DatabaseConfig instance
    """
    # If DATABASE_URL is provided, use it
    database_url = os.getenv('DATABASE_URL')
    if database_url and not environment:
        return DatabaseConfig.from_url(database_url)
    
    # Use environment-specific config if specified
    if environment:
        env_configs = {
            'development': EnvironmentConfig.development,
            'dev': EnvironmentConfig.development,
            'testing': EnvironmentConfig.testing,
            'test': EnvironmentConfig.testing,
            'staging': EnvironmentConfig.staging,
            'stage': EnvironmentConfig.staging,
            'production': EnvironmentConfig.production,
            'prod': EnvironmentConfig.production,
        }
        
        if environment.lower() in env_configs:
            return env_configs[environment.lower()]()
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    # Default to environment variables
    return DatabaseConfig.from_env()


# Connection string templates for different scenarios
CONNECTION_TEMPLATES = {
    'local_development': 'postgresql+asyncpg://dev_user:dev_password@localhost:5432/slackbot_dev',
    'docker_compose': 'postgresql+asyncpg://slackbot:slackbot_password@db:5432/slackbot_db',
    'heroku': 'postgresql+asyncpg://user:password@host:5432/database?sslmode=require',
    'aws_rds': 'postgresql+asyncpg://user:password@rds-instance.region.rds.amazonaws.com:5432/slackbot?sslmode=require',
    'google_cloud_sql': 'postgresql+asyncpg://user:password@/slackbot?host=/cloudsql/project:region:instance',
}


def create_database_url(template: str, **kwargs) -> str:
    """
    Create a database URL from a template with parameter substitution.
    
    Args:
        template: Template name or URL pattern
        **kwargs: Parameters to substitute in the template
    
    Returns:
        Complete database URL
    """
    if template in CONNECTION_TEMPLATES:
        url_template = CONNECTION_TEMPLATES[template]
    else:
        url_template = template
    
    try:
        return url_template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required parameter for database URL: {e}")


# Example usage and configuration validation
if __name__ == "__main__":
    import json
    
    print("=== Database Configuration Examples ===\n")
    
    # Show different environment configurations
    environments = ['development', 'testing', 'staging', 'production']
    
    for env in environments:
        print(f"--- {env.upper()} Configuration ---")
        config = get_database_config(env)
        print(f"Async URL: {config.get_async_url()}")
        print(f"Sync URL: {config.get_sync_url()}")
        print(f"Pool Size: {config.pool_size}")
        print(f"SSL Mode: {config.ssl_mode}")
        print(f"Echo SQL: {config.echo_sql}")
        print()
    
    # Show configuration from environment variables
    print("--- Environment Variables Configuration ---")
    env_config = DatabaseConfig.from_env()
    print(f"Host: {env_config.host}")
    print(f"Database: {env_config.database}")
    print(f"Pool Size: {env_config.pool_size}")
    print()
    
    # Show SQLAlchemy configuration
    print("--- SQLAlchemy Engine Configuration ---")
    sqlalchemy_config = env_config.get_sqlalchemy_config()
    print(json.dumps(sqlalchemy_config, indent=2))
    print()
    
    # Validate configuration
    try:
        env_config.validate()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
    
    # Show connection templates
    print("\n--- Connection Templates ---")
    for name, template in CONNECTION_TEMPLATES.items():
        print(f"{name}: {template}")
