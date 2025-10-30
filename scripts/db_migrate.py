#!/usr/bin/env python3
"""
Database migration management script
Handles schema migrations, rollbacks, and version tracking
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import hashlib

import asyncpg
import structlog

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class Migration:
    """Represents a database migration"""
    
    def __init__(self, version: str, name: str, up_sql: str, down_sql: str):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum of migration SQL"""
        content = f"{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
    
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(self.database_url)
        logger.info("Connected to database")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def initialize(self):
        """Initialize migration tracking table"""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW(),
                execution_time FLOAT,
                success BOOLEAN DEFAULT true
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied 
            ON schema_migrations(applied_at)
        """)
        
        logger.info("Migration tracking initialized")
    
    async def get_current_version(self) -> Optional[str]:
        """Get current database version"""
        result = await self.conn.fetchval("""
            SELECT version FROM schema_migrations 
            WHERE success = true 
            ORDER BY applied_at DESC 
            LIMIT 1
        """)
        return result
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        results = await self.conn.fetch("""
            SELECT version FROM schema_migrations 
            WHERE success = true 
            ORDER BY version
        """)
        return [row["version"] for row in results]
    
    def load_migrations(self) -> List[Migration]:
        """Load all migration files"""
        migrations = []
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            # Parse filename: V001__initial_schema.sql
            filename = file_path.stem
            parts = filename.split("__", 1)
            
            if len(parts) != 2:
                logger.warning(f"Skipping invalid migration file: {filename}")
                continue
            
            version = parts[0]
            name = parts[1].replace("_", " ")
            
            # Read SQL content
            content = file_path.read_text()
            
            # Split into up and down migrations
            if "-- DOWN" in content:
                up_sql, down_sql = content.split("-- DOWN", 1)
                up_sql = up_sql.replace("-- UP", "").strip()
                down_sql = down_sql.strip()
            else:
                up_sql = content.replace("-- UP", "").strip()
                down_sql = ""
            
            migrations.append(Migration(version, name, up_sql, down_sql))
        
        return migrations
    
    async def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration"""
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        start_time = datetime.now()
        
        try:
            async with self.conn.transaction():
                # Execute migration SQL
                await self.conn.execute(migration.up_sql)
                
                # Record migration
                execution_time = (datetime.now() - start_time).total_seconds()
                
                await self.conn.execute("""
                    INSERT INTO schema_migrations (version, name, checksum, execution_time, success)
                    VALUES ($1, $2, $3, $4, true)
                """, migration.version, migration.name, migration.checksum, execution_time)
                
                logger.info(
                    f"Migration {migration.version} applied successfully",
                    execution_time=execution_time
                )
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to apply migration {migration.version}",
                error=str(e)
            )
            
            # Record failed migration
            try:
                await self.conn.execute("""
                    INSERT INTO schema_migrations (version, name, checksum, success)
                    VALUES ($1, $2, $3, false)
                """, migration.version, migration.name, migration.checksum)
            except:
                pass
            
            return False
    
    async def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration"""
        logger.info(f"Rolling back migration {migration.version}: {migration.name}")
        
        if not migration.down_sql:
            logger.error(f"No rollback SQL for migration {migration.version}")
            return False
        
        try:
            async with self.conn.transaction():
                # Execute rollback SQL
                await self.conn.execute(migration.down_sql)
                
                # Remove migration record
                await self.conn.execute("""
                    DELETE FROM schema_migrations WHERE version = $1
                """, migration.version)
                
                logger.info(f"Migration {migration.version} rolled back successfully")
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to rollback migration {migration.version}",
                error=str(e)
            )
            return False
    
    async def migrate_up(self, target_version: Optional[str] = None):
        """Migrate up to target version (or latest)"""
        applied = await self.get_applied_migrations()
        migrations = self.load_migrations()
        
        pending = [m for m in migrations if m.version not in applied]
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations")
            return
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        for migration in pending:
            success = await self.apply_migration(migration)
            if not success:
                logger.error("Migration failed, stopping")
                sys.exit(1)
        
        logger.info("All migrations applied successfully")
    
    async def migrate_down(self, target_version: Optional[str] = None):
        """Migrate down to target version"""
        applied = await self.get_applied_migrations()
        migrations = self.load_migrations()
        
        # Get migrations to rollback
        to_rollback = []
        for version in reversed(applied):
            if target_version and version <= target_version:
                break
            
            migration = next((m for m in migrations if m.version == version), None)
            if migration:
                to_rollback.append(migration)
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return
        
        logger.info(f"Rolling back {len(to_rollback)} migrations")
        
        for migration in to_rollback:
            success = await self.rollback_migration(migration)
            if not success:
                logger.error("Rollback failed, stopping")
                sys.exit(1)
        
        logger.info("Rollback completed successfully")
    
    async def status(self):
        """Show migration status"""
        current = await self.get_current_version()
        applied = await self.get_applied_migrations()
        migrations = self.load_migrations()
        
        print("\n" + "=" * 80)
        print("DATABASE MIGRATION STATUS")
        print("=" * 80)
        print(f"Current version: {current or 'None'}")
        print(f"Applied migrations: {len(applied)}")
        print(f"Available migrations: {len(migrations)}")
        print("\n" + "-" * 80)
        print(f"{'Version':<15} {'Name':<40} {'Status':<15}")
        print("-" * 80)
        
        for migration in migrations:
            status = "✓ Applied" if migration.version in applied else "○ Pending"
            print(f"{migration.version:<15} {migration.name:<40} {status:<15}")
        
        print("=" * 80 + "\n")
    
    async def create_migration(self, name: str):
        """Create a new migration file"""
        # Get next version number
        migrations = self.load_migrations()
        if migrations:
            last_version = int(migrations[-1].version[1:])  # Remove 'V' prefix
            next_version = f"V{last_version + 1:03d}"
        else:
            next_version = "V001"
        
        # Create filename
        safe_name = name.lower().replace(" ", "_")
        filename = f"{next_version}__{safe_name}.sql"
        file_path = self.migrations_dir / filename
        
        # Create template
        template = f"""-- Migration: {name}
