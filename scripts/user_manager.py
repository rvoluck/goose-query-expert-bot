#!/usr/bin/env python3
"""
User management CLI tool
Manage users, roles, permissions, and mappings
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

import asyncpg
from tabulate import tabulate
import structlog

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from database import DatabaseManager, UserMappingRepository, DatabaseConfig

logger = structlog.get_logger(__name__)
settings = get_settings()


class UserManager:
    """User management operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_manager: Optional[DatabaseManager] = None
        self.user_repo: Optional[UserMappingRepository] = None
    
    async def connect(self):
        """Connect to database"""
        config = DatabaseConfig(dsn=self.database_url)
        self.db_manager = DatabaseManager(config)
        await self.db_manager.initialize()
        self.user_repo = UserMappingRepository(self.db_manager)
        logger.info("Connected to database")
    
    async def close(self):
        """Close database connection"""
        if self.db_manager:
            await self.db_manager.close()
            logger.info("Database connection closed")
    
    async def list_users(self, active_only: bool = True):
        """List all users"""
        query = """
            SELECT slack_user_id, internal_user_id, email, full_name, 
                   roles, is_active, created_at, updated_at
            FROM user_mappings
        """
        
        if active_only:
            query += " WHERE is_active = true"
        
        query += " ORDER BY created_at DESC"
        
        rows = await self.db_manager.execute_query(query)
        
        if not rows:
            print("\nNo users found")
            return
        
        # Format data for display
        data = []
        for row in rows:
            roles = json.loads(row["roles"] or "[]")
            data.append([
                row["slack_user_id"],
                row["internal_user_id"],
                row["email"] or "N/A",
                row["full_name"] or "N/A",
                ", ".join(roles) if roles else "None",
                "✓" if row["is_active"] else "✗",
                row["created_at"].strftime("%Y-%m-%d")
            ])
        
        headers = ["Slack ID", "Internal ID", "Email", "Name", "Roles", "Active", "Created"]
        print("\n" + tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal users: {len(data)}")
    
    async def get_user(self, slack_user_id: str):
        """Get user details"""
        mapping = await self.user_repo.get_mapping(slack_user_id)
        
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        print("\n" + "=" * 80)
        print("USER DETAILS")
        print("=" * 80)
        print(f"Slack User ID:    {mapping['slack_user_id']}")
        print(f"Internal User ID: {mapping['internal_user_id']}")
        print(f"LDAP ID:          {mapping.get('ldap_id') or 'N/A'}")
        print(f"Email:            {mapping.get('email') or 'N/A'}")
        print(f"Full Name:        {mapping.get('full_name') or 'N/A'}")
        print(f"Active:           {'Yes' if mapping['is_active'] else 'No'}")
        print(f"\nRoles:            {', '.join(mapping['roles']) if mapping['roles'] else 'None'}")
        print(f"Permissions:      {', '.join(mapping['permissions']) if mapping['permissions'] else 'None'}")
        print(f"\nCreated:          {mapping['created_at']}")
        print(f"Updated:          {mapping['updated_at']}")
        
        if mapping.get('metadata'):
            print(f"\nMetadata:")
            print(json.dumps(mapping['metadata'], indent=2))
        
        print("=" * 80 + "\n")
    
    async def create_user(
        self,
        slack_user_id: str,
        internal_user_id: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        ldap_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None
    ):
        """Create a new user"""
        try:
            await self.user_repo.create_or_update_mapping(
                slack_user_id=slack_user_id,
                internal_user_id=internal_user_id,
                email=email,
                full_name=full_name,
                ldap_id=ldap_id,
                roles=roles or [],
                permissions=permissions or []
            )
            
            print(f"\n✓ User created successfully: {slack_user_id}")
            await self.get_user(slack_user_id)
            
        except Exception as e:
            print(f"\n❌ Failed to create user: {e}")
            logger.error("Failed to create user", error=str(e))
    
    async def update_user(
        self,
        slack_user_id: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        ldap_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None
    ):
        """Update user details"""
        # Get existing user
        mapping = await self.user_repo.get_mapping(slack_user_id)
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        try:
            await self.user_repo.create_or_update_mapping(
                slack_user_id=slack_user_id,
                internal_user_id=mapping["internal_user_id"],
                email=email or mapping.get("email"),
                full_name=full_name or mapping.get("full_name"),
                ldap_id=ldap_id or mapping.get("ldap_id"),
                roles=roles if roles is not None else mapping["roles"],
                permissions=permissions if permissions is not None else mapping["permissions"]
            )
            
            print(f"\n✓ User updated successfully: {slack_user_id}")
            await self.get_user(slack_user_id)
            
        except Exception as e:
            print(f"\n❌ Failed to update user: {e}")
            logger.error("Failed to update user", error=str(e))
    
    async def delete_user(self, slack_user_id: str, soft_delete: bool = True):
        """Delete or deactivate user"""
        if soft_delete:
            # Soft delete - just deactivate
            await self.db_manager.execute_command(
                "UPDATE user_mappings SET is_active = false WHERE slack_user_id = $1",
                slack_user_id
            )
            print(f"\n✓ User deactivated: {slack_user_id}")
        else:
            # Hard delete
            await self.db_manager.execute_command(
                "DELETE FROM user_mappings WHERE slack_user_id = $1",
                slack_user_id
            )
            print(f"\n✓ User deleted permanently: {slack_user_id}")
    
    async def add_role(self, slack_user_id: str, role: str):
        """Add role to user"""
        mapping = await self.user_repo.get_mapping(slack_user_id)
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        roles = mapping["roles"]
        if role in roles:
            print(f"\n⚠️  User already has role: {role}")
            return
        
        roles.append(role)
        
        await self.user_repo.create_or_update_mapping(
            slack_user_id=slack_user_id,
            internal_user_id=mapping["internal_user_id"],
            email=mapping.get("email"),
            full_name=mapping.get("full_name"),
            ldap_id=mapping.get("ldap_id"),
            roles=roles,
            permissions=mapping["permissions"]
        )
        
        print(f"\n✓ Role '{role}' added to user: {slack_user_id}")
    
    async def remove_role(self, slack_user_id: str, role: str):
        """Remove role from user"""
        mapping = await self.user_repo.get_mapping(slack_user_id)
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        roles = mapping["roles"]
        if role not in roles:
            print(f"\n⚠️  User does not have role: {role}")
            return
        
        roles.remove(role)
        
        await self.user_repo.create_or_update_mapping(
            slack_user_id=slack_user_id,
            internal_user_id=mapping["internal_user_id"],
            email=mapping.get("email"),
            full_name=mapping.get("full_name"),
            ldap_id=mapping.get("ldap_id"),
            roles=roles,
            permissions=mapping["permissions"]
        )
        
        print(f"\n✓ Role '{role}' removed from user: {slack_user_id}")
    
    async def add_permission(self, slack_user_id: str, permission: str):
        """Add permission to user"""
        mapping = await self.user_repo.get_mapping(slack_user_id)
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        permissions = mapping["permissions"]
        if permission in permissions:
            print(f"\n⚠️  User already has permission: {permission}")
            return
        
        permissions.append(permission)
        
        await self.user_repo.create_or_update_mapping(
            slack_user_id=slack_user_id,
            internal_user_id=mapping["internal_user_id"],
            email=mapping.get("email"),
            full_name=mapping.get("full_name"),
            ldap_id=mapping.get("ldap_id"),
            roles=mapping["roles"],
            permissions=permissions
        )
        
        print(f"\n✓ Permission '{permission}' added to user: {slack_user_id}")
    
    async def remove_permission(self, slack_user_id: str, permission: str):
        """Remove permission from user"""
        mapping = await self.user_repo.get_mapping(slack_user_id)
        if not mapping:
            print(f"\n❌ User not found: {slack_user_id}")
            return
        
        permissions = mapping["permissions"]
        if permission not in permissions:
            print(f"\n⚠️  User does not have permission: {permission}")
            return
        
        permissions.remove(permission)
        
        await self.user_repo.create_or_update_mapping(
            slack_user_id=slack_user_id,
            internal_user_id=mapping["internal_user_id"],
            email=mapping.get("email"),
            full_name=mapping.get("full_name"),
            ldap_id=mapping.get("ldap_id"),
            roles=mapping["roles"],
            permissions=permissions
        )
        
        print(f"\n✓ Permission '{permission}' removed from user: {slack_user_id}")
    
    async def bulk_import(self, csv_file: str):
        """Bulk import users from CSV"""
        import csv
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            errors = 0
            
            for row in reader:
                try:
                    roles = row.get('roles', '').split(',') if row.get('roles') else []
                    permissions = row.get('permissions', '').split(',') if row.get('permissions') else []
                    
                    await self.user_repo.create_or_update_mapping(
                        slack_user_id=row['slack_user_id'],
                        internal_user_id=row['internal_user_id'],
                        email=row.get('email'),
                        full_name=row.get('full_name'),
                        ldap_id=row.get('ldap_id'),
                        roles=[r.strip() for r in roles if r.strip()],
                        permissions=[p.strip() for p in permissions if p.strip()]
                    )
                    count += 1
                    
                except Exception as e:
                    print(f"Error importing user {row.get('slack_user_id')}: {e}")
                    errors += 1
            
            print(f"\n✓ Imported {count} users ({errors} errors)")
    
    async def export_users(self, output_file: str):
        """Export users to CSV"""
        import csv
        
        rows = await self.db_manager.execute_query("""
            SELECT slack_user_id, internal_user_id, ldap_id, email, full_name,
                   roles, permissions, is_active
            FROM user_mappings
            ORDER BY created_at
        """)
        
        with open(output_file, 'w', newline='') as f:
            fieldnames = [
                'slack_user_id', 'internal_user_id', 'ldap_id', 'email',
                'full_name', 'roles', 'permissions', 'is_active'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                roles = json.loads(row['roles'] or '[]')
                permissions = json.loads(row['permissions'] or '[]')
                
                writer.writerow({
                    'slack_user_id': row['slack_user_id'],
                    'internal_user_id': row['internal_user_id'],
                    'ldap_id': row['ldap_id'] or '',
                    'email': row['email'] or '',
                    'full_name': row['full_name'] or '',
                    'roles': ','.join(roles),
                    'permissions': ','.join(permissions),
                    'is_active': row['is_active']
                })
        
        print(f"\n✓ Exported {len(rows)} users to {output_file}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="User management CLI")
    parser.add_argument("command", choices=[
        "list", "get", "create", "update", "delete",
        "add-role", "remove-role", "add-permission", "remove-permission",
        "import", "export"
    ], help="Management command")
    
    # User identification
    parser.add_argument("--slack-user-id", help="Slack user ID")
    parser.add_argument("--internal-user-id", help="Internal user ID")
    
    # User details
    parser.add_argument("--email", help="User email")
    parser.add_argument("--full-name", help="User full name")
    parser.add_argument("--ldap-id", help="LDAP ID")
    
    # Roles and permissions
    parser.add_argument("--role", help="Role name")
    parser.add_argument("--roles", help="Comma-separated roles")
    parser.add_argument("--permission", help="Permission name")
    parser.add_argument("--permissions", help="Comma-separated permissions")
    
    # Options
    parser.add_argument("--all", action="store_true", help="Include inactive users")
    parser.add_argument("--hard-delete", action="store_true", help="Permanently delete user")
    parser.add_argument("--file", help="CSV file for import/export")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or settings.database_url
    
    if not database_url:
        print("Error: DATABASE_URL not configured")
        sys.exit(1)
    
    # Create user manager
    manager = UserManager(database_url)
    
    try:
        await manager.connect()
        
        if args.command == "list":
            await manager.list_users(active_only=not args.all)
        
        elif args.command == "get":
            if not args.slack_user_id:
                print("Error: --slack-user-id required")
                sys.exit(1)
            await manager.get_user(args.slack_user_id)
        
        elif args.command == "create":
            if not args.slack_user_id or not args.internal_user_id:
                print("Error: --slack-user-id and --internal-user-id required")
                sys.exit(1)
            
            roles = args.roles.split(',') if args.roles else []
            permissions = args.permissions.split(',') if args.permissions else []
            
            await manager.create_user(
                slack_user_id=args.slack_user_id,
                internal_user_id=args.internal_user_id,
                email=args.email,
                full_name=args.full_name,
                ldap_id=args.ldap_id,
                roles=roles,
                permissions=permissions
            )
        
        elif args.command == "update":
            if not args.slack_user_id:
                print("Error: --slack-user-id required")
                sys.exit(1)
            
            roles = args.roles.split(',') if args.roles else None
            permissions = args.permissions.split(',') if args.permissions else None
            
            await manager.update_user(
                slack_user_id=args.slack_user_id,
                email=args.email,
                full_name=args.full_name,
                ldap_id=args.ldap_id,
                roles=roles,
                permissions=permissions
            )
        
        elif args.command == "delete":
            if not args.slack_user_id:
                print("Error: --slack-user-id required")
                sys.exit(1)
            await manager.delete_user(args.slack_user_id, soft_delete=not args.hard_delete)
        
        elif args.command == "add-role":
            if not args.slack_user_id or not args.role:
                print("Error: --slack-user-id and --role required")
                sys.exit(1)
            await manager.add_role(args.slack_user_id, args.role)
        
        elif args.command == "remove-role":
            if not args.slack_user_id or not args.role:
                print("Error: --slack-user-id and --role required")
                sys.exit(1)
            await manager.remove_role(args.slack_user_id, args.role)
        
        elif args.command == "add-permission":
            if not args.slack_user_id or not args.permission:
                print("Error: --slack-user-id and --permission required")
                sys.exit(1)
            await manager.add_permission(args.slack_user_id, args.permission)
        
        elif args.command == "remove-permission":
            if not args.slack_user_id or not args.permission:
                print("Error: --slack-user-id and --permission required")
                sys.exit(1)
            await manager.remove_permission(args.slack_user_id, args.permission)
        
        elif args.command == "import":
            if not args.file:
                print("Error: --file required")
                sys.exit(1)
            await manager.bulk_import(args.file)
        
        elif args.command == "export":
            if not args.file:
                print("Error: --file required")
                sys.exit(1)
            await manager.export_users(args.file)
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
