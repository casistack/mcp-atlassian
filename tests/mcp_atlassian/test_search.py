import pytest
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from mcp_atlassian.search import UnifiedSearch


@pytest.fixture
def mock_unified_search(mock_config, mock_confluence_client, mock_jira_client):
    search = UnifiedSearch(mock_config)
    search.confluence_client = mock_confluence_client
    search.jira_client = mock_jira_client
    return search


@pytest.mark.asyncio
async def test_unified_search_all_platforms(mock_unified_search):
    # Mock Confluence search results
    mock_unified_search.confluence_client.cql.return_value = {
        "results": [
            {
                "content": {
                    "id": "123456",
                    "type": "page",
                    "title": "Test Confluence Page",
                    "space": {"key": "TEST"},
                    "_links": {"webui": "/spaces/TEST/pages/123456"},
                    "lastModified": "2024-01-09T12:00:00Z",
                }
            }
        ]
    }

    # Mock Jira search results
    mock_unified_search.jira_client.search_issues.return_value = {
        "issues": [
            {
                "id": "10000",
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Jira Issue",
                    "description": "Test description",
                    "updated": "2024-01-09T13:00:00Z",
                },
            }
        ]
    }

    results = await mock_unified_search.search(
        query="test", platforms=["confluence", "jira"]
    )

    assert len(results) == 2
    assert any(r["platform"] == "confluence" for r in results)
    assert any(r["platform"] == "jira" for r in results)


@pytest.mark.asyncio
async def test_unified_search_confluence_only(mock_unified_search):
    mock_unified_search.confluence_client.cql.return_value = {
        "results": [
            {
                "content": {
                    "id": "123456",
                    "type": "page",
                    "title": "Test Confluence Page",
                    "space": {"key": "TEST"},
                    "_links": {"webui": "/spaces/TEST/pages/123456"},
                    "lastModified": "2024-01-09T12:00:00Z",
                }
            }
        ]
    }

    results = await mock_unified_search.search(query="test", platforms=["confluence"])

    assert len(results) == 1
    assert results[0]["platform"] == "confluence"
    assert results[0]["title"] == "Test Confluence Page"


@pytest.mark.asyncio
async def test_unified_search_jira_only(mock_unified_search):
    mock_unified_search.jira_client.search_issues.return_value = {
        "issues": [
            {
                "id": "10000",
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Jira Issue",
                    "description": "Test description",
                    "updated": "2024-01-09T13:00:00Z",
                },
            }
        ]
    }

    results = await mock_unified_search.search(query="test", platforms=["jira"])

    assert len(results) == 1
    assert results[0]["platform"] == "jira"
    assert results[0]["title"] == "Test Jira Issue"


@pytest.mark.asyncio
async def test_unified_search_sorting(mock_unified_search):
    # Mock results with different timestamps
    mock_unified_search.confluence_client.cql.return_value = {
        "results": [
            {
                "content": {
                    "id": "123456",
                    "type": "page",
                    "title": "Old Confluence Page",
                    "space": {"key": "TEST"},
                    "_links": {"webui": "/spaces/TEST/pages/123456"},
                    "lastModified": "2024-01-08T12:00:00Z",
                }
            }
        ]
    }

    mock_unified_search.jira_client.search_issues.return_value = {
        "issues": [
            {
                "id": "10000",
                "key": "TEST-1",
                "fields": {
                    "summary": "New Jira Issue",
                    "description": "Test description",
                    "updated": "2024-01-09T13:00:00Z",
                },
            }
        ]
    }

    results = await mock_unified_search.search(
        query="test", platforms=["confluence", "jira"]
    )

    assert len(results) == 2
    # First result should be the newer Jira issue
    assert results[0]["platform"] == "jira"
    assert results[0]["title"] == "New Jira Issue"
