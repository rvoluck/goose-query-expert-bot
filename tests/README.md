# Goose Slackbot Testing Framework

Comprehensive testing framework for the Goose Slackbot project, including unit tests, integration tests, load tests, and utility scripts.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Utility Scripts](#utility-scripts)
- [CI/CD Integration](#cicd-integration)
- [Writing Tests](#writing-tests)
- [Best Practices](#best-practices)

## Overview

The testing framework provides:

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: End-to-end workflow testing
- **Load Tests**: Performance and stress testing
- **Coverage Reports**: Code coverage analysis
- **Utility Scripts**: Database migrations, user management, monitoring, backups

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── requirements.txt            # Testing dependencies
├── README.md                   # This file
│
├── unit/                       # Unit tests
│   ├── test_auth.py           # Authentication tests
│   ├── test_config.py         # Configuration tests
│   ├── test_database.py       # Database operations tests
│   ├── test_goose_client.py   # Goose client tests
│   └── test_slack_bot.py      # Slack bot tests
│
├── integration/                # Integration tests
│   ├── test_database_integration.py
│   ├── test_end_to_end.py     # Complete workflow tests
│   └── test_full_workflow.py
│
├── load/                       # Load and performance tests
│   ├── locustfile.py          # Locust load testing
│   ├── load_test_runner.py   # Custom load test runner
│   └── stress_test.py         # Stress testing
│
├── fixtures/                   # Test data fixtures
├── mocks/                      # Mock objects
└── helpers/                    # Test helper functions
```

## Running Tests

### Quick Start

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test types
./scripts/run_tests.sh unit          # Unit tests only
./scripts/run_tests.sh integration   # Integration tests only
./scripts/run_tests.sh load          # Load tests only

# Run with coverage
./scripts/run_tests.sh all true      # With coverage report
./scripts/run_tests.sh all false     # Without coverage

# Run tests in parallel
./scripts/run_tests.sh parallel

# Run specific test file
./scripts/run_tests.sh tests/unit/test_config.py

# Run code quality checks
./scripts/run_tests.sh lint
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test function
pytest tests/unit/test_auth.py::TestAuthManager::test_authenticate_user

# Run tests with markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

## Test Categories

Tests are organized using pytest markers:

### Unit Tests (`@pytest.mark.unit`)
- Fast execution (< 1 second per test)
- No external dependencies
- Isolated component testing
- Mocked external services

### Integration Tests (`@pytest.mark.integration`)
- Test complete workflows
- Require running services (database, Redis)
- Test component interactions
- Slower execution

### Load Tests (`@pytest.mark.load`)
- Performance testing
- Stress testing
- Concurrent user simulation
- Requires running application

### Other Markers
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.smoke`: Quick validation tests
- `@pytest.mark.database`: Requires database
- `@pytest.mark.redis`: Requires Redis
- `@pytest.mark.slack`: Requires Slack API
- `@pytest.mark.security`: Security tests

## Utility Scripts

### Database Migration (`db_migrate.py`)

Manage database schema migrations:

```bash
# Initialize migration tracking
./scripts/db_migrate.py init

# Show migration status
./scripts/db_migrate.py status

# Run migrations
./scripts/db_migrate.py up

# Rollback to version
./scripts/db_migrate.py down --version V002

# Create new migration
./scripts/db_migrate.py create --name "add_user_roles"

# Validate migrations
./scripts/db_migrate.py validate
```

### User Management (`user_manager.py`)

Manage users, roles, and permissions:

```bash
# List all users
./scripts/user_manager.py list

# Get user details
./scripts/user_manager.py get --slack-user-id U123456789

# Create user
./scripts/user_manager.py create \
    --slack-user-id U123456789 \
    --internal-user-id user123 \
    --email user@example.com \
    --full-name "John Doe" \
    --roles analyst,viewer

# Update user
./scripts/user_manager.py update \
    --slack-user-id U123456789 \
    --full-name "Jane Doe" \
    --roles analyst,admin

# Add role to user
./scripts/user_manager.py add-role \
    --slack-user-id U123456789 \
    --role admin

# Remove role from user
./scripts/user_manager.py remove-role \
    --slack-user-id U123456789 \
    --role viewer

# Delete user (soft delete)
./scripts/user_manager.py delete --slack-user-id U123456789

# Delete user (hard delete)
./scripts/user_manager.py delete --slack-user-id U123456789 --hard-delete

# Bulk import from CSV
./scripts/user_manager.py import --file users.csv

# Export to CSV
./scripts/user_manager.py export --file users_backup.csv
```

### Monitoring (`monitor.py`)

Monitor system health and metrics:

```bash
# Run health checks
./scripts/monitor.py check

# Get system metrics
./scripts/monitor.py metrics --hours 24

# Continuous monitoring
./scripts/monitor.py monitor --interval 60

# Export health check as JSON
./scripts/monitor.py json
```

Health checks include:
- Database connectivity and performance
- Redis connectivity
- Goose service availability
- Slack API connectivity
- Disk space usage
- Memory usage
- CPU usage

### Backup & Restore (`backup_restore.py`)

Database backup and restore operations:

```bash
# Create backup
./scripts/backup_restore.py backup

# Create compressed backup
./scripts/backup_restore.py backup --compress

# Create schema-only backup
./scripts/backup_restore.py backup --schema-only

# List available backups
./scripts/backup_restore.py list

# Restore from backup
./scripts/backup_restore.py restore --file backups/backup_20240101_120000.sql.gz

# Restore with drop existing
./scripts/backup_restore.py restore \
    --file backups/backup_20240101_120000.sql.gz \
    --drop-existing

# Clean up old backups
./scripts/backup_restore.py cleanup --keep-days 30 --keep-count 10

# Archive old queries
./scripts/backup_restore.py archive-queries --archive-days 90

# Archive old sessions
./scripts/backup_restore.py archive-sessions --archive-days 180
```

## Load Testing

### Using Locust

```bash
# Start Locust web interface
cd tests/load
locust -f locustfile.py --host http://localhost:3000

# Open browser to http://localhost:8089
# Configure number of users and spawn rate

# Run headless load test
locust -f locustfile.py \
    --host http://localhost:3000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless
```

### Load Test Scenarios

The load testing framework includes:

1. **SlackBotUser**: Normal user behavior
   - Simple queries (10x weight)
   - Complex queries (5x weight)
   - Query history (3x weight)
   - Popular queries (2x weight)

2. **HeavyUser**: Power user with high volume
   - Rapid queries with minimal wait time
   - Simulates analyst workload

3. **BurstUser**: Burst traffic patterns
   - Sudden spikes in query volume
   - Tests rate limiting and scaling

4. **Load Shapes**:
   - **StepLoadShape**: Gradual increase
   - **SpikeLoadShape**: Periodic spikes
   - **WaveLoadShape**: Sine wave pattern

## CI/CD Integration

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
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      
      - name: Run tests
        run: ./scripts/run_tests.sh all
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
          REDIS_URL: redis://localhost:6379/15
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### GitLab CI

```yaml
stages:
  - test
  - report

test:
  stage: test
  image: python:3.11
  
  services:
    - postgres:14
    - redis:7
  
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres/test
    REDIS_URL: redis://redis:6379/15
  
  before_script:
    - pip install -r requirements.txt
    - pip install -r tests/requirements.txt
  
  script:
    - ./scripts/run_tests.sh all
  
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 1 week
```

## Writing Tests

### Test Structure

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
        # Arrange
        component = MyComponent(mock_dependency)
        
        # Act
        result = await component.do_async_something()
        
        # Assert
        assert result is not None
        mock_dependency.method.assert_called_once()
```

### Using Fixtures

```python
@pytest.fixture
async def db_manager():
    """Database manager fixture"""
    config = DatabaseConfig(dsn="postgresql://localhost/test")
    manager = DatabaseManager(config)
    await manager.initialize()
    
    yield manager
    
    await manager.close()

@pytest.fixture
def mock_slack_client():
    """Mock Slack client fixture"""
    client = MagicMock()
    client.chat_postMessage = AsyncMock()
    return client
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_operation(db_manager):
    """Test async database operation"""
    result = await db_manager.execute_query("SELECT 1")
    assert result is not None
```

### Mocking External Services

```python
@patch('slack_bot.SlackClient')
async def test_with_mocked_slack(mock_slack):
    """Test with mocked Slack client"""
    mock_slack.return_value.chat_postMessage.return_value = {"ok": True}
    
    bot = SlackBot()
    await bot.send_message("C123", "Hello")
    
    mock_slack.return_value.chat_postMessage.assert_called_once()
```

## Best Practices

### 1. Test Naming
- Use descriptive names: `test_user_authentication_with_valid_credentials`
- Follow pattern: `test_<what>_<condition>_<expected_result>`

### 2. Test Organization
- One test class per component
- Group related tests together
- Use markers for categorization

### 3. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 4. Assertions
- Use specific assertions
- One logical assertion per test
- Include helpful assertion messages

### 5. Mocking
- Mock external dependencies
- Don't mock the system under test
- Use appropriate mock types (Mock, MagicMock, AsyncMock)

### 6. Coverage
- Aim for >80% code coverage
- Focus on critical paths
- Don't chase 100% coverage blindly

### 7. Performance
- Keep unit tests fast (< 1 second)
- Use `@pytest.mark.slow` for slow tests
- Run slow tests separately in CI

### 8. Documentation
- Document complex test scenarios
- Explain why, not what
- Include examples in docstrings

## Troubleshooting

### Common Issues

**Tests fail with database connection error:**
```bash
# Ensure PostgreSQL is running
pg_isready

# Check DATABASE_URL
echo $DATABASE_URL

# Create test database
createdb goose_slackbot_test
```

**Tests fail with Redis connection error:**
```bash
# Ensure Redis is running
redis-cli ping

# Check REDIS_URL
echo $REDIS_URL
```

**Import errors:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements.txt

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async tests not working:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add appropriate markers
3. Update this README if needed
4. Ensure tests pass locally
5. Check code coverage

## Support

For issues or questions:
- Check the troubleshooting section
- Review existing tests for examples
- Consult the main project documentation
