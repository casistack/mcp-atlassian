import pytest
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
from mcp_atlassian.search import UnifiedSearch
from mcp_atlassian.types import Document


@pytest.fixture
def mock_unified_search(mock_config, mock_confluence_client, mock_jira_client):
    # Create mock fetchers
    mock_confluence_fetcher = MagicMock()
    mock_confluence_fetcher.search.return_value = [
        Document(
            page_content="Test Confluence content",
            metadata={
                "page_id": "123456",
                "title": "Test Confluence Page",
                "url": "/spaces/TEST/pages/123456",
                "space_key": "TEST",
                "last_modified": "2024-01-09T12:00:00Z",
                "author_name": "Test User",
            },
        )
    ]

    mock_jira_fetcher = MagicMock()
    mock_jira_fetcher.search_issues.return_value = [
        Document(
            page_content="Test Jira content",
            metadata={
                "key": "TEST-1",
                "title": "Test Jira Issue",
                "link": "/browse/TEST-1",
                "created_date": "2024-01-09T13:00:00Z",
                "type": "Task",
            },
        )
    ]

    # Initialize UnifiedSearch with both fetchers
    search = UnifiedSearch(mock_confluence_fetcher, mock_jira_fetcher)
    return search


def test_unified_search_all_platforms(mock_unified_search):
    results = mock_unified_search.search(query="test", platforms=["confluence", "jira"])

    assert len(results) == 2
    assert any(r.platform == "confluence" for r in results)
    assert any(r.platform == "jira" for r in results)


def test_unified_search_confluence_only(mock_unified_search):
    results = mock_unified_search.search(query="test", platforms=["confluence"])

    assert len(results) == 1
    assert results[0].platform == "confluence"
    assert results[0].title == "Test Confluence Page"


def test_unified_search_jira_only(mock_unified_search):
    results = mock_unified_search.search(query="test", platforms=["jira"])

    assert len(results) == 1
    assert results[0].platform == "jira"
    assert results[0].title == "Test Jira Issue"


def test_unified_search_sorting(mock_unified_search):
    # Mock results with different timestamps
    mock_unified_search.confluence.search.return_value = [
        Document(
            page_content="Old Confluence content",
            metadata={
                "page_id": "123456",
                "title": "Old Confluence Page",
                "url": "/spaces/TEST/pages/123456",
                "space_key": "TEST",
                "last_modified": "2024-01-08T12:00:00Z",
                "author_name": "Test User",
            },
        )
    ]

    mock_unified_search.jira.search_issues.return_value = [
        Document(
            page_content="New Jira content",
            metadata={
                "key": "TEST-1",
                "title": "New Jira Issue",
                "link": "/browse/TEST-1",
                "created_date": "2024-01-09T13:00:00Z",
                "type": "Task",
            },
        )
    ]

    results = mock_unified_search.search(query="test", platforms=["confluence", "jira"])

    assert len(results) == 2
    # First result should be the newer Jira issue
    assert results[0].platform == "jira"
    assert results[0].title == "New Jira Issue"
