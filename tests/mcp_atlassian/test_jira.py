import pytest
from unittest.mock import MagicMock, patch
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.types import Document
from mcp_atlassian.attachments import AttachmentInfo


@pytest.mark.asyncio
async def test_create_issue(mock_config, mock_jira_client):
    # Initialize JiraFetcher without config
    fetcher = JiraFetcher()
    fetcher.jira = mock_jira_client

    # Mock response for successful issue creation
    mock_jira_client.issue_create.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000",
        "fields": {
            "summary": "Test Issue",
            "description": "Test description",
            "issuetype": {"name": "Task"},
            "status": {"name": "To Do"},
            "created": "2024-01-09T12:00:00Z",
        },
    }

    # Mock get_issue response for the created issue
    mock_jira_client.issue.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "fields": {
            "summary": "Test Issue",
            "description": "Test description",
            "issuetype": {"name": "Task"},
            "status": {"name": "To Do"},
            "created": "2024-01-09T12:00:00Z",
        },
    }

    result = fetcher.create_issue(
        project_key="TEST",
        summary="Test Issue",
        description="Test description",
        issue_type="Task",
    )

    assert isinstance(result, Document)
    assert result.metadata["key"] == "TEST-1"
    assert result.metadata["title"] == "Test Issue"
    mock_jira_client.issue_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_issue(mock_config, mock_jira_client):
    # Initialize JiraFetcher without config
    fetcher = JiraFetcher()
    fetcher.jira = mock_jira_client

    # Mock get_issue response for the original issue
    mock_jira_client.issue.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "fields": {
            "summary": "Updated Test Issue",
            "description": "Updated description",
            "issuetype": {"name": "Task"},
            "status": {"name": "To Do"},
            "created": "2024-01-09T12:00:00Z",
        },
    }

    # Mock update_issue response
    mock_jira_client.issue_update.return_value = (
        None  # Jira returns None on successful update
    )

    result = fetcher.update_issue(
        issue_key="TEST-1",
        summary="Updated Test Issue",
        description="Updated description",
    )

    assert isinstance(result, Document)
    assert result.metadata["key"] == "TEST-1"
    assert result.metadata["title"] == "Updated Test Issue"
    mock_jira_client.issue_update.assert_called_once()


@pytest.mark.asyncio
async def test_get_issue_transitions(mock_config, mock_jira_client):
    # Initialize JiraFetcher without config
    fetcher = JiraFetcher()
    fetcher.jira = mock_jira_client

    # Mock get_transitions response
    mock_jira_client.get_issue_transitions.return_value = {
        "transitions": [
            {"id": "11", "name": "To Do"},
            {"id": "21", "name": "In Progress"},
        ]
    }

    transitions = fetcher.get_issue_transitions("TEST-1")
    assert isinstance(transitions, dict)
    assert len(transitions["transitions"]) == 2
    assert transitions["transitions"][0]["name"] == "To Do"
    mock_jira_client.get_issue_transitions.assert_called_once()


@pytest.mark.asyncio
async def test_attachment_handling(mock_config, mock_jira_client):
    # Initialize JiraFetcher without config
    fetcher = JiraFetcher()
    fetcher.jira = mock_jira_client

    # Mock attachment response
    mock_jira_client.add_attachment.return_value = [
        {"id": "10001", "filename": "test.txt", "size": 1024}
    ]

    # Create a temporary test file
    with open("test.txt", "wb") as f:
        f.write(b"test content")

    # Test adding attachment
    result = fetcher.add_attachment("TEST-1", "test.txt")
    assert isinstance(result, AttachmentInfo)
    assert result.id == "10001"
    mock_jira_client.add_attachment.assert_called_once()

    # Clean up
    import os

    os.remove("test.txt")


@pytest.mark.asyncio
async def test_search_issues(mock_config, mock_jira_client):
    # Initialize JiraFetcher without config
    fetcher = JiraFetcher()
    fetcher.jira = mock_jira_client

    # Mock jql search response
    mock_jira_client.jql.return_value = {
        "issues": [
            {
                "id": "10000",
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Issue",
                    "description": "Test description",
                    "issuetype": {"name": "Task"},
                    "status": {"name": "To Do"},
                    "created": "2024-01-09T12:00:00Z",
                },
            }
        ],
        "total": 1,
    }

    # Mock get_issue response for the found issue
    mock_jira_client.issue.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "fields": {
            "summary": "Test Issue",
            "description": "Test description",
            "issuetype": {"name": "Task"},
            "status": {"name": "To Do"},
            "created": "2024-01-09T12:00:00Z",
        },
    }

    results = fetcher.search_issues("project = TEST")
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], Document)
    assert results[0].metadata["key"] == "TEST-1"
    mock_jira_client.jql.assert_called_once()
