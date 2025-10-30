"""
Database migration utilities for the Slackbot application.

This module provides tools for:
- Database initialization and setup
- Schema migrations and updates
- Data migration utilities
- Database health checks and maintenance
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import asyncpg
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from database import DatabaseManager, Base, initialize_database_sync

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations and schema updates.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
        
    async def create_migration_table(self):
        """Create the migrations tracking table."""
        conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    checksum VARCHAR(64),
                    execution_time_ms INTEGER
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
                ON schema_migrations(version)
            """)
            logger.info("Migration tracking table created/verified")
        finally:
            await conn.close()
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
        try:
            rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
            return [row['version'] for row in rows]
        except Exception:
            # Migration table doesn't exist yet
            return []
        finally:
            await conn.close()
    
    async def apply_migration(self, version: str, name: str, sql: str) -> bool:
        """Apply a single migration."""
        conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
        try:
            start_time = datetime.now()
            
            # Execute migration in a transaction
            async with conn.transaction():
                await conn.execute(sql)
                
                # Record migration
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                await conn.execute("""
                    INSERT INTO schema_migrations (version, name, execution_time_ms)
                    VALUES ($1, $2, $3)
                """, version, name, execution_time)
            
            logger.info(f"Applied migration {version}: {name} ({execution_time}ms)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
        finally:
            await conn.close()
    
    async def rollback_migration(self, version: str) -> bool:
        """Rollback a migration (if rollback SQL is provided)."""
        # This would require storing rollback SQL in migration files
        # For now, this is a placeholder for future implementation
        logger.warning(f"Rollback not implemented for migration {version}")
        return False
    
    def generate_migration(self, name: str, up_sql: str, down_sql: str = "") -> str:
        """Generate a new migration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name}"
        filename = f"{version}.sql"
        filepath = self.migrations_dir / filename
        
        content = f"""-- Migration: {version}
-- Description: {name}
-- Created: {datetime.now().isoformat()}

-- UP Migration
{up_sql}

-- DOWN Migration (for rollbacks)
-- {down_sql if down_sql else 'No rollback provided'}
"""
        
        filepath.write_text(content)
        logger.info(f"Generated migration file: {filename}")
        return str(filepath)


class DatabaseInitializer:
    """
    Handles database initialization and setup.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    async def check_database_exists(self) -> bool:
        """Check if the database exists."""
        # Parse database URL to get connection info
        import urllib.parse
        parsed = urllib.parse.urlparse(self.database_url)
        db_name = parsed.path.lstrip('/')
        
        # Connect to postgres database to check if target database exists
        admin_url = self.database_url.replace(f"/{db_name}", "/postgres")
        admin_url = admin_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        try:
            conn = await asyncpg.connect(admin_url)
            try:
                result = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = $1", db_name
                )
                return result is not None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
            return False
    
    async def create_database(self) -> bool:
        """Create the database if it doesn't exist."""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.database_url)
        db_name = parsed.path.lstrip('/')
        
        admin_url = self.database_url.replace(f"/{db_name}", "/postgres")
        admin_url = admin_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        try:
            conn = await asyncpg.connect(admin_url)
            try:
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Created database: {db_name}")
                return True
            except asyncpg.DuplicateDatabaseError:
                logger.info(f"Database {db_name} already exists")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    async def initialize_schema(self) -> bool:
        """Initialize the database schema using SQLAlchemy."""
        try:
            db_manager = DatabaseManager(self.database_url)
            await db_manager.create_tables()
            await db_manager.close()
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            return False
    
    async def run_sql_file(self, sql_file_path: str) -> bool:
        """Run a SQL file against the database."""
        try:
            with open(sql_file_path, 'r') as f:
                sql_content = f.read()
            
            conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            try:
                await conn.execute(sql_content)
                logger.info(f"Successfully executed SQL file: {sql_file_path}")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error executing SQL file {sql_file_path}: {e}")
            return False
    
    async def seed_initial_data(self) -> bool:
        """Seed the database with initial data."""
        try:
            db_manager = DatabaseManager(self.database_url)
            
            async with db_manager.get_async_session() as session:
                # Add any initial data here
                # For example, default user mappings, system configurations, etc.
                
                # Example: Create a system user for automated tasks
                from database import UserMapping, AuditLog
                
                # Check if system user already exists
                existing_user = await session.execute(
                    text("SELECT id FROM user_mappings WHERE slack_user_id = 'SYSTEM'")
                )
                
                if not existing_user.first():
                    system_user = UserMapping(
                        slack_user_id="SYSTEM",
                        slack_team_id="SYSTEM",
                        slack_username="system",
                        slack_display_name="System User",
                        snowflake_username="SYSTEM_USER",
                        is_admin=True,
                        is_active=True
                    )
                    session.add(system_user)
                    
                    # Log the creation
                    audit_log = AuditLog(
                        event_type="system_user_created",
                        event_category="system",
                        event_description="System user created during database initialization",
                        slack_user_id="SYSTEM"
                    )
                    session.add(audit_log)
                    
                    logger.info("Created system user")
            
            await db_manager.close()
            return True
            
        except Exception as e:
            logger.error(f"Error seeding initial data: {e}")
            return False


