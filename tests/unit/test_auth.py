"""
Unit tests for authentication system
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from auth import (
    AuthSystem, UserContext, LDAPAuthProvider, DatabaseAuthProvider,
    TokenAuthProvider, create_auth_system
)
from database import UserMappingRepository
from tests import async_test


class TestUserContext:
    """Test UserContext class"""
    
    def test_user_context_creation(self):
        """Test UserContext creation"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            ldap_id="test.user",
            email="test@example.com",
            full_name="Test User",
            roles=["analyst", "viewer"],
            permissions=["query_execute", "query_view"],
            is_active=True
        )
        
        assert context.user_id == "test_user"
        assert context.slack_user_id == "U123456789"
        assert context.ldap_id == "test.user"
        assert context.email == "test@example.com"
        assert "analyst" in context.roles
        assert "query_execute" in context.permissions
        assert context.is_active is True
    
    def test_has_permission(self):
        """Test permission checking"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            permissions=["query_execute", "query_view"]
        )
        
        assert context.has_permission("query_execute") is True
        assert context.has_permission("query_view") is True
        assert context.has_permission("admin_access") is False
    
    def test_has_role(self):
        """Test role checking"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            roles=["analyst", "viewer"]
        )
        
        assert context.has_role("analyst") is True
        assert context.has_role("viewer") is True
        assert context.has_role("admin") is False
    
    def test_to_dict(self):
        """Test UserContext serialization"""
        context = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            ldap_id="test.user",
            email="test@example.com",
            roles=["analyst"],
            permissions=["query_execute"]
        )
        
        data = context.to_dict()
        
        assert data["user_id"] == "test_user"
        assert data["slack_user_id"] == "U123456789"
        assert data["ldap_id"] == "test.user"
        assert data["email"] == "test@example.com"
        assert data["roles"] == ["analyst"]
        assert data["permissions"] == ["query_execute"]
    
    def test_from_dict(self):
        """Test UserContext deserialization"""
        data = {
            "user_id": "test_user",
            "slack_user_id": "U123456789",
            "ldap_id": "test.user",
            "email": "test@example.com",
            "full_name": "Test User",
            "roles": ["analyst"],
            "permissions": ["query_execute"],
            "is_active": True
        }
        
        context = UserContext.from_dict(data)
        
        assert context.user_id == "test_user"
        assert context.slack_user_id == "U123456789"
        assert context.ldap_id == "test.user"
        assert context.email == "test@example.com"
        assert context.roles == ["analyst"]
        assert context.permissions == ["query_execute"]
        assert context.is_active is True


class TestDatabaseAuthProvider:
    """Test DatabaseAuthProvider class"""
    
    @async_test
    async def test_authenticate_existing_user(self):
        """Test authentication of existing user"""
        # Mock user mapping repository
        mock_repo = AsyncMock(spec=UserMappingRepository)
        mock_repo.get_mapping.return_value = {
            "slack_user_id": "U123456789",
            "internal_user_id": "test_user",
            "ldap_id": "test.user",
            "email": "test@example.com",
            "full_name": "Test User",
            "roles": ["analyst"],
            "permissions": ["query_execute"],
            "is_active": True,
            "metadata": {}
        }
        
        provider = DatabaseAuthProvider(mock_repo)
        context = await provider.authenticate("U123456789")
        
        assert context is not None
        assert context.user_id == "test_user"
        assert context.slack_user_id == "U123456789"
        assert context.ldap_id == "test.user"
        assert context.email == "test@example.com"
        assert "analyst" in context.roles
        assert "query_execute" in context.permissions
        
        mock_repo.get_mapping.assert_called_once_with("U123456789")
    
    @async_test
    async def test_authenticate_nonexistent_user(self):
        """Test authentication of non-existent user"""
        mock_repo = AsyncMock(spec=UserMappingRepository)
        mock_repo.get_mapping.return_value = None
        
        provider = DatabaseAuthProvider(mock_repo)
        context = await provider.authenticate("U999999999")
        
        assert context is None
        mock_repo.get_mapping.assert_called_once_with("U999999999")
    
    @async_test
    async def test_authenticate_inactive_user(self):
        """Test authentication of inactive user"""
        mock_repo = AsyncMock(spec=UserMappingRepository)
        mock_repo.get_mapping.return_value = {
            "slack_user_id": "U123456789",
            "internal_user_id": "test_user",
            "is_active": False,
            "roles": [],
            "permissions": [],
            "metadata": {}
        }
        
        provider = DatabaseAuthProvider(mock_repo)
        context = await provider.authenticate("U123456789")
        
        assert context is None


