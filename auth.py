"""
Authentication and Authorization System for Goose Slackbot
Handles user authentication, permissions, and security
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

import jwt
import redis.asyncio as redis
from cryptography.fernet import Fernet
import structlog
import ldap3
from ldap3 import Server, Connection, ALL

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class Permission(Enum):
    """Available permissions in the system"""
    QUERY_EXECUTE = "query_execute"
    QUERY_HISTORY = "query_history"
    QUERY_SHARE = "query_share"
    USER_ADMIN = "user_admin"
    SYSTEM_ADMIN = "system_admin"
    AUDIT_VIEW = "audit_view"


class Role(Enum):
    """Available roles in the system"""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.QUERY_HISTORY],
    Role.ANALYST: [
        Permission.QUERY_EXECUTE,
        Permission.QUERY_HISTORY, 
        Permission.QUERY_SHARE
    ],
    Role.ADMIN: [
        Permission.QUERY_EXECUTE,
        Permission.QUERY_HISTORY,
        Permission.QUERY_SHARE,
        Permission.USER_ADMIN,
        Permission.AUDIT_VIEW
    ],
    Role.SUPER_ADMIN: [
        Permission.QUERY_EXECUTE,
        Permission.QUERY_HISTORY,
        Permission.QUERY_SHARE,
        Permission.USER_ADMIN,
        Permission.SYSTEM_ADMIN,
        Permission.AUDIT_VIEW
    ]
}


@dataclass
class UserContext:
    """User context with authentication and authorization info"""
    user_id: str
    slack_user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    ldap_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    last_activity: Optional[datetime] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission.value in self.permissions
    
    def has_role(self, role: Role) -> bool:
        """Check if user has specific role"""
        return role.value in self.roles
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(self.has_permission(perm) for perm in permissions)


@dataclass
class AuthConfig:
    """Authentication system configuration"""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    session_ttl_seconds: int = 3600
    max_sessions_per_user: int = 5
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60
    redis_url: str = "redis://localhost:6379/0"
    slack_signing_secret: str = ""
    ldap_server: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_user: Optional[str] = None
    ldap_bind_password: Optional[str] = None


class JWTManager:
    """JWT token management"""
    
    def __init__(self, config: AuthConfig):
        self.secret = config.jwt_secret
        self.algorithm = config.jwt_algorithm
        self.expiration_hours = config.jwt_expiration_hours
    
    def generate_token(self, user_context: UserContext) -> str:
        """Generate JWT token for user"""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(hours=self.expiration_hours)
        
        payload = {
            "user_id": user_context.user_id,
            "slack_user_id": user_context.slack_user_id,
            "email": user_context.email,
            "roles": user_context.roles,
            "permissions": user_context.permissions,
            "iat": now.timestamp(),
            "exp": expiry.timestamp(),
            "jti": str(uuid.uuid4())  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh JWT token if valid and not expired"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # Create new token with fresh expiry
        user_context = UserContext(
            user_id=payload["user_id"],
            slack_user_id=payload["slack_user_id"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", [])
        )
        
        return self.generate_token(user_context)


class SessionManager:
    """User session management with Redis"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.redis_client = None
        self.fernet = Fernet(settings.encryption_key.encode()[:32].ljust(32, b'0'))
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(
            self.config.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Session manager initialized")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _encrypt_session_data(self, data: Dict[str, Any]) -> str:
        """Encrypt session data"""
        json_data = json.dumps(data)
        encrypted = self.fernet.encrypt(json_data.encode())
        return encrypted.decode()
    
    def _decrypt_session_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt session data"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error("Failed to decrypt session data", error=str(e))
            return {}
    
    async def create_session(self, user_context: UserContext) -> str:
        """Create new user session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "user_id": user_context.user_id,
            "slack_user_id": user_context.slack_user_id,
            "email": user_context.email,
            "full_name": user_context.full_name,
            "ldap_id": user_context.ldap_id,
            "roles": user_context.roles,
            "permissions": user_context.permissions,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "metadata": user_context.metadata
        }
        
        # Encrypt session data
        encrypted_data = self._encrypt_session_data(session_data)
        
        # Store in Redis with TTL
        session_key = f"session:{session_id}"
        await self.redis_client.setex(
            session_key,
            self.config.session_ttl_seconds,
            encrypted_data
        )
        
        # Track user sessions
        user_sessions_key = f"user_sessions:{user_context.user_id}"
        await self.redis_client.sadd(user_sessions_key, session_id)
        await self.redis_client.expire(user_sessions_key, self.config.session_ttl_seconds)
        
        # Cleanup old sessions if too many
        await self._cleanup_user_sessions(user_context.user_id)
        
        logger.info("Created session", session_id=session_id, user_id=user_context.user_id)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[UserContext]:
        """Get session by ID"""
        session_key = f"session:{session_id}"
        encrypted_data = await self.redis_client.get(session_key)
        
        if not encrypted_data:
            return None
        
        session_data = self._decrypt_session_data(encrypted_data)
        if not session_data:
            return None
        
        # Update last activity
        session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
        encrypted_data = self._encrypt_session_data(session_data)
        await self.redis_client.setex(
            session_key,
            self.config.session_ttl_seconds,
            encrypted_data
        )
        
        return UserContext(
            user_id=session_data["user_id"],
            slack_user_id=session_data["slack_user_id"],
            email=session_data.get("email"),
            full_name=session_data.get("full_name"),
            ldap_id=session_data.get("ldap_id"),
            roles=session_data.get("roles", []),
            permissions=session_data.get("permissions", []),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            session_id=session_id,
            metadata=session_data.get("metadata", {})
        )
    
    async def delete_session(self, session_id: str):
        """Delete session"""
        session_key = f"session:{session_id}"
        await self.redis_client.delete(session_key)
        logger.info("Deleted session", session_id=session_id)
    
    async def _cleanup_user_sessions(self, user_id: str):
        """Cleanup old sessions for user"""
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_client.smembers(user_sessions_key)
        
        if len(session_ids) > self.config.max_sessions_per_user:
            # Get session creation times and remove oldest
            session_times = []
            for session_id in session_ids:
                session_key = f"session:{session_id}"
                encrypted_data = await self.redis_client.get(session_key)
                if encrypted_data:
                    session_data = self._decrypt_session_data(encrypted_data)
                    created_at = datetime.fromisoformat(session_data.get("created_at", "1970-01-01T00:00:00+00:00"))
                    session_times.append((session_id, created_at))
            
            # Sort by creation time and remove oldest
            session_times.sort(key=lambda x: x[1])
            sessions_to_remove = len(session_times) - self.config.max_sessions_per_user
            
            for i in range(sessions_to_remove):
                session_id = session_times[i][0]
                await self.delete_session(session_id)
                await self.redis_client.srem(user_sessions_key, session_id)


class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, redis_client: redis.Redis, config: AuthConfig):
        self.redis_client = redis_client
        self.config = config
    
    async def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        key = f"rate_limit:{user_id}"
        current_time = int(time.time())
        window_start = current_time - self.config.rate_limit_window_seconds
        
        # Remove old entries
        await self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = await self.redis_client.zcard(key)
        
        if current_requests >= self.config.rate_limit_requests:
            return False
        
        # Add current request
        await self.redis_client.zadd(key, {str(current_time): current_time})
        await self.redis_client.expire(key, self.config.rate_limit_window_seconds)
        
        return True
    
    async def get_rate_limit_info(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit information for user"""
        key = f"rate_limit:{user_id}"
        current_time = int(time.time())
        window_start = current_time - self.config.rate_limit_window_seconds
        
        # Clean old entries
        await self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Get current count
        current_requests = await self.redis_client.zcard(key)
        
        return {
            "requests_made": current_requests,
            "requests_allowed": self.config.rate_limit_requests,
            "window_seconds": self.config.rate_limit_window_seconds,
            "reset_time": current_time + self.config.rate_limit_window_seconds
        }


class UserMapper:
    """Maps Slack users to internal users"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def create_mapping(
        self,
        slack_user_id: str,
        internal_user_id: str,
        email: str = None,
        full_name: str = None,
        ldap_id: str = None,
        roles: List[str] = None,
        permissions: List[str] = None
    ):
        """Create user mapping"""
        mapping_data = {
            "internal_user_id": internal_user_id,
            "email": email or "",
            "full_name": full_name or "",
            "ldap_id": ldap_id or "",
            "roles": json.dumps(roles or []),
            "permissions": json.dumps(permissions or []),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"user_mapping:{slack_user_id}"
        await self.redis_client.hset(key, mapping=mapping_data)
        
        # Create reverse mapping
        reverse_key = f"reverse_mapping:{internal_user_id}"
        await self.redis_client.set(reverse_key, slack_user_id)
        
        logger.info("Created user mapping", slack_user_id=slack_user_id, internal_user_id=internal_user_id)
    
    async def get_mapping(self, slack_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user mapping by Slack user ID"""
        key = f"user_mapping:{slack_user_id}"
        mapping_data = await self.redis_client.hgetall(key)
        
        if not mapping_data:
            return None
        
        # Parse JSON fields
        mapping_data["roles"] = json.loads(mapping_data.get("roles", "[]"))
        mapping_data["permissions"] = json.loads(mapping_data.get("permissions", "[]"))
        
        return mapping_data
    
    async def update_roles_and_permissions(
        self, 
        slack_user_id: str, 
        roles: List[str], 
        permissions: List[str]
    ):
        """Update user roles and permissions"""
        key = f"user_mapping:{slack_user_id}"
        
        await self.redis_client.hset(key, mapping={
            "roles": json.dumps(roles),
            "permissions": json.dumps(permissions),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info("Updated user permissions", slack_user_id=slack_user_id)


class SlackSignatureVerifier:
    """Verifies Slack request signatures"""
    
    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret.encode()
    
    def verify_signature(self, request_body: bytes, timestamp: str, signature: str) -> bool:
        """Verify Slack request signature"""
        if not timestamp or not signature:
            return False
        
        # Check timestamp (prevent replay attacks)
        try:
            request_timestamp = int(timestamp)
            current_timestamp = int(time.time())
            
            if abs(current_timestamp - request_timestamp) > 300:  # 5 minutes
                logger.warning("Request timestamp too old", timestamp=timestamp)
                return False
        except ValueError:
            return False
        
        # Verify signature
        sig_basestring = f"v0:{timestamp}:{request_body.decode()}"
        computed_signature = "v0=" + hmac.new(
            self.signing_secret,
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)


class LDAPAuthenticator:
    """LDAP authentication (optional)"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.server = None
        
        if config.ldap_server:
            self.server = Server(config.ldap_server, get_info=ALL)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user against LDAP"""
        if not self.server:
            return None
        
        try:
            # Bind with service account
            conn = Connection(
                self.server,
                user=self.config.ldap_bind_user,
                password=self.config.ldap_bind_password,
                auto_bind=True
            )
            
            # Search for user
            search_filter = f"(uid={username})"
            conn.search(
                search_base=self.config.ldap_base_dn,
                search_filter=search_filter,
                attributes=["uid", "mail", "cn", "memberOf"]
            )
            
            if not conn.entries:
                return None
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # Try to bind as user to verify password
            user_conn = Connection(self.server, user=user_dn, password=password)
            if not user_conn.bind():
                return None
            
            # Extract user information
            user_info = {
                "username": str(user_entry.uid),
                "email": str(user_entry.mail) if user_entry.mail else None,
                "full_name": str(user_entry.cn) if user_entry.cn else None,
                "groups": [str(group) for group in user_entry.memberOf] if user_entry.memberOf else []
            }
            
            user_conn.unbind()
            conn.unbind()
            
            return user_info
            
        except Exception as e:
            logger.error("LDAP authentication failed", error=str(e))
            return None


class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self, config: AuthConfig):
        self.signature_verifier = SlackSignatureVerifier(config.slack_signing_secret)
        self.rate_limiter = None  # Will be set after Redis initialization
    
    async def verify_slack_request(
        self, 
        request_body: bytes, 
        timestamp: str, 
        signature: str
    ) -> bool:
        """Verify Slack request signature and timestamp"""
        return self.signature_verifier.verify_signature(request_body, timestamp, signature)
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        if self.rate_limiter:
            return await self.rate_limiter.is_allowed(user_id)
        return True


class AuthSystem:
    """Main authentication system"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.jwt_manager = JWTManager(config)
        self.session_manager = SessionManager(config)
        self.user_mapper = None  # Will be set after Redis initialization
        self.rate_limiter = None  # Will be set after Redis initialization
        self.security_middleware = SecurityMiddleware(config)
        self.ldap_authenticator = LDAPAuthenticator(config)
        
    async def initialize(self):
        """Initialize the authentication system"""
        await self.session_manager.initialize()
        
        # Initialize Redis-dependent components
        self.user_mapper = UserMapper(self.session_manager.redis_client)
        self.rate_limiter = RateLimiter(self.session_manager.redis_client, self.config)
        self.security_middleware.rate_limiter = self.rate_limiter
        
        logger.info("Authentication system initialized")
    
    async def close(self):
        """Close authentication system"""
        await self.session_manager.close()
    
    async def authenticate_user(self, slack_user_id: str) -> Optional[UserContext]:
        """Authenticate user by Slack user ID"""
        # Get user mapping
        mapping = await self.user_mapper.get_mapping(slack_user_id)
        if not mapping:
            logger.warning("No user mapping found", slack_user_id=slack_user_id)
            return None
        
        # Create user context
        user_context = UserContext(
            user_id=mapping["internal_user_id"],
            slack_user_id=slack_user_id,
            email=mapping.get("email"),
            full_name=mapping.get("full_name"),
            ldap_id=mapping.get("ldap_id"),
            roles=mapping.get("roles", []),
            permissions=mapping.get("permissions", [])
        )
        
        # Create session
        session_id = await self.session_manager.create_session(user_context)
        user_context.session_id = session_id
        
        return user_context
    
    async def create_user_mapping(
        self,
        slack_user_id: str,
        internal_user_id: str,
        email: str = None,
        full_name: str = None,
        ldap_id: str = None,
        roles: List[Role] = None,
        custom_permissions: List[Permission] = None
    ):
        """Create user mapping with roles and permissions"""
        
        # Convert roles to permissions
        all_permissions = set()
        role_names = []
        
        if roles:
            for role in roles:
                role_names.append(role.value)
                role_perms = ROLE_PERMISSIONS.get(role, [])
                all_permissions.update(perm.value for perm in role_perms)
        
        # Add custom permissions
        if custom_permissions:
            all_permissions.update(perm.value for perm in custom_permissions)
        
        await self.user_mapper.create_mapping(
            slack_user_id=slack_user_id,
            internal_user_id=internal_user_id,
            email=email,
            full_name=full_name,
            ldap_id=ldap_id,
            roles=role_names,
            permissions=list(all_permissions)
        )


# Decorators for permission checking
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user context from arguments
            user_context = None
            for arg in args:
                if isinstance(arg, UserContext):
                    user_context = arg
                    break
            
            if not user_context:
                raise PermissionError("No user context provided")
            
            if not user_context.has_permission(permission):
                raise PermissionError(f"Permission {permission.value} required")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user context from arguments
            user_context = None
            for arg in args:
                if isinstance(arg, UserContext):
                    user_context = arg
                    break
            
            if not user_context:
                raise PermissionError("No user context provided")
            
            if not user_context.has_role(role):
                raise PermissionError(f"Role {role.value} required")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Factory function
async def create_auth_system() -> AuthSystem:
    """Create and initialize authentication system"""
    config = AuthConfig(
        jwt_secret=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        jwt_expiration_hours=settings.jwt_expiration_hours,
        session_ttl_seconds=settings.redis_session_ttl,
        rate_limit_requests=settings.rate_limit_per_user_per_minute,
        rate_limit_window_seconds=60,
        redis_url=settings.redis_url,
        slack_signing_secret=settings.slack_signing_secret,
        ldap_server=settings.ldap_server,
        ldap_base_dn=settings.ldap_base_dn,
        ldap_bind_user=settings.ldap_bind_user,
        ldap_bind_password=settings.ldap_bind_password
    )
    
    auth_system = AuthSystem(config)
    await auth_system.initialize()
    return auth_system


if __name__ == "__main__":
    # Test authentication system
    async def test_auth():
        auth_system = await create_auth_system()
        
        # Create test user mapping
        await auth_system.create_user_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            email="test@example.com",
            full_name="Test User",
            roles=[Role.ANALYST]
        )
        
        # Authenticate user
        user_context = await auth_system.authenticate_user("U123456789")
        if user_context:
            print(f"✅ User authenticated: {user_context.user_id}")
            print(f"Permissions: {user_context.permissions}")
            print(f"Can execute queries: {user_context.has_permission(Permission.QUERY_EXECUTE)}")
        else:
            print("❌ Authentication failed")
        
        await auth_system.close()
    
    asyncio.run(test_auth())
