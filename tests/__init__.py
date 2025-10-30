"""
Test package for Goose Slackbot
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/goose_slackbot_test")
TEST_SLACK_BOT_TOKEN = "xoxb-test-token"
TEST_SLACK_SIGNING_SECRET = "test-signing-secret"
TEST_SLACK_APP_TOKEN = "xapp-test-token"

# Common test utilities
def async_test(func):
    """Decorator for async test functions"""
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper

# Test data constants
SAMPLE_USER_ID = "U123456789"
SAMPLE_CHANNEL_ID = "C987654321"
SAMPLE_QUERY_ID = "query_12345"
SAMPLE_SESSION_ID = "session_67890"