-- Version: {next_version}
-- Created: {datetime.now().isoformat()}

-- UP
-- Add your migration SQL here


-- DOWN
-- Add your rollback SQL here

"""
        
        file_path.write_text(template)
        logger.info(f"Created migration file: {filename}")
        print(f"Migration file created: {file_path}")
    
    async def validate_migrations(self):
        """Validate migration checksums"""
        applied = await self.conn.fetch("""
            SELECT version, checksum FROM schema_migrations WHERE success = true
        """)
        
        migrations = self.load_migrations()
        
        issues = []
        for row in applied:
            migration = next((m for m in migrations if m.version == row["version"]), None)
            if not migration:
                issues.append(f"Applied migration {row['version']} not found in files")
            elif migration.checksum != row["checksum"]:
                issues.append(f"Checksum mismatch for migration {row['version']}")
        
        if issues:
            print("\n⚠️  VALIDATION ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("\n✓ All migrations validated successfully")
            return True


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument("command", choices=[
        "init", "status", "up", "down", "create", "validate"
    ], help="Migration command")
    parser.add_argument("--version", help="Target version for up/down")
    parser.add_argument("--name", help="Migration name for create")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or settings.database_url
    
    if not database_url:
        print("Error: DATABASE_URL not configured")
        sys.exit(1)
    
    # Create migration manager
    manager = MigrationManager(database_url)
    
    try:
        await manager.connect()
        await manager.initialize()
        
        if args.command == "init":
            print("✓ Migration tracking initialized")
        
        elif args.command == "status":
            await manager.status()
        
        elif args.command == "up":
            await manager.migrate_up(args.version)
        
        elif args.command == "down":
            if not args.version:
                print("Error: --version required for down migration")
                sys.exit(1)
            await manager.migrate_down(args.version)
        
        elif args.command == "create":
            if not args.name:
                print("Error: --name required for create")
                sys.exit(1)
            await manager.create_migration(args.name)
        
        elif args.command == "validate":
            await manager.validate_migrations()
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
