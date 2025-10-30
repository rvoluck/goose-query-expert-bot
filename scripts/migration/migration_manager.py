"""
Database migration management system for Goose Slackbot
Handles schema changes, data migrations, and version control
"""

import asyncio
import asyncpg
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import argparse
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_settings
from database import DatabaseManager, DatabaseConfig

logger = structlog.get_logger(__name__)


@dataclass
class Migration:
    """Represents a database migration"""
    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        
        # Calculate checksum if not provided
        if not self.checksum:
            content = f"{self.up_sql}{self.down_sql}{self.name}"
            self.checksum = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class MigrationRecord:
    """Database record of applied migration"""
    version: str
    name: str
    checksum: str
    applied_at: datetime
    applied_by: str
    execution_time_ms: int


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, database_url: str, migrations_dir: str = None):
        self.database_url = database_url
        self.migrations_dir = Path(migrations_dir or Path(__file__).parent / "migrations")
        self.db_manager: Optional[DatabaseManager] = None
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database connection and migration table"""
        config = DatabaseConfig(dsn=self.database_url)
        self.db_manager = DatabaseManager(config)
        await self.db_manager.initialize()
        
        # Create migration tracking table
        await self._create_migration_table()
    
    async def close(self):
        """Close database connection"""
        if self.db_manager:
            await self.db_manager.close()
    
    async def _create_migration_table(self):
        """Create the migration tracking table"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            checksum VARCHAR(64) NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            applied_by VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
            execution_time_ms INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at 
        ON schema_migrations(applied_at);
        """
        
        await self.db_manager.execute_command(create_table_sql)
        logger.info("Migration tracking table initialized")
    
    def load_migrations(self) -> List[Migration]:
        """Load all migration files from the migrations directory"""
        migrations = []
        
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            migration = self._parse_migration_file(migration_file)
            if migration:
                migrations.append(migration)
        
        # Also load JSON migration files
        for migration_file in sorted(self.migrations_dir.glob("*.json")):
            migration = self._parse_json_migration_file(migration_file)
            if migration:
                migrations.append(migration)
        
        # Sort by version
        migrations.sort(key=lambda m: m.version)
        
        logger.info(f"Loaded {len(migrations)} migrations")
        return migrations
    
    def _parse_migration_file(self, file_path: Path) -> Optional[Migration]:
        """Parse a SQL migration file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract metadata from comments
            lines = content.split('\n')
            metadata = {}
            sql_lines = []
            
            in_metadata = False
            in_down_section = False
            up_sql_lines = []
            down_sql_lines = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('-- Migration:'):
                    in_metadata = True
                    continue
                elif line.startswith('-- End Migration') or (line.startswith('--') and not line.startswith('-- ')):
                    in_metadata = False
                    continue
                elif in_metadata and line.startswith('-- '):
                    key_value = line[3:].split(':', 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        metadata[key.strip().lower()] = value.strip()
                    continue
                elif line.startswith('-- DOWN'):
                    in_down_section = True
                    continue
                elif line.startswith('-- UP') or line.startswith('-- End'):
                    in_down_section = False
                    continue
                
                if not line.startswith('--'):
                    if in_down_section:
                        down_sql_lines.append(line)
                    else:
                        up_sql_lines.append(line)
            
            # Extract version from filename (e.g., "001_create_users.sql" -> "001")
            version = file_path.stem.split('_')[0]
            name = metadata.get('name', file_path.stem)
            description = metadata.get('description', '')
            dependencies = metadata.get('dependencies', '').split(',') if metadata.get('dependencies') else []
            dependencies = [dep.strip() for dep in dependencies if dep.strip()]
            
            up_sql = '\n'.join(up_sql_lines).strip()
            down_sql = '\n'.join(down_sql_lines).strip()
            
            if not up_sql:
                logger.warning(f"No UP SQL found in migration file: {file_path}")
                return None
            
            return Migration(
                version=version,
                name=name,
                description=description,
                up_sql=up_sql,
                down_sql=down_sql,
                checksum='',  # Will be calculated in __post_init__
                dependencies=dependencies
            )
        
        except Exception as e:
            logger.error(f"Error parsing migration file {file_path}: {e}")
            return None
    
    def _parse_json_migration_file(self, file_path: Path) -> Optional[Migration]:
        """Parse a JSON migration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Migration(
                version=data['version'],
                name=data['name'],
                description=data.get('description', ''),
                up_sql=data['up_sql'],
                down_sql=data.get('down_sql', ''),
                checksum=data.get('checksum', ''),
                dependencies=data.get('dependencies', [])
            )
        
        except Exception as e:
            logger.error(f"Error parsing JSON migration file {file_path}: {e}")
            return None
    
    async def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get list of applied migrations from database"""
        rows = await self.db_manager.execute_query(
            """
            SELECT version, name, checksum, applied_at, applied_by, execution_time_ms
            FROM schema_migrations
            ORDER BY version
            """
        )
        
        return [
            MigrationRecord(
                version=row['version'],
                name=row['name'],
                checksum=row['checksum'],
                applied_at=row['applied_at'],
                applied_by=row['applied_by'],
                execution_time_ms=row['execution_time_ms']
            )
            for row in rows
        ]
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of migrations that haven't been applied"""
        all_migrations = self.load_migrations()
        applied_migrations = await self.get_applied_migrations()
        applied_versions = {m.version for m in applied_migrations}
        
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        # Validate checksums for applied migrations
        applied_by_version = {m.version: m for m in applied_migrations}
        for migration in all_migrations:
            if migration.version in applied_by_version:
                applied = applied_by_version[migration.version]
                if migration.checksum != applied.checksum:
                    logger.warning(
                        f"Checksum mismatch for migration {migration.version}: "
                        f"file={migration.checksum[:8]} vs db={applied.checksum[:8]}"
                    )
        
        return pending
    
    def _validate_dependencies(self, migrations: List[Migration], applied_versions: set) -> List[str]:
        """Validate migration dependencies"""
        errors = []
        
        for migration in migrations:
            for dep in migration.dependencies:
                if dep not in applied_versions:
                    # Check if dependency is in the current migration batch
                    dep_in_batch = any(m.version == dep for m in migrations)
                    if not dep_in_batch:
                        errors.append(
                            f"Migration {migration.version} depends on {dep} which is not applied"
                        )
        
        return errors
    
    async def apply_migration(self, migration: Migration) -> Tuple[bool, str, int]:
        """Apply a single migration"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Applying migration {migration.version}: {migration.name}")
            
            # Start transaction
            async with self.db_manager.pool.acquire() as conn:
                async with conn.transaction():
                    # Execute migration SQL
                    await conn.execute(migration.up_sql)
                    
                    # Record migration
                    execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    await conn.execute(
                        """
                        INSERT INTO schema_migrations 
                        (version, name, checksum, execution_time_ms)
                        VALUES ($1, $2, $3, $4)
                        """,
                        migration.version,
                        migration.name,
                        migration.checksum,
                        execution_time_ms
                    )
            
            logger.info(f"Successfully applied migration {migration.version}")
            return True, "Success", execution_time_ms
        
        except Exception as e:
            error_msg = f"Failed to apply migration {migration.version}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0
    
    async def rollback_migration(self, migration: Migration) -> Tuple[bool, str]:
        """Rollback a single migration"""
        try:
            if not migration.down_sql:
                return False, f"No rollback SQL defined for migration {migration.version}"
            
            logger.info(f"Rolling back migration {migration.version}: {migration.name}")
            
            # Start transaction
            async with self.db_manager.pool.acquire() as conn:
                async with conn.transaction():
                    # Execute rollback SQL
                    await conn.execute(migration.down_sql)
                    
                    # Remove migration record
                    await conn.execute(
                        "DELETE FROM schema_migrations WHERE version = $1",
                        migration.version
                    )
            
            logger.info(f"Successfully rolled back migration {migration.version}")
            return True, "Success"
        
        except Exception as e:
            error_msg = f"Failed to rollback migration {migration.version}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def migrate_up(self, target_version: str = None) -> Dict[str, Any]:
        """Apply pending migrations up to target version"""
        pending_migrations = await self.get_pending_migrations()
        applied_migrations = await self.get_applied_migrations()
        applied_versions = {m.version for m in applied_migrations}
        
        if target_version:
            pending_migrations = [m for m in pending_migrations if m.version <= target_version]
        
        if not pending_migrations:
            logger.info("No pending migrations to apply")
            return {
                'success': True,
                'message': 'No pending migrations',
                'applied_count': 0,
                'migrations': []
            }
        
        # Validate dependencies
        dependency_errors = self._validate_dependencies(pending_migrations, applied_versions)
        if dependency_errors:
            return {
                'success': False,
                'message': 'Dependency validation failed',
                'errors': dependency_errors,
                'applied_count': 0,
                'migrations': []
            }
        
        # Apply migrations
        results = []
        applied_count = 0
        
        for migration in pending_migrations:
            success, message, execution_time = await self.apply_migration(migration)
            
            results.append({
                'version': migration.version,
                'name': migration.name,
                'success': success,
                'message': message,
                'execution_time_ms': execution_time
            })
            
            if success:
                applied_count += 1
                applied_versions.add(migration.version)
            else:
                # Stop on first failure
                break
        
        return {
            'success': applied_count == len(pending_migrations),
            'message': f'Applied {applied_count}/{len(pending_migrations)} migrations',
            'applied_count': applied_count,
            'migrations': results
        }
    
    async def migrate_down(self, target_version: str) -> Dict[str, Any]:
        """Rollback migrations down to target version"""
        applied_migrations = await self.get_applied_migrations()
        all_migrations = self.load_migrations()
        migration_by_version = {m.version: m for m in all_migrations}
        
        # Find migrations to rollback (in reverse order)
        to_rollback = [m for m in applied_migrations if m.version > target_version]
        to_rollback.sort(key=lambda m: m.version, reverse=True)
        
        if not to_rollback:
            logger.info(f"No migrations to rollback to version {target_version}")
            return {
                'success': True,
                'message': f'Already at or below version {target_version}',
                'rolled_back_count': 0,
                'migrations': []
            }
        
        # Rollback migrations
        results = []
        rolled_back_count = 0
        
        for migration_record in to_rollback:
            migration = migration_by_version.get(migration_record.version)
            if not migration:
                results.append({
                    'version': migration_record.version,
                    'name': migration_record.name,
                    'success': False,
                    'message': 'Migration file not found'
                })
                break
            
            success, message = await self.rollback_migration(migration)
            
            results.append({
                'version': migration.version,
                'name': migration.name,
                'success': success,
                'message': message
            })
            
            if success:
                rolled_back_count += 1
            else:
                # Stop on first failure
                break
        
        return {
            'success': rolled_back_count == len(to_rollback),
            'message': f'Rolled back {rolled_back_count}/{len(to_rollback)} migrations',
            'rolled_back_count': rolled_back_count,
            'migrations': results
        }
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        all_migrations = self.load_migrations()
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()
        
        applied_versions = {m.version for m in applied_migrations}
        
        # Check for missing migrations (applied but file not found)
        missing_migrations = []
        migration_versions = {m.version for m in all_migrations}
        for applied in applied_migrations:
            if applied.version not in migration_versions:
                missing_migrations.append(applied.version)
        
        # Get current version
        current_version = None
        if applied_migrations:
            current_version = max(applied_migrations, key=lambda m: m.version).version
        
        return {
            'current_version': current_version,
            'total_migrations': len(all_migrations),
            'applied_migrations': len(applied_migrations),
            'pending_migrations': len(pending_migrations),
            'missing_migrations': missing_migrations,
            'migrations': [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description,
                    'applied': m.version in applied_versions,
                    'checksum': m.checksum[:8]
                }
                for m in all_migrations
            ]
        }
    
    def create_migration_file(self, name: str, description: str = "", dependencies: List[str] = None) -> Path:
        """Create a new migration file template"""
        dependencies = dependencies or []
        
        # Generate version number
        existing_migrations = self.load_migrations()
        if existing_migrations:
            last_version = max(int(m.version) for m in existing_migrations if m.version.isdigit())
            version = f"{last_version + 1:03d}"
        else:
            version = "001"
        
        # Create filename
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
        filename = f"{version}_{safe_name}.sql"
        file_path = self.migrations_dir / filename
        
        # Create migration template
        template = f"""-- Migration: {name}
-- Version: {version}
-- Description: {description}
-- Dependencies: {', '.join(dependencies)}
-- Created: {datetime.now(timezone.utc).isoformat()}

-- UP: Apply migration
-- Add your migration SQL here


-- DOWN: Rollback migration
-- Add your rollback SQL here (optional)

"""
        
        file_path.write_text(template, encoding='utf-8')
        logger.info(f"Created migration file: {file_path}")
        
        return file_path


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("--database-url", 
                       default=os.getenv("DATABASE_URL", "postgresql://localhost:5432/goose_slackbot"),
                       help="Database connection URL")
    parser.add_argument("--migrations-dir", 
                       default=None,
                       help="Migrations directory path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    
    # Up command
    up_parser = subparsers.add_parser("up", help="Apply pending migrations")
    up_parser.add_argument("--target", help="Target version to migrate to")
    
    # Down command
    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument("target", help="Target version to rollback to")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration file")
    create_parser.add_argument("name", help="Migration name")
    create_parser.add_argument("--description", default="", help="Migration description")
    create_parser.add_argument("--depends-on", action="append", help="Migration dependencies")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize migration manager
    manager = MigrationManager(args.database_url, args.migrations_dir)
    
    try:
        if args.command != "create":
            await manager.initialize()
        
        if args.command == "status":
            status = await manager.get_migration_status()
            
            print(f"Current Version: {status['current_version'] or 'None'}")
            print(f"Total Migrations: {status['total_migrations']}")
            print(f"Applied: {status['applied_migrations']}")
            print(f"Pending: {status['pending_migrations']}")
            
            if status['missing_migrations']:
                print(f"Missing: {len(status['missing_migrations'])}")
                print("  " + ", ".join(status['missing_migrations']))
            
            print("\nMigrations:")
            for migration in status['migrations']:
                status_icon = "✅" if migration['applied'] else "⏳"
                print(f"  {status_icon} {migration['version']} - {migration['name']}")
                if migration['description']:
                    print(f"      {migration['description']}")
        
        elif args.command == "up":
            result = await manager.migrate_up(args.target)
            
            print(f"Migration Result: {result['message']}")
            
            for migration in result['migrations']:
                status_icon = "✅" if migration['success'] else "❌"
                print(f"  {status_icon} {migration['version']} - {migration['name']}")
                if not migration['success']:
                    print(f"      Error: {migration['message']}")
                else:
                    print(f"      Completed in {migration['execution_time_ms']}ms")
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == "down":
            result = await manager.migrate_down(args.target)
            
            print(f"Rollback Result: {result['message']}")
            
            for migration in result['migrations']:
                status_icon = "✅" if migration['success'] else "❌"
                print(f"  {status_icon} {migration['version']} - {migration['name']}")
                if not migration['success']:
                    print(f"      Error: {migration['message']}")
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == "create":
            file_path = manager.create_migration_file(
                args.name, 
                args.description, 
                args.depends_on or []
            )
            print(f"Created migration file: {file_path}")
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