class TestLDAPAuthProvider:
    """Test LDAPAuthProvider class"""
    
    @async_test
    async def test_authenticate_valid_ldap_user(self):
        """Test LDAP authentication with valid user"""
        mock_ldap_client = AsyncMock()
        mock_ldap_client.search.return_value = [{
            "cn": ["Test User"],
            "mail": ["test@example.com"],
            "memberOf": ["CN=DataAnalysts,OU=Groups,DC=company,DC=com"]
        }]
        
        with patch('auth.ldap3.Connection', return_value=mock_ldap_client):
            provider = LDAPAuthProvider(
                server="ldap://localhost",
                base_dn="DC=company,DC=com",
                bind_dn="CN=service,DC=company,DC=com",
                bind_password="password"
            )
            
            context = await provider.authenticate("test.user")
            
            assert context is not None
            assert context.ldap_id == "test.user"
            assert context.email == "test@example.com"
            assert context.full_name == "Test User"
    
    @async_test
    async def test_authenticate_invalid_ldap_user(self):
        """Test LDAP authentication with invalid user"""
        mock_ldap_client = AsyncMock()
        mock_ldap_client.search.return_value = []
        
        with patch('auth.ldap3.Connection', return_value=mock_ldap_client):
            provider = LDAPAuthProvider(
                server="ldap://localhost",
                base_dn="DC=company,DC=com",
                bind_dn="CN=service,DC=company,DC=com",
                bind_password="password"
            )
            
            context = await provider.authenticate("invalid.user")
            assert context is None
    
    @async_test
    async def test_ldap_connection_error(self):
        """Test LDAP connection error handling"""
        with patch('auth.ldap3.Connection', side_effect=Exception("Connection failed")):
            provider = LDAPAuthProvider(
                server="ldap://invalid",
                base_dn="DC=company,DC=com",
                bind_dn="CN=service,DC=company,DC=com",
                bind_password="password"
            )
            
            context = await provider.authenticate("test.user")
            assert context is None


class TestTokenAuthProvider:
    """Test TokenAuthProvider class"""
    
    @async_test
    async def test_authenticate_valid_token(self):
        """Test token authentication with valid token"""
        # Mock external API response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "user_id": "test_user",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["analyst"],
            "permissions": ["query_execute"]
        }
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            provider = TokenAuthProvider(
                api_url="https://auth.example.com/validate",
                api_key="test_key"
            )
            
            context = await provider.authenticate("valid_token")
            
            assert context is not None
            assert context.user_id == "test_user"
            assert context.email == "test@example.com"
            assert "analyst" in context.roles
    
    @async_test
    async def test_authenticate_invalid_token(self):
        """Test token authentication with invalid token"""
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            provider = TokenAuthProvider(
                api_url="https://auth.example.com/validate",
                api_key="test_key"
            )
            
            context = await provider.authenticate("invalid_token")
            assert context is None


class TestAuthSystem:
    """Test AuthSystem class"""
    
    @async_test
    async def test_single_provider_success(self):
        """Test authentication with single provider success"""
        mock_provider = AsyncMock()
        mock_provider.authenticate.return_value = UserContext(
            user_id="test_user",
            slack_user_id="U123456789"
        )
        
        auth_system = AuthSystem([mock_provider])
        context = await auth_system.authenticate_user("U123456789")
        
        assert context is not None
        assert context.user_id == "test_user"
        mock_provider.authenticate.assert_called_once_with("U123456789")
    
    @async_test
    async def test_multiple_providers_fallback(self):
        """Test authentication with multiple providers and fallback"""
        # First provider fails
        mock_provider1 = AsyncMock()
        mock_provider1.authenticate.return_value = None
        
        # Second provider succeeds
        mock_provider2 = AsyncMock()
        mock_provider2.authenticate.return_value = UserContext(
            user_id="test_user",
            slack_user_id="U123456789"
        )
        
        auth_system = AuthSystem([mock_provider1, mock_provider2])
        context = await auth_system.authenticate_user("U123456789")
        
        assert context is not None
        assert context.user_id == "test_user"
        
        mock_provider1.authenticate.assert_called_once_with("U123456789")
        mock_provider2.authenticate.assert_called_once_with("U123456789")
    
    @async_test
    async def test_all_providers_fail(self):
        """Test authentication when all providers fail"""
        mock_provider1 = AsyncMock()
        mock_provider1.authenticate.return_value = None
        
        mock_provider2 = AsyncMock()
        mock_provider2.authenticate.return_value = None
        
        auth_system = AuthSystem([mock_provider1, mock_provider2])
        context = await auth_system.authenticate_user("U123456789")
        
        assert context is None
    
    @async_test
    async def test_check_permission_with_context(self):
        """Test permission checking with user context"""
        mock_provider = AsyncMock()
        mock_provider.authenticate.return_value = UserContext(
            user_id="test_user",
            slack_user_id="U123456789",
            permissions=["query_execute"]
        )
        
        auth_system = AuthSystem([mock_provider])
        context = await auth_system.authenticate_user("U123456789")
        
        assert auth_system.check_permission(context, "query_execute") is True
        assert auth_system.check_permission(context, "admin_access") is False
    
    @async_test
    async def test_check_permission_without_context(self):
        """Test permission checking without user context"""
        auth_system = AuthSystem([])
        
        assert auth_system.check_permission(None, "query_execute") is False
    
    @async_test
    async def test_provider_exception_handling(self):
        """Test handling of provider exceptions"""
        mock_provider1 = AsyncMock()
        mock_provider1.authenticate.side_effect = Exception("Provider error")
        
        mock_provider2 = AsyncMock()
        mock_provider2.authenticate.return_value = UserContext(
            user_id="test_user",
            slack_user_id="U123456789"
        )
        
        auth_system = AuthSystem([mock_provider1, mock_provider2])
        context = await auth_system.authenticate_user("U123456789")
        
        # Should still succeed with second provider
        assert context is not None
        assert context.user_id == "test_user"


