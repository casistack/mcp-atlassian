import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

# Set testing mode
os.environ["TESTING"] = "true"

# Load test environment variables
test_env_path = Path(__file__).parent / ".env.test"
load_dotenv(test_env_path)

# Mock the server module
server_mock = MagicMock()
server_mock.tool = MagicMock()
sys.modules["mcp_atlassian.server"] = server_mock


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Automatically mock environment variables for all tests"""
    original_environ = dict(os.environ)
    os.environ.update(
        {
            "TESTING": "true",
            "CONFLUENCE_URL": "https://your-domain.atlassian.net",
            "CONFLUENCE_USERNAME": "test@example.com",
            "CONFLUENCE_API_TOKEN": "dummy-token",
            "JIRA_URL": "https://your-domain.atlassian.net",
            "JIRA_USERNAME": "test@example.com",
            "JIRA_API_TOKEN": "dummy-token",
        }
    )
    yield
    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.confluence_url = "https://your-domain.atlassian.net"
    config.confluence_username = "test@example.com"
    config.confluence_api_token = "dummy-token"
    config.jira_url = "https://your-domain.atlassian.net"
    config.jira_username = "test@example.com"
    config.jira_api_token = "dummy-token"
    return config


@pytest.fixture
def mock_confluence_client():
    client = MagicMock()
    return client


@pytest.fixture
def mock_jira_client():
    client = MagicMock()
    return client
