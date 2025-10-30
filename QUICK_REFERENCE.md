# Quick Reference Card - Testing & Utilities

## 🚀 Most Common Commands

### Testing
```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-coverage     # With coverage report
make quick-test        # Fast validation
```

### Database
```bash
make db-migrate        # Run migrations
make db-status         # Check status
make backup            # Create backup
```

### Users
```bash
make users-list        # List all users
make users-export      # Export to CSV
```

### Monitoring
```bash
make monitor           # Health check
make monitor-metrics   # View metrics
```

### Code Quality
```bash
make lint              # Run linters
make format            # Format code
```

## 📝 Test Commands

### Run Tests
```bash
# Using Make
make test                    # All tests
make test-unit              # Unit only
make test-integration       # Integration only
make test-parallel          # Parallel execution

# Using pytest
pytest                      # All tests
pytest -m unit             # Unit tests
pytest -m integration      # Integration tests
pytest -v -s               # Verbose with output

# Using script
./scripts/run_tests.sh all
./scripts/run_tests.sh unit
./scripts/run_tests.sh lint
```

### Coverage
```bash
make test-coverage         # Generate coverage
open htmlcov/index.html   # View report
```

## 🗄️ Database Commands

### Migrations
```bash
# Status and execution
./scripts/db_migrate.py status
./scripts/db_migrate.py up
./scripts/db_migrate.py down --version V002

# Create new
./scripts/db_migrate.py create --name "add_feature"
make db-create-migration NAME=add_feature
```

### Backup
```bash
# Create
./scripts/backup_restore.py backup
./scripts/backup_restore.py backup --compress

# List and restore
./scripts/backup_restore.py list
./scripts/backup_restore.py restore --file backup.sql.gz

# Cleanup
./scripts/backup_restore.py cleanup --keep-days 30
```

## 👥 User Management

### Basic Operations
```bash
# List
./scripts/user_manager.py list
./scripts/user_manager.py list --all

# Get details
./scripts/user_manager.py get --slack-user-id U123

# Create
./scripts/user_manager.py create \
    --slack-user-id U123 \
    --internal-user-id user1 \
    --email user@example.com \
    --roles analyst
```

### Roles & Permissions
```bash
# Add role
./scripts/user_manager.py add-role \
    --slack-user-id U123 --role admin

# Remove role
./scripts/user_manager.py remove-role \
    --slack-user-id U123 --role viewer

# Add permission
./scripts/user_manager.py add-permission \
    --slack-user-id U123 --permission admin_access
```

### Bulk Operations
```bash
# Import from CSV
./scripts/user_manager.py import --file users.csv

# Export to CSV
./scripts/user_manager.py export --file backup.csv
```

## 📊 Monitoring

### Health Checks
```bash
# Single check
./scripts/monitor.py check

# Continuous
./scripts/monitor.py monitor --interval 60

# Export JSON
./scripts/monitor.py json
```

### Metrics
```bash
# View metrics
./scripts/monitor.py metrics --hours 24

# Using Make
make monitor-metrics
```

## 🔧 Development

### Setup
```bash
make install           # Install dependencies
make setup            # Setup project
make init             # Complete initialization
```

### Running
```bash
make dev              # Start dev server
make dev-watch        # With auto-reload
make shell            # Python shell
```

### Docker
```bash
make docker-build     # Build image
make docker-up        # Start services
make docker-down      # Stop services
make docker-logs      # View logs
```

## 📦 Load Testing

### Locust
```bash
# Web interface
make load-test
# Open http://localhost:8089

# Headless
make load-test-headless

# Custom
cd tests/load
locust -f locustfile.py \
    --host http://localhost:3000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m
```

## 🎨 Code Quality

### Formatting
```bash
make format           # Format code
make format-check     # Check only
```

### Linting
```bash
make lint             # All linters
make type-check       # Type checking
make security-check   # Security audit
```

## 🔄 CI/CD

### Local CI
```bash
make ci               # Run full CI pipeline
make quick-check      # Quick quality check
```

### Deployment
```bash
make deploy-staging
make deploy-production
```

## 📋 File Locations

```
tests/                          # All tests
  unit/                        # Unit tests
  integration/                 # Integration tests
  load/                        # Load tests

scripts/                       # Utility scripts
  db_migrate.py               # Migrations
  user_manager.py             # User management
  monitor.py                  # Monitoring
  backup_restore.py           # Backup/restore
  run_tests.sh                # Test runner

migrations/                    # Migration files
backups/                      # Backup files
archives/                     # Archived data
logs/                         # Application logs
```

## 🔑 Environment Variables

### Required
```bash
DATABASE_URL=postgresql://localhost/db
SLACK_BOT_TOKEN=xoxb-token
SLACK_APP_TOKEN=xapp-token
SLACK_SIGNING_SECRET=secret
JWT_SECRET_KEY=jwt-secret
ENCRYPTION_KEY=encryption-key
```

### Testing
```bash
ENVIRONMENT=test
MOCK_MODE=true
```

## 🎯 Test Markers

```bash
pytest -m unit              # Unit tests
pytest -m integration       # Integration tests
pytest -m load             # Load tests
pytest -m slow             # Slow tests
pytest -m smoke            # Smoke tests
pytest -m "not slow"       # Skip slow tests
```

## 📊 Coverage Targets

- Unit tests: > 90%
- Integration tests: > 70%
- Overall: > 80%

## ⚡ Quick Workflows

### New Feature
```bash
1. make test-unit              # Ensure tests pass
2. # Write code
3. # Write tests
4. make test-unit              # Verify new tests
5. make lint                   # Check quality
6. make test-coverage          # Check coverage
```

### Database Change
```bash
1. make backup                 # Backup first
2. make db-create-migration NAME=change
3. # Edit migration file
4. make db-migrate            # Apply migration
5. make db-status             # Verify
```

### User Management
```bash
1. make users-export          # Backup users
2. # Make changes
3. make users-list            # Verify
```

### Deployment
```bash
1. make test                  # All tests pass
2. make lint                  # Quality check
3. make backup                # Backup database
4. make deploy-staging        # Deploy to staging
5. # Test staging
6. make deploy-production     # Deploy to prod
```

## 🆘 Emergency Commands

### Rollback Migration
```bash
./scripts/db_migrate.py down --version V001
```

### Restore Backup
```bash
./scripts/backup_restore.py restore \
    --file backups/latest.sql.gz \
    --drop-existing
```

### Check System Health
```bash
make monitor
```

### View Logs
```bash
make logs
make logs-error
```

## 📞 Help

```bash
make help              # Show all commands
pytest --help         # Pytest help
./scripts/db_migrate.py --help
./scripts/user_manager.py --help
./scripts/monitor.py --help
./scripts/backup_restore.py --help
```

## 📚 Documentation

- `tests/README.md` - Testing guide
- `TESTING_UTILITIES_GUIDE.md` - Complete utilities guide
- `TESTING_FRAMEWORK_SUMMARY.md` - Implementation summary
- `README.md` - Main project documentation

---

**Tip**: Use `make help` to see all available commands!
