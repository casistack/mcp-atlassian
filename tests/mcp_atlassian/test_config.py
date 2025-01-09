import pytest
from src.mcp_atlassian.config import ConfluenceConfig, JiraConfig

def test_confluence_config_initialization():
    config = ConfluenceConfig(
        url="https://example.atlassian.net",
        username="user@example.com",
        api_token="test_token"
    )
    assert config.url == "https://example.atlassian.net"
    assert config.username == "user@example.com"
    assert config.api_token == "test_token"

def test_jira_config_initialization():
    config = JiraConfig(
        url="https://example.atlassian.net",
        username="user@example.com",
        api_token="test_token"
    )
    assert config.url == "https://example.atlassian.net"
    assert config.username == "user@example.com"
    assert config.api_token == "test_token"

@pytest.mark.parametrize("url,expected", [
    ("https://example.atlassian.net", True),
    ("https://example.com", False)
])
def test_confluence_is_cloud(url, expected):
    config = ConfluenceConfig(
        url=url,
        username="user@example.com",
        api_token="test_token"
    )
    assert config.is_cloud == expected

@pytest.mark.parametrize("url,expected", [
    ("https://example.atlassian.net", True),
    ("https://example.com", False)
])
def test_jira_is_cloud(url, expected):
    config = JiraConfig(
        url=url,
        username="user@example.com",
        api_token="test_token"
    )
    assert config.is_cloud == expected
