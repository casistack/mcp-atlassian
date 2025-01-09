import pytest
from unittest.mock import MagicMock, patch
from mcp_atlassian.confluence import ConfluenceFetcher


@pytest.mark.asyncio
async def test_create_page(mock_config, mock_confluence_client):
    fetcher = ConfluenceFetcher(mock_config)
    fetcher.client = mock_confluence_client

    # Mock response for successful page creation
    mock_confluence_client.create_page.return_value = {
        "id": "123456",
        "title": "Test Page",
        "space": {"key": "TEST"},
        "_links": {"webui": "/spaces/TEST/pages/123456"},
    }

    result = await fetcher.create_page(
        space_key="TEST", title="Test Page", body="Test content", parent_id=None
    )

    assert result["id"] == "123456"
    assert result["title"] == "Test Page"
    mock_confluence_client.create_page.assert_called_once()


@pytest.mark.asyncio
async def test_update_page(mock_config, mock_confluence_client):
    fetcher = ConfluenceFetcher(mock_config)
    fetcher.client = mock_confluence_client

    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "123456",
        "version": {"number": 1},
        "title": "Test Page",
        "space": {"key": "TEST"},
    }

    # Mock update_page response
    mock_confluence_client.update_page.return_value = {
        "id": "123456",
        "version": {"number": 2},
        "title": "Updated Test Page",
    }

    result = await fetcher.update_page(
        page_id="123456", title="Updated Test Page", body="Updated content"
    )

    assert result["id"] == "123456"
    assert result["version"]["number"] == 2
    mock_confluence_client.update_page.assert_called_once()


@pytest.mark.asyncio
async def test_get_page_content(mock_config, mock_confluence_client):
    fetcher = ConfluenceFetcher(mock_config)
    fetcher.client = mock_confluence_client

    mock_confluence_client.get_page_by_id.return_value = {
        "id": "123456",
        "body": {"storage": {"value": "Test content"}},
        "title": "Test Page",
        "space": {"key": "TEST"},
    }

    content = await fetcher.get_page_content("123456")
    assert "Test content" in content
    mock_confluence_client.get_page_by_id.assert_called_once_with("123456")


@pytest.mark.asyncio
async def test_attachment_handling(mock_config, mock_confluence_client):
    fetcher = ConfluenceFetcher(mock_config)
    fetcher.client = mock_confluence_client

    # Mock attachment list response
    mock_confluence_client.get_attachments_from_content.return_value = {
        "results": [
            {
                "id": "att123",
                "title": "test.txt",
                "metadata": {"mediaType": "text/plain"},
            }
        ]
    }

    attachments = await fetcher.get_attachments("123456")
    assert len(attachments["results"]) == 1
    assert attachments["results"][0]["id"] == "att123"
    mock_confluence_client.get_attachments_from_content.assert_called_once()
