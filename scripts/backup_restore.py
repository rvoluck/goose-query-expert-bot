#!/usr/bin/env python3
"""
Backup and restore utilities for Goose Slackbot
Handles database backups, restore operations, and data archival
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import json
import gzip
import shutil
import subprocess

import asyncpg
import structlog

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class BackupManager:
    """Manages database backups and restores"""
    
    def __init__(self, database_url: str, backup_dir: str = None):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir or "./backups")
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def _parse_database_url(self) -> dict:
        """Parse database URL into components"""
        # postgresql://user:password@host:port/database
        from urllib.parse import urlparse
        
        parsed = urlparse(self.database_url)
        
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/")
        }
    
    def create_backup(self, compress: bool = True, schema_only: bool = False) -> Path:
        """Create database backup using pg_dump"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        
        if schema_only:
            backup_name += "_schema"
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        db_config = self._parse_database_url()
        
        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h", db_config["host"],
            "-p", str(db_config["port"]),
            "-U", db_config["user"],
            "-d", db_config["database"],
            "-F", "p",  # Plain text format
            "-f", str(backup_file)
        ]
        
        if schema_only:
            cmd.append("--schema-only")
        else:
            cmd.append("--data-only")
            cmd.append("--inserts")  # Use INSERT statements
        
        # Set password environment variable
        env = {"PGPASSWORD": db_config["password"]}
        
        try:
            logger.info(f"Creating backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress if requested
            if compress:
                compressed_file = Path(str(backup_file) + ".gz")
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                backup_file.unlink()  # Remove uncompressed file
                backup_file = compressed_file
            
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            logger.info(f"Backup created successfully: {backup_file} ({size_mb:.2f} MB)")
            
            print(f"\n✓ Backup created: {backup_file}")
            print(f"  Size: {size_mb:.2f} MB")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            print(f"\n❌ Backup failed: {e}")
            sys.exit(1)
    
    def restore_backup(self, backup_file: Path, drop_existing: bool = False):
        """Restore database from backup"""
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        db_config = self._parse_database_url()
        
        # Decompress if needed
        temp_file = None
        if backup_file.suffix == ".gz":
            temp_file = backup_file.with_suffix("")
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = temp_file
        
        try:
            # Drop existing database if requested
            if drop_existing:
                logger.warning("Dropping existing database")
                self._drop_database(db_config)
                self._create_database(db_config)
            
            # Build psql command
            cmd = [
                "psql",
                "-h", db_config["host"],
                "-p", str(db_config["port"]),
                "-U", db_config["user"],
                "-d", db_config["database"],
                "-f", str(backup_file)
            ]
            
            env = {"PGPASSWORD": db_config["password"]}
            
            logger.info(f"Restoring backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql failed: {result.stderr}")
            
            logger.info("Backup restored successfully")
            print(f"\n✓ Backup restored successfully from: {backup_file}")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            print(f"\n❌ Restore failed: {e}")
            sys.exit(1)
        
        finally:
            # Clean up temp file
            if temp_file and temp_file.exists():
                temp_file.unlink()
    
    def _drop_database(self, db_config: dict):
        """Drop database"""
        cmd = [
            "dropdb",
            "-h", db_config["host"],
            "-p", str(db_config["port"]),
            "-U", db_config["user"],
            "--if-exists",
            db_config["database"]
        ]
        
        env = {"PGPASSWORD": db_config["password"]}
        subprocess.run(cmd, env=env, check=True)
    
    def _create_database(self, db_config: dict):
        """Create database"""
        cmd = [
            "createdb",
            "-h", db_config["host"],
            "-p", str(db_config["port"]),
            "-U", db_config["user"],
            db_config["database"]
        ]
        
        env = {"PGPASSWORD": db_config["password"]}
        subprocess.run(cmd, env=env, check=True)
    
    def list_backups(self) -> List[dict]:
        """List all available backups"""
        backups = []
        
        for file in sorted(self.backup_dir.glob("backup_*.sql*"), reverse=True):
            stat = file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            
            backups.append({
                "file": file.name,
                "path": str(file),
                "size_mb": round(size_mb, 2),
                "created": datetime.fromtimestamp(stat.st_mtime),
                "compressed": file.suffix == ".gz"
            })
        
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """Clean up old backups"""
        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Keep most recent backups
        to_keep = backups[:keep_count]
        to_check = backups[keep_count:]
        
        deleted = 0
        for backup in to_check:
            if backup["created"] < cutoff_date:
                Path(backup["path"]).unlink()
                logger.info(f"Deleted old backup: {backup['file']}")
                deleted += 1
        
        print(f"\n✓ Cleaned up {deleted} old backups")
        print(f"  Kept {len(backups) - deleted} backups")


class DataArchiver:
    """Archive old data to reduce database size"""
    
    def __init__(self, database_url: str, archive_dir: str = None):
        self.database_url = database_url
        self.archive_dir = Path(archive_dir or "./archives")
        self.archive_dir.mkdir(exist_ok=True, parents=True)
    
    async def archive_old_queries(self, days: int = 90) -> int:
        """Archive old query history"""
        conn = await asyncpg.connect(self.database_url)
        
        cutoff = datetime.now() - timedelta(days=days)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Fetch old queries
            queries = await conn.fetch("""
                SELECT * FROM query_history 
                WHERE created_at < $1
                ORDER BY created_at
            """, cutoff)
            
            if not queries:
                print(f"\nNo queries older than {days} days to archive")
                return 0
            
            # Save to JSON file
            archive_file = self.archive_dir / f"queries_{timestamp}.json.gz"
            
            data = [dict(q) for q in queries]
            
            # Convert datetime objects to strings
            for item in data:
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
            
            with gzip.open(archive_file, 'wt') as f:
                json.dump(data, f, indent=2)
            
            # Delete archived queries
            deleted = await conn.execute("""
                DELETE FROM query_history WHERE created_at < $1
            """, cutoff)
            
            await conn.close()
            
            size_mb = archive_file.stat().st_size / (1024 * 1024)
            logger.info(f"Archived {len(queries)} queries to {archive_file}")
            
            print(f"\n✓ Archived {len(queries)} queries")
            print(f"  File: {archive_file}")
            print(f"  Size: {size_mb:.2f} MB")
            
            return len(queries)
            
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            print(f"\n❌ Archive failed: {e}")
            await conn.close()
            return 0
    
    async def archive_old_sessions(self, days: int = 180) -> int:
        """Archive old inactive sessions"""
        conn = await asyncpg.connect(self.database_url)
        
        cutoff = datetime.now() - timedelta(days=days)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Fetch old sessions
            sessions = await conn.fetch("""
                SELECT * FROM user_sessions 
                WHERE last_activity < $1 AND is_active = false
                ORDER BY last_activity
            """, cutoff)
            
            if not sessions:
                print(f"\nNo sessions older than {days} days to archive")
                return 0
            
            # Save to JSON file
            archive_file = self.archive_dir / f"sessions_{timestamp}.json.gz"
            
            data = [dict(s) for s in sessions]
            
            # Convert datetime objects to strings
            for item in data:
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
            
            with gzip.open(archive_file, 'wt') as f:
                json.dump(data, f, indent=2)
            
            # Delete archived sessions
            deleted = await conn.execute("""
                DELETE FROM user_sessions 
                WHERE last_activity < $1 AND is_active = false
            """, cutoff)
            
            await conn.close()
            
            size_mb = archive_file.stat().st_size / (1024 * 1024)
            logger.info(f"Archived {len(sessions)} sessions to {archive_file}")
            
            print(f"\n✓ Archived {len(sessions)} sessions")
            print(f"  File: {archive_file}")
            print(f"  Size: {size_mb:.2f} MB")
            
            return len(sessions)
            
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            print(f"\n❌ Archive failed: {e}")
            await conn.close()
            return 0


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Backup and restore utilities")
    parser.add_argument("command", choices=[
        "backup", "restore", "list", "cleanup", "archive-queries", "archive-sessions"
    ], help="Backup command")
    
    parser.add_argument("--file", help="Backup file for restore")
    parser.add_argument("--compress", action="store_true", default=True, 
                       help="Compress backup")
    parser.add_argument("--schema-only", action="store_true", 
                       help="Backup schema only")
    parser.add_argument("--drop-existing", action="store_true",
                       help="Drop existing database before restore")
    parser.add_argument("--keep-days", type=int, default=30,
                       help="Days to keep backups")
    parser.add_argument("--keep-count", type=int, default=10,
                       help="Number of recent backups to keep")
    parser.add_argument("--archive-days", type=int, default=90,
                       help="Days before archiving data")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--archive-dir", help="Archive directory")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or settings.database_url
    
    if not database_url:
        print("Error: DATABASE_URL not configured")
        sys.exit(1)
    
    if args.command in ["backup", "restore", "list", "cleanup"]:
        manager = BackupManager(database_url, args.backup_dir)
        
        if args.command == "backup":
            manager.create_backup(
                compress=args.compress,
                schema_only=args.schema_only
            )
        
        elif args.command == "restore":
            if not args.file:
                print("Error: --file required for restore")
                sys.exit(1)
            
            backup_file = Path(args.file)
            manager.restore_backup(backup_file, drop_existing=args.drop_existing)
        
        elif args.command == "list":
            backups = manager.list_backups()
            
            if not backups:
                print("\nNo backups found")
            else:
                print("\n" + "=" * 80)
                print("AVAILABLE BACKUPS")
                print("=" * 80)
                
                for backup in backups:
                    print(f"\n{backup['file']}")
                    print(f"  Size: {backup['size_mb']} MB")
                    print(f"  Created: {backup['created']}")
                    print(f"  Compressed: {'Yes' if backup['compressed'] else 'No'}")
                
                print("\n" + "=" * 80)
        
        elif args.command == "cleanup":
            manager.cleanup_old_backups(
                keep_days=args.keep_days,
                keep_count=args.keep_count
            )
    
    elif args.command in ["archive-queries", "archive-sessions"]:
        archiver = DataArchiver(database_url, args.archive_dir)
        
        if args.command == "archive-queries":
            await archiver.archive_old_queries(days=args.archive_days)
        
        elif args.command == "archive-sessions":
            await archiver.archive_old_sessions(days=args.archive_days)


if __name__ == "__main__":
    asyncio.run(main())