class DatabaseHealthChecker:
    """
    Performs database health checks and maintenance.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check database connection and basic health."""
        result = {
            'status': 'unknown',
            'connection': False,
            'tables_exist': False,
            'migration_table_exists': False,
            'error': None,
            'response_time_ms': None
        }
        
        start_time = datetime.now()
        
        try:
            conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            try:
                # Test basic connection
                await conn.fetchval("SELECT 1")
                result['connection'] = True
                
                # Check if main tables exist
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('user_sessions', 'query_history', 'user_mappings', 'query_cache', 'audit_logs')
                """)
                result['tables_exist'] = len(tables) == 5
                
                # Check if migration table exists
                migration_table = await conn.fetchval("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'schema_migrations'
                """)
                result['migration_table_exists'] = migration_table is not None
                
                result['status'] = 'healthy'
                
            finally:
                await conn.close()
                
        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'unhealthy'
        
        result['response_time_ms'] = int((datetime.now() - start_time).total_seconds() * 1000)
        return result
    
    async def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about database tables."""
        try:
            conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            try:
                stats = {}
                
                # Get row counts for each table
                tables = ['user_sessions', 'query_history', 'user_mappings', 'query_cache', 'audit_logs']
                for table in tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = {'row_count': count}
                
                # Get active sessions count
                active_sessions = await conn.fetchval(
                    "SELECT COUNT(*) FROM user_sessions WHERE is_active = TRUE"
                )
                stats['active_sessions'] = active_sessions
                
                # Get recent query count (last 24 hours)
                recent_queries = await conn.fetchval("""
                    SELECT COUNT(*) FROM query_history 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                stats['recent_queries_24h'] = recent_queries
                
                # Get cache hit rate
                cache_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(hit_count) as total_hits,
                        COUNT(CASE WHEN is_valid = TRUE AND expires_at > NOW() THEN 1 END) as valid_entries
                    FROM query_cache
                """)
                stats['cache'] = dict(cache_stats) if cache_stats else {}
                
                return stats
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data from the database."""
        cleanup_stats = {}
        
        try:
            conn = await asyncpg.connect(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            try:
                # Clean up expired sessions
                expired_sessions = await conn.execute("""
                    UPDATE user_sessions SET is_active = FALSE 
                    WHERE is_active = TRUE 
                    AND last_activity < NOW() - INTERVAL '%s days'
                """ % days)
                cleanup_stats['expired_sessions'] = expired_sessions
                
                # Clean up expired cache
                expired_cache = await conn.execute("""
                    DELETE FROM query_cache 
                    WHERE expires_at < NOW() OR is_valid = FALSE
                """)
                cleanup_stats['expired_cache'] = expired_cache
                
                # Archive old audit logs (keep errors and critical events)
                archived_logs = await conn.execute("""
                    DELETE FROM audit_logs 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    AND event_severity NOT IN ('error', 'critical')
                """ % (days * 3))  # Keep audit logs 3x longer
                cleanup_stats['archived_logs'] = archived_logs
                
                logger.info(f"Cleanup completed: {cleanup_stats}")
                return cleanup_stats
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return cleanup_stats


# CLI Commands
async def init_database(database_url: str, run_schema_file: bool = True):
    """Initialize a new database."""
    print("🚀 Initializing Slackbot database...")
    
    initializer = DatabaseInitializer(database_url)
    
    # Check and create database
    if not await initializer.check_database_exists():
        print("📦 Creating database...")
        if not await initializer.create_database():
            print("❌ Failed to create database")
            return False
    
    # Initialize schema
    if run_schema_file:
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            print("📋 Running schema.sql...")
            if not await initializer.run_sql_file(str(schema_file)):
                print("❌ Failed to run schema file")
                return False
        else:
            print("📋 Creating tables with SQLAlchemy...")
            if not await initializer.initialize_schema():
                print("❌ Failed to initialize schema")
                return False
    else:
        print("📋 Creating tables with SQLAlchemy...")
        if not await initializer.initialize_schema():
            print("❌ Failed to initialize schema")
            return False
    
    # Seed initial data
    print("🌱 Seeding initial data...")
    if not await initializer.seed_initial_data():
        print("⚠️  Warning: Failed to seed initial data")
    
    # Setup migration tracking
    migration_manager = MigrationManager(database_url)
    await migration_manager.create_migration_table()
    
    print("✅ Database initialization completed successfully!")
    return True


async def check_health(database_url: str):
    """Check database health."""
    print("🔍 Checking database health...")
    
    checker = DatabaseHealthChecker(database_url)
    
    # Basic health check
    health = await checker.check_connection()
    print(f"Connection: {'✅' if health['connection'] else '❌'}")
    print(f"Tables exist: {'✅' if health['tables_exist'] else '❌'}")
    print(f"Migration table: {'✅' if health['migration_table_exists'] else '❌'}")
    print(f"Response time: {health['response_time_ms']}ms")
    
    if health['error']:
        print(f"❌ Error: {health['error']}")
        return False
    
    # Get table statistics
    stats = await checker.get_table_stats()
    if stats:
        print("\n📊 Table Statistics:")
        for table, data in stats.items():
            if isinstance(data, dict) and 'row_count' in data:
                print(f"  {table}: {data['row_count']} rows")
            elif isinstance(data, (int, float)):
                print(f"  {table}: {data}")
    
    print(f"\n✅ Database is {health['status']}")
    return health['status'] == 'healthy'


async def cleanup_database(database_url: str, days: int = 30):
    """Clean up old database records."""
    print(f"🧹 Cleaning up records older than {days} days...")
    
    checker = DatabaseHealthChecker(database_url)
    stats = await checker.cleanup_old_data(days)
    
    print("Cleanup results:")
    for operation, count in stats.items():
        print(f"  {operation}: {count} records")
    
    print("✅ Cleanup completed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python migrations.py init <database_url>")
        print("  python migrations.py health <database_url>")
        print("  python migrations.py cleanup <database_url> [days]")
        sys.exit(1)
    
    command = sys.argv[1]
    database_url = sys.argv[2]
    
    if command == "init":
        asyncio.run(init_database(database_url))
    elif command == "health":
        asyncio.run(check_health(database_url))
    elif command == "cleanup":
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        asyncio.run(cleanup_database(database_url, days))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
