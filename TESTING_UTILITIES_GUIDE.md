# Testing Framework and Utility Scripts Guide

Complete guide to the testing framework and utility scripts for Goose Slackbot.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Testing Framework](#testing-framework)
- [Utility Scripts](#utility-scripts)
- [Makefile Commands](#makefile-commands)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## 🎯 Overview

This project includes a comprehensive testing framework and utility scripts covering:

### Testing Components
1. **Unit Tests** - Fast, isolated component tests
2. **Integration Tests** - End-to-end workflow tests
3. **Load Tests** - Performance and stress testing
4. **Coverage Reports** - Code coverage analysis

### Utility Scripts
1. **Database Migration** - Schema version management
2. **User Management** - User, role, and permission management
3. **Monitoring** - Health checks and metrics
4. **Backup & Restore** - Database backup and data archival

## 🚀 Quick Start

### Initial Setup

```bash
# Install dependencies
make install

# Setup project structure
make setup

# Initialize database
make db-migrate

# Run tests
make test
```

### Common Commands

```bash
# Testing
make test              # Run all tests
make test-unit         # Unit tests only
make test-coverage     # With coverage report

# Database
make db-migrate        # Run migrations
make db-status         # Check migration status
make backup            # Create backup

# Monitoring
make monitor           # Health checks
make monitor-metrics   # System metrics

# Code Quality
make lint              # Run linters
make format            # Format code
```

## 🧪 Testing Framework

### Directory Structure

```
tests/
├── unit/                       # Unit tests
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_goose_client.py
│   └── test_slack_bot.py
├── integration/                # Integration tests
│   ├── test_database_integration.py
│   ├── test_end_to_end.py
│   └── test_full_workflow.py
├── load/                       # Load tests
│   ├── locustfile.py
│   ├── load_test_runner.py
│   └── stress_test.py
├── conftest.py                 # Shared fixtures
├── requirements.txt            # Test dependencies
└── README.md                   # Testing documentation
```

### Running Tests

#### Using Make

```bash
# All tests
make test

# Specific test types
make test-unit
make test-integration
make test-load

# With coverage
make test-coverage

# In parallel
make test-parallel
```

#### Using pytest directly

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_config.py

# Specific test function
pytest tests/unit/test_config.py::TestSettings::test_settings_with_valid_env

# With markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests

# With coverage
pytest --cov=. --cov-report=html

# Parallel execution
pytest -n auto

# Verbose output
pytest -v -s
```

#### Using test runner script

```bash
# Run all tests
./scripts/run_tests.sh all

# Run specific types
./scripts/run_tests.sh unit
./scripts/run_tests.sh integration
./scripts/run_tests.sh load

# With/without coverage
./scripts/run_tests.sh all true   # With coverage
./scripts/run_tests.sh all false  # Without coverage

# Run specific file
./scripts/run_tests.sh tests/unit/test_config.py

# Code quality checks
./scripts/run_tests.sh lint
```

### Test Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # End-to-end tests
@pytest.mark.load          # Performance tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.smoke         # Quick validation
@pytest.mark.database      # Requires database
@pytest.mark.redis         # Requires Redis
@pytest.mark.slack         # Requires Slack API
@pytest.mark.security      # Security tests
```

### Writing Tests

#### Basic Test Structure

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.unit
class TestMyComponent:
    """Test suite for MyComponent"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        component = MyComponent()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, mock_dependency):
        """Test async functionality"""
        component = MyComponent(mock_dependency)
        result = await component.do_async_something()
        assert result is not None
```

#### Using Fixtures

```python
@pytest.fixture
async def db_manager():
    """Database manager fixture"""
    config = DatabaseConfig(dsn="postgresql://localhost/test")
    manager = DatabaseManager(config)
    await manager.initialize()
    yield manager
    await manager.close()
```

### Load Testing

#### Using Locust

```bash
# Start Locust web interface
make load-test

# Open browser to http://localhost:8089
# Configure users and spawn rate

# Headless mode
make load-test-headless
```

#### Load Test Scenarios

The framework includes multiple user types:

1. **SlackBotUser** - Normal user behavior
2. **HeavyUser** - High-volume power user
3. **BurstUser** - Burst traffic patterns

And load shapes:

1. **StepLoadShape** - Gradual increase
2. **SpikeLoadShape** - Periodic spikes
3. **WaveLoadShape** - Sine wave pattern

## 🛠️ Utility Scripts

### 1. Database Migration (`db_migrate.py`)

Manage database schema versions and migrations.

#### Commands

```bash
# Initialize migration tracking
./scripts/db_migrate.py init

# Show current status
./scripts/db_migrate.py status

# Run migrations
./scripts/db_migrate.py up

# Rollback to specific version
./scripts/db_migrate.py down --version V002

# Create new migration
./scripts/db_migrate.py create --name "add_user_roles"

# Validate migrations
./scripts/db_migrate.py validate
```

#### Using Make

```bash
make db-migrate                          # Run migrations
make db-status                           # Show status
make db-rollback                         # Rollback last
make db-create-migration NAME=add_roles  # Create migration
```

#### Migration File Format

```sql
-- Migration: Add User Roles
-- Version: V002
-- Created: 2024-01-01

-- UP
ALTER TABLE user_mappings ADD COLUMN role VARCHAR(50);
CREATE INDEX idx_user_mappings_role ON user_mappings(role);

-- DOWN
DROP INDEX idx_user_mappings_role;
ALTER TABLE user_mappings DROP COLUMN role;
```

### 2. User Management (`user_manager.py`)

Manage users, roles, and permissions.

#### Commands

```bash
# List users
./scripts/user_manager.py list
./scripts/user_manager.py list --all  # Include inactive

# Get user details
./scripts/user_manager.py get --slack-user-id U123456789

# Create user
./scripts/user_manager.py create \
    --slack-user-id U123456789 \
    --internal-user-id user123 \
    --email user@example.com \
    --full-name "John Doe" \
    --roles analyst,viewer \
    --permissions query_execute,query_share

# Update user
./scripts/user_manager.py update \
    --slack-user-id U123456789 \
    --full-name "Jane Doe" \
    --roles analyst,admin

# Manage roles
./scripts/user_manager.py add-role \
    --slack-user-id U123456789 \
    --role admin

./scripts/user_manager.py remove-role \
    --slack-user-id U123456789 \
    --role viewer

# Manage permissions
./scripts/user_manager.py add-permission \
    --slack-user-id U123456789 \
    --permission admin_access

./scripts/user_manager.py remove-permission \
    --slack-user-id U123456789 \
    --permission query_delete

# Delete user
./scripts/user_manager.py delete --slack-user-id U123456789
./scripts/user_manager.py delete --slack-user-id U123456789 --hard-delete

# Bulk operations
./scripts/user_manager.py import --file users.csv
./scripts/user_manager.py export --file users_backup.csv
```

#### Using Make

```bash
make users-list                                    # List all users
make users-create SLACK_ID=U123 INTERNAL_ID=user1 # Create user
make users-export                                  # Export to CSV
```

#### CSV Format for Import

```csv
slack_user_id,internal_user_id,email,full_name,ldap_id,roles,permissions,is_active
U123456789,user123,user@example.com,John Doe,john.doe,analyst,query_execute,true
U987654321,user456,admin@example.com,Jane Admin,jane.admin,"analyst,admin","query_execute,admin_access",true
```

### 3. Monitoring (`monitor.py`)

System health checks and metrics collection.

#### Commands

```bash
# Run health checks
./scripts/monitor.py check

# Get system metrics
./scripts/monitor.py metrics --hours 24

# Continuous monitoring
./scripts/monitor.py monitor --interval 60

# Export as JSON
./scripts/monitor.py json
```

#### Using Make

```bash
make monitor                # Health checks
make monitor-metrics        # System metrics
make monitor-continuous     # Continuous monitoring
```

#### Health Checks

The monitor checks:

- ✓ Database connectivity and performance
- ✓ Redis connectivity
- ✓ Goose service availability
- ✓ Slack API connectivity
- ✓ Disk space usage
- ✓ Memory usage
- ✓ CPU usage

#### Metrics Collected

- Total queries (last 24 hours)
- Success/failure rates
- Average execution time
- Active sessions
- Top users by query count
- Database size and connections

### 4. Backup & Restore (`backup_restore.py`)

Database backup, restore, and data archival.

#### Commands

```bash
# Create backup
./scripts/backup_restore.py backup
./scripts/backup_restore.py backup --compress
./scripts/backup_restore.py backup --schema-only

# List backups
./scripts/backup_restore.py list

# Restore backup
./scripts/backup_restore.py restore \
    --file backups/backup_20240101_120000.sql.gz

# Restore with drop existing
./scripts/backup_restore.py restore \
    --file backups/backup_20240101_120000.sql.gz \
    --drop-existing

# Clean up old backups
./scripts/backup_restore.py cleanup \
    --keep-days 30 \
    --keep-count 10

# Archive old data
./scripts/backup_restore.py archive-queries --archive-days 90
./scripts/backup_restore.py archive-sessions --archive-days 180
```

#### Using Make

```bash
make backup                              # Create backup
make backup-list                         # List backups
make backup-restore FILE=backup.sql.gz   # Restore backup
make backup-cleanup                      # Clean old backups
make archive-data                        # Archive old data
```

#### Backup Strategy

Recommended backup schedule:

- **Daily**: Full database backup (compressed)
- **Weekly**: Schema-only backup
- **Monthly**: Archive old data (>90 days)
- **Retention**: Keep 30 days of daily backups, 10 most recent

## 📝 Makefile Commands

The Makefile provides convenient shortcuts for all operations.

### Installation & Setup

```bash
make install        # Install dependencies
make install-dev    # Install dev dependencies
make setup          # Initial project setup
make init           # Complete initialization
```

### Testing

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-load         # Load tests
make test-parallel     # Parallel execution
make test-coverage     # With coverage report
make quick-test        # Quick validation (unit tests)
```

### Code Quality

```bash
make lint           # Run all linters
make format         # Format code
make format-check   # Check formatting
make type-check     # Type checking
make security-check # Security audit
make quick-check    # Quick quality check
```

### Database

```bash
make db-migrate                          # Run migrations
make db-rollback                         # Rollback migration
make db-status                           # Migration status
make db-create-migration NAME=add_roles  # Create migration
```

### User Management

```bash
make users-list                                    # List users
make users-create SLACK_ID=U123 INTERNAL_ID=user1 # Create user
make users-export                                  # Export users
```

### Monitoring

```bash
make monitor           # Health checks
make monitor-metrics   # System metrics
make monitor-continuous # Continuous monitoring
```

### Backup & Restore

```bash
make backup                              # Create backup
make backup-list                         # List backups
make backup-restore FILE=backup.sql.gz   # Restore
make backup-cleanup                      # Clean old backups
make archive-data                        # Archive old data
```

### Docker

```bash
make docker-build   # Build image
make docker-up      # Start services
make docker-down    # Stop services
make docker-logs    # View logs
make docker-clean   # Clean resources
```

### Development

```bash
make dev            # Start dev server
make dev-watch      # Auto-reload dev server
make shell          # Python shell with context
make logs           # View logs
make logs-error     # Error logs only
```

### Deployment

```bash
make deploy-staging     # Deploy to staging
make deploy-production  # Deploy to production
make k8s-apply         # Apply K8s manifests
make k8s-status        # K8s status
```

### Utilities

```bash
make clean          # Clean generated files
make clean-all      # Clean everything
make version        # Show versions
make env-check      # Check environment
make help           # Show all commands
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
      redis:
        image: redis:7
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: make install
      
      - name: Run tests
        run: make test-coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
stages:
  - test
  - deploy

test:
  stage: test
  image: python:3.11
  services:
    - postgres:14
    - redis:7
  script:
    - make install
    - make test-coverage
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Pre-commit Hooks

```bash
# Install pre-commit
make install-dev

# Hooks will run automatically on commit
# Or run manually:
pre-commit run --all-files
```

## ✅ Best Practices

### Testing

1. **Write tests first** - TDD approach
2. **Keep tests fast** - Unit tests < 1 second
3. **Use descriptive names** - `test_user_authentication_with_valid_credentials`
4. **One assertion per test** - Focus on single behavior
5. **Use fixtures** - Share setup code
6. **Mock external services** - Isolate tests
7. **Test edge cases** - Not just happy path
8. **Maintain coverage** - Aim for >80%

### Database Migrations

1. **Always reversible** - Include DOWN migration
2. **Test migrations** - On copy of production data
3. **Small changes** - One logical change per migration
4. **Backup first** - Before running migrations
5. **Version control** - Commit migrations with code

### User Management

1. **Soft delete** - Default to deactivation
2. **Audit trail** - Log all changes
3. **Bulk operations** - Use CSV for mass updates
4. **Regular exports** - Backup user data
5. **Validate roles** - Check permissions before granting

### Monitoring

1. **Continuous monitoring** - Run health checks regularly
2. **Set thresholds** - Define acceptable limits
3. **Alert on failures** - Integrate with alerting system
4. **Track trends** - Monitor metrics over time
5. **Document baselines** - Know normal behavior

### Backups

1. **Automated backups** - Schedule daily backups
2. **Test restores** - Verify backups work
3. **Multiple locations** - Store offsite
4. **Retention policy** - Balance cost and recovery needs
5. **Archive old data** - Keep database size manageable

## 📚 Additional Resources

- [Testing README](tests/README.md) - Detailed testing documentation
- [pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)

## 🆘 Troubleshooting

### Tests Failing

```bash
# Check environment
make env-check

# Verify services running
docker-compose ps

# Check database
psql $DATABASE_URL -c "SELECT 1"

# Check Redis
redis-cli -u $REDIS_URL ping

# Run with verbose output
pytest -v -s
```

### Migration Issues

```bash
# Check current version
make db-status

# Validate migrations
./scripts/db_migrate.py validate

# Manual rollback if needed
./scripts/db_migrate.py down --version V001
```

### Backup/Restore Issues

```bash
# Check PostgreSQL tools installed
which pg_dump
which psql

# Verify database URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version()"
```

## 📞 Support

For issues or questions:
1. Check this guide and documentation
2. Review test examples
3. Check troubleshooting section
4. Consult main project README

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