class TestAuthSystemFactory:
    """Test auth system factory function"""
    
    @async_test
    async def test_create_auth_system_database_only(self):
        """Test creating auth system with database provider only"""
        with patch('auth.get_database_manager') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            with patch('auth.UserMappingRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                
                auth_system = await create_auth_system()
                
                assert auth_system is not None
                assert len(auth_system.providers) == 1
                assert isinstance(auth_system.providers[0], DatabaseAuthProvider)
    
    @async_test
    async def test_create_auth_system_with_ldap(self):
        """Test creating auth system with LDAP provider"""
        with patch.dict('os.environ', {
            'LDAP_SERVER': 'ldap://localhost',
            'LDAP_BASE_DN': 'DC=company,DC=com',
            'LDAP_BIND_DN': 'CN=service,DC=company,DC=com',
            'LDAP_BIND_PASSWORD': 'password'
        }):
            with patch('auth.get_database_manager') as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                with patch('auth.UserMappingRepository') as mock_repo_class:
                    mock_repo = AsyncMock()
                    mock_repo_class.return_value = mock_repo
                    
                    auth_system = await create_auth_system()
                    
                    assert auth_system is not None
                    assert len(auth_system.providers) == 2
                    assert any(isinstance(p, LDAPAuthProvider) for p in auth_system.providers)
                    assert any(isinstance(p, DatabaseAuthProvider) for p in auth_system.providers)


class TestAuthIntegration:
    """Integration tests for authentication system"""
    
    @async_test
    async def test_full_authentication_flow(self, test_db_manager):
        """Test complete authentication flow"""
        # Setup user mapping
        user_repo = UserMappingRepository(test_db_manager)
        await user_repo.create_or_update_mapping(
            slack_user_id="U123456789",
            internal_user_id="test_user",
            ldap_id="test.user",
            email="test@example.com",
            full_name="Test User",
            roles=["analyst"],
            permissions=["query_execute", "query_view"]
        )
        
        # Create auth system
        db_provider = DatabaseAuthProvider(user_repo)
        auth_system = AuthSystem([db_provider])
        
        # Authenticate user
        context = await auth_system.authenticate_user("U123456789")
        
        assert context is not None
        assert context.user_id == "test_user"
        assert context.slack_user_id == "U123456789"
        assert context.ldap_id == "test.user"
        assert context.email == "test@example.com"
        assert "analyst" in context.roles
        assert "query_execute" in context.permissions
        
        # Test permissions
        assert auth_system.check_permission(context, "query_execute") is True
        assert auth_system.check_permission(context, "query_view") is True
        assert auth_system.check_permission(context, "admin_access") is False
    
    @async_test
    async def test_authentication_caching(self):
        """Test authentication result caching"""
        mock_provider = AsyncMock()
        mock_provider.authenticate.return_value = UserContext(
            user_id="test_user",
            slack_user_id="U123456789"
        )
        
        auth_system = AuthSystem([mock_provider])
        
        # First call
        context1 = await auth_system.authenticate_user("U123456789")
        
        # Second call (should use cache if implemented)
        context2 = await auth_system.authenticate_user("U123456789")
        
        assert context1 is not None
        assert context2 is not None
        assert context1.user_id == context2.user_id
        
        # Provider should be called for each request (no caching in current implementation)
        assert mock_provider.authenticate.call_count == 2
