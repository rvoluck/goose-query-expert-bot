# Contributing to Goose Slackbot

Thank you for your interest in contributing to Goose Slackbot! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Commit Guidelines](#commit-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Reporting Issues](#reporting-issues)
10. [Feature Requests](#feature-requests)

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:
- Python 3.9 or higher
- Git installed and configured
- PostgreSQL 12+ for local development
- Redis 6+ for caching
- A GitHub account
- Familiarity with Slack API and Python async programming

### Finding Issues to Work On

1. **Good First Issues**: Look for issues labeled `good-first-issue`
2. **Help Wanted**: Check issues labeled `help-wanted`
3. **Bugs**: Issues labeled `bug` are always welcome
4. **Documentation**: Issues labeled `documentation` are great for getting started

## 💻 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/goose-slackbot.git
cd goose-slackbot

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/goose-slackbot.git
```

### 2. Create Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Setup Development Database

```bash
# Create development database
createdb goose_slackbot_dev

# Run migrations
python migrations.py

# Seed test data (optional)
python scripts/seed_dev_data.py
```

### 4. Configure Environment

```bash
# Copy environment template
cp env.example .env.dev

# Edit with development settings
# Use Socket Mode for development to avoid webhook setup
ENVIRONMENT=development
DEBUG=true
MOCK_MODE=true  # Optional: Use mock mode for testing without real integrations
```

### 5. Verify Setup

```bash
# Run tests
pytest tests/

# Run linters
black --check .
flake8 .
mypy .

# Start development server
python slack_bot.py
```

## 🔧 Making Changes

### Branch Naming Convention

Create a descriptive branch name:
- `feature/add-query-caching` - New features
- `fix/slack-connection-timeout` - Bug fixes
- `docs/update-api-documentation` - Documentation updates
- `refactor/improve-database-layer` - Code refactoring
- `test/add-auth-tests` - Test additions

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name
```

### Development Workflow

1. **Make Your Changes**
   ```bash
   # Edit files
   vim slack_bot.py
   
   # Test changes locally
   python slack_bot.py
   ```

2. **Write Tests**
   ```python
   # tests/test_your_feature.py
   import pytest
   from your_module import your_function
   
   def test_your_feature():
       result = your_function()
       assert result == expected_value
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test file
   pytest tests/test_your_feature.py
   
   # Run with coverage
   pytest tests/ --cov=. --cov-report=html
   ```

4. **Update Documentation**
   - Update README.md if adding features
   - Update API.md for API changes
   - Add docstrings to new functions
   - Update CHANGELOG.md

### Code Organization

```
goose-slackbot/
├── slack_bot.py          # Main Slack bot implementation
├── goose_client.py       # Goose integration client
├── database.py           # Database layer
├── auth.py               # Authentication system
├── config.py             # Configuration management
├── tests/                # Test files
│   ├── test_slack_bot.py
│   ├── test_goose_client.py
│   └── conftest.py       # Test fixtures
├── scripts/              # Utility scripts
├── k8s/                  # Kubernetes manifests
└── docs/                 # Additional documentation
```

## 🧪 Testing

### Test Categories

1. **Unit Tests**: Test individual functions and classes
   ```python
   def test_format_query_result():
       formatter = SlackResultFormatter()
       result = formatter.format_small_results(mock_result)
       assert "blocks" in result
   ```

2. **Integration Tests**: Test component interactions
   ```python
   @pytest.mark.integration
   async def test_database_query_flow():
       db = await get_database_manager()
       result = await db.fetch("SELECT 1")
       assert result[0]['?column?'] == 1
   ```

3. **End-to-End Tests**: Test complete workflows
   ```python
   @pytest.mark.e2e
   async def test_query_execution_flow():
       # Test complete query from Slack to result
       pass
   ```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m e2e

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test
pytest tests/test_slack_bot.py::test_format_query_result

# Run tests in parallel
pytest tests/ -n auto
```

### Writing Good Tests

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestSlackBot:
    """Test Slack bot functionality"""
    
    @pytest.fixture
    def mock_slack_client(self):
        """Fixture for mock Slack client"""
        client = AsyncMock()
        client.auth_test.return_value = {"user": "test_bot"}
        return client
    
    @pytest.mark.asyncio
    async def test_process_query_request(self, mock_slack_client):
        """Test query request processing"""
        # Arrange
        bot = GooseSlackBot()
        bot.app.client = mock_slack_client
        event = {
            "user": "U123",
            "text": "What was our revenue?",
            "channel": "C123"
        }
        
        # Act
        await bot._process_query_request(event, mock_say, mock_slack_client)
        
        # Assert
        assert mock_slack_client.chat_postMessage.called
        assert "revenue" in mock_slack_client.chat_postMessage.call_args[1]["text"]
```

### Test Coverage Requirements

- Minimum 80% code coverage for new code
- 100% coverage for critical paths (authentication, query execution)
- All public APIs must have tests
- Bug fixes must include regression tests

## 🎨 Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

```python
# Good: Clear, descriptive names
async def process_user_query(question: str, user_context: UserContext) -> QueryResult:
    """
    Process a user's natural language query.
    
    Args:
        question: The user's question in natural language
        user_context: Context about the user making the request
        
    Returns:
        QueryResult containing the query execution results
        
    Raises:
        AuthenticationError: If user is not authenticated
        PermissionError: If user lacks required permissions
    """
    # Implementation
    pass

# Bad: Unclear names, no documentation
async def proc_q(q, u):
    pass
```

### Code Formatting

```bash
# Format code with Black
black .

# Check formatting
black --check .

# Sort imports with isort
isort .

# Check with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class QueryResult:
    query_id: str
    sql: str
    success: bool
    rows: List[List[Any]]
    columns: List[str]
    execution_time: float
    error_message: Optional[str] = None

async def execute_query(
    sql: str,
    timeout: int = 300
) -> QueryResult:
    """Execute SQL query with timeout"""
    pass
```

### Documentation

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Short one-line description.
    
    Longer description explaining the function's purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Dictionary containing:
            - key1: Description of key1
            - key2: Description of key2
            
    Raises:
        ValueError: When param2 is negative
        RuntimeError: When operation fails
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["key1"])
        "value1"
    """
    pass
```

### Logging

Use structured logging with appropriate levels:

```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured logging with context
logger.info(
    "query_executed",
    query_id=query_id,
    user_id=user_id,
    execution_time=execution_time,
    row_count=row_count
)

# Bad: Unstructured logging
logger.info(f"Query {query_id} executed in {execution_time}s")
```

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(slack): add query refinement button

Add interactive button to allow users to refine their queries
without starting a new conversation. Includes modal for query
modification and context preservation.

Closes #123"

# Bug fix
git commit -m "fix(database): resolve connection pool exhaustion

Fix issue where database connections were not being properly
released, causing pool exhaustion under high load.

Fixes #456"

# Documentation
git commit -m "docs(api): update authentication examples

Add examples for JWT token generation and usage in API
documentation. Include error handling scenarios."
```

### Commit Best Practices

- Write clear, descriptive commit messages
- Keep commits focused on a single change
- Reference issue numbers when applicable
- Use present tense ("add feature" not "added feature")
- Separate subject from body with a blank line
- Limit subject line to 50 characters
- Wrap body at 72 characters

## 🔄 Pull Request Process

### Before Submitting

1. **Update Your Branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run All Checks**
   ```bash
   # Tests
   pytest tests/
   
   # Linting
   black --check .
   flake8 .
   mypy .
   
   # Security scan
   bandit -r .
   ```

3. **Update Documentation**
   - Update README.md if needed
   - Add/update docstrings
   - Update CHANGELOG.md

### Submitting Pull Request

1. **Push Your Branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Go to GitHub and create a pull request
   - Use the pull request template
   - Link related issues
   - Add appropriate labels

3. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests pass locally
   
   ## Related Issues
   Closes #123
   Related to #456
   
   ## Screenshots (if applicable)
   ```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline must pass
   - Code coverage must meet threshold
   - Linting must pass
   - Security scan must pass

2. **Code Review**
   - At least one approval required
   - Address all review comments
   - Keep discussions constructive

3. **Merging**
   - Squash commits if needed
   - Update commit message
   - Delete branch after merge

### Addressing Review Comments

```bash
# Make requested changes
git add .
git commit -m "address review comments"

# Update pull request
git push origin feature/your-feature-name

# If requested to squash commits
git rebase -i HEAD~3  # Interactive rebase last 3 commits
git push --force-with-lease origin feature/your-feature-name
```

## 🐛 Reporting Issues

### Before Reporting

1. **Search Existing Issues**: Check if issue already exists
2. **Verify Bug**: Ensure it's reproducible
3. **Check Documentation**: Review docs for known issues
4. **Test Latest Version**: Verify bug exists in latest version

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- Goose Slackbot Version: [e.g., 1.0.0]
- Deployment Method: [e.g., Docker, Kubernetes]

## Logs
```
Relevant log output
```

## Additional Context
Any other context about the problem

## Screenshots
If applicable, add screenshots
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear and concise description of the feature

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other solutions did you consider?

## Use Cases
Who would use this feature and how?

## Implementation Ideas
Any thoughts on implementation?

## Additional Context
Any other context or screenshots
```

## 📚 Additional Resources

### Documentation
- [README.md](README.md) - Project overview
- [SETUP.md](SETUP.md) - Setup instructions
- [API.md](API.md) - API documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

### External Resources
- [Slack API Documentation](https://api.slack.com/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Goose Documentation](https://github.com/block/goose)

### Community
- GitHub Issues: For bug reports and feature requests
- Slack Channel: #goose-slackbot-dev
- Email: dev-team@company.com

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing to Goose Slackbot! 🎉

---

**Questions?** Open an issue or reach out to the maintainers.
