import pytest
from unittest.mock import MagicMock, patch
from mcp_atlassian.jira import JiraFetcher


@pytest.mark.asyncio
async def test_create_issue(mock_config, mock_jira_client):
    fetcher = JiraFetcher(mock_config)
    fetcher.client = mock_jira_client

    # Mock response for successful issue creation
    mock_jira_client.create_issue.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000",
    }

    result = await fetcher.create_issue(
        project_key="TEST",
        summary="Test Issue",
        description="Test description",
        issue_type="Task",
    )

    assert result["key"] == "TEST-1"
    assert result["id"] == "10000"
    mock_jira_client.create_issue.assert_called_once()


@pytest.mark.asyncio
async def test_update_issue(mock_config, mock_jira_client):
    fetcher = JiraFetcher(mock_config)
    fetcher.client = mock_jira_client

    # Mock get_issue response
    mock_jira_client.issue.return_value = {
        "id": "10000",
        "key": "TEST-1",
        "fields": {"summary": "Test Issue", "description": "Original description"},
    }

    # Mock update_issue response
    mock_jira_client.update_issue.return_value = (
        None  # Jira returns None on successful update
    )

    result = await fetcher.update_issue(
        issue_key="TEST-1", fields={"summary": "Updated Test Issue"}
    )

    assert result is None  # Successful update
    mock_jira_client.update_issue.assert_called_once()


@pytest.mark.asyncio
async def test_get_issue_transitions(mock_config, mock_jira_client):
    fetcher = JiraFetcher(mock_config)
    fetcher.client = mock_jira_client

    mock_jira_client.get_issue_transitions.return_value = {
        "transitions": [
            {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
            {"id": "31", "name": "Done", "to": {"name": "Done"}},
        ]
    }

    transitions = await fetcher.get_issue_transitions("TEST-1")
    assert len(transitions["transitions"]) == 2
    assert transitions["transitions"][0]["name"] == "In Progress"
    mock_jira_client.get_issue_transitions.assert_called_once()


@pytest.mark.asyncio
async def test_attachment_handling(mock_config, mock_jira_client):
    fetcher = JiraFetcher(mock_config)
    fetcher.client = mock_jira_client

    # Mock attachment list response
    mock_jira_client.issue.return_value = {
        "fields": {
            "attachment": [
                {
                    "id": "10000",
                    "filename": "test.txt",
                    "mimeType": "text/plain",
                    "size": 2048,
                }
            ]
        }
    }

    attachments = await fetcher.get_attachments("TEST-1")
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "test.txt"
    mock_jira_client.issue.assert_called_once()


@pytest.mark.asyncio
async def test_search_issues(mock_config, mock_jira_client):
    fetcher = JiraFetcher(mock_config)
    fetcher.client = mock_jira_client

    mock_jira_client.search_issues.return_value = {
        "issues": [
            {
                "id": "10000",
                "key": "TEST-1",
                "fields": {"summary": "Test Issue", "description": "Test description"},
            }
        ],
        "total": 1,
    }

    results = await fetcher.search_issues("project = TEST")
    assert len(results["issues"]) == 1
    assert results["issues"][0]["key"] == "TEST-1"
    mock_jira_client.search_issues.assert_called_once()
