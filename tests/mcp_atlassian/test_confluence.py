import pytest
from unittest.mock import MagicMock, patch
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.types import Document
from mcp_atlassian.attachments import AttachmentInfo
from pathlib import Path


@pytest.fixture
def mock_env_vars():
    with patch.dict(
        "os.environ",
        {
            "CONFLUENCE_URL": "https://example.atlassian.net",
            "CONFLUENCE_USERNAME": "test@example.com",
            "CONFLUENCE_API_TOKEN": "test-token",
        },
    ):
        yield


@pytest.fixture
def mock_confluence_client(mocker):
    mock = mocker.MagicMock()
    mock.update_page.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Updated content</p>"}},
        "version": {"number": 2},
        "space": {"key": "TEAM"},
    }
    return mock


@pytest.fixture
def mock_preprocessor(mocker):
    mock = mocker.MagicMock()
    mock.process_html_content.return_value = (
        "<p>Processed HTML</p>",
        "Processed Markdown",
    )
    return mock


@pytest.fixture
def confluence_fetcher(mock_env_vars, mock_confluence_client, mock_preprocessor):
    fetcher = ConfluenceFetcher()
    fetcher.confluence = mock_confluence_client
    fetcher.preprocessor = mock_preprocessor
    return fetcher


def test_init_with_missing_env_vars():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(
            ValueError, match="Missing required Confluence environment variables"
        ):
            ConfluenceFetcher()


def test_get_spaces(confluence_fetcher, mock_confluence_client):
    # Mock response
    mock_confluence_client.get_all_spaces.return_value = {
        "results": [
            {"key": "TEAM", "name": "Team Space", "type": "global"},
            {"key": "PROJ", "name": "Project Space", "type": "global"},
        ]
    }

    spaces = confluence_fetcher.get_spaces(start=0, limit=10)
    assert spaces["results"][0]["key"] == "TEAM"
    assert spaces["results"][1]["key"] == "PROJ"
    mock_confluence_client.get_all_spaces.assert_called_once_with(start=0, limit=10)


def test_get_page_content(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Test content</p>"}},
        "version": {
            "number": 1,
            "by": {"displayName": "Test User"},
            "when": "2024-01-09T12:00:00Z",
        },
        "space": {"key": "TEAM", "name": "Team Space"},
    }

    result = confluence_fetcher.get_page_content("12345")
    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["title"] == "Test Page"
    assert result.metadata["version"] == 1
    assert result.metadata["space_key"] == "TEAM"
    assert result.metadata["author_name"] == "Test User"
    mock_confluence_client.get_page_by_id.assert_called_once()
    mock_preprocessor.process_html_content.assert_called_once()


def test_get_page_by_title(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock response
    mock_confluence_client.get_page_by_title.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Test content</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.get_page_by_title("TEAM", "Test Page")
    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["title"] == "Test Page"
    mock_confluence_client.get_page_by_title.assert_called_once()
    mock_preprocessor.process_html_content.assert_called_once()

    # Test non-existent page
    mock_confluence_client.get_page_by_title.return_value = None
    result = confluence_fetcher.get_page_by_title("TEAM", "Non-existent Page")
    assert result is None


def test_get_space_pages(confluence_fetcher, mock_confluence_client, mock_preprocessor):
    # Mock response
    mock_confluence_client.get_all_pages_from_space.return_value = [
        {
            "id": "12345",
            "title": "Page 1",
            "body": {"storage": {"value": "<p>Content 1</p>"}},
            "version": {"number": 1},
            "space": {"key": "TEAM"},
        },
        {
            "id": "67890",
            "title": "Page 2",
            "body": {"storage": {"value": "<p>Content 2</p>"}},
            "version": {"number": 1},
            "space": {"key": "TEAM"},
        },
    ]

    results = confluence_fetcher.get_space_pages("TEAM", start=0, limit=10)
    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    assert results[0].metadata["page_id"] == "12345"
    assert results[1].metadata["page_id"] == "67890"
    mock_confluence_client.get_all_pages_from_space.assert_called_once()
    assert mock_preprocessor.process_html_content.call_count == 2


def test_create_page(confluence_fetcher, mock_confluence_client):
    # Mock create_page response
    mock_confluence_client.create_page.return_value = {
        "id": "12345",
        "title": "New Page",
        "space": {"key": "TEAM"},
    }

    # Mock get_page_by_id response for the created page
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "New Page",
        "body": {"storage": {"value": "<p>New content</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.create_page(
        space_key="TEAM", title="New Page", body="New content"
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["title"] == "New Page"
    mock_confluence_client.create_page.assert_called_once()

    # Test creation failure
    mock_confluence_client.create_page.return_value = None
    result = confluence_fetcher.create_page(
        space_key="TEAM", title="Failed Page", body="Content"
    )
    assert result is None


def test_update_page(confluence_fetcher, mock_confluence_client):
    # Mock update response
    mock_confluence_client.update_page.return_value = {
        "id": "12345",
        "title": "Updated Page",
        "space": {"key": "TEAM"},
    }

    # Mock get_page_by_id response for the updated page
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Updated Page",
        "body": {"storage": {"value": "<p>Updated content</p>"}},
        "version": {"number": 2},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.update_page(
        page_id="12345", title="Updated Page", body="Updated content"
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["title"] == "Updated Page"
    assert result.metadata["version"] == 2
    mock_confluence_client.update_page.assert_called_once()

    # Test update failure
    mock_confluence_client.update_page.side_effect = Exception("Update failed")
    result = confluence_fetcher.update_page(
        page_id="12345", title="Failed Update", body="Content"
    )
    assert result is None


def test_get_page_comments(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "space": {"key": "TEAM", "name": "Team Space"}
    }

    # Mock get_page_comments response
    mock_confluence_client.get_page_comments.return_value = {
        "results": [
            {
                "id": "comment1",
                "body": {"view": {"value": "<p>Test comment</p>"}},
                "version": {
                    "by": {"displayName": "Test User"},
                    "when": "2024-01-09T12:00:00Z",
                },
            }
        ]
    }

    results = confluence_fetcher.get_page_comments("12345")
    assert len(results) == 1
    assert isinstance(results[0], Document)
    assert results[0].metadata["comment_id"] == "comment1"
    assert results[0].metadata["author_name"] == "Test User"
    assert results[0].metadata["type"] == "comment"
    mock_confluence_client.get_page_comments.assert_called_once()
    mock_preprocessor.process_html_content.assert_called_once()


def test_search(confluence_fetcher, mock_confluence_client, mock_preprocessor):
    # Mock CQL search response
    mock_confluence_client.cql.return_value = {
        "results": [
            {
                "content": {
                    "id": "12345",
                    "type": "page",
                    "title": "Test Page",
                    "space": {"key": "TEAM"},
                }
            }
        ]
    }

    # Mock get_page_by_id response for the found page
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Test content</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    results = confluence_fetcher.search("text ~ 'test'", limit=10)
    assert len(results) == 1
    assert isinstance(results[0], Document)
    assert results[0].metadata["page_id"] == "12345"
    assert results[0].metadata["title"] == "Test Page"
    mock_confluence_client.cql.assert_called_once()

    # Test search error
    mock_confluence_client.cql.side_effect = Exception("Search failed")
    results = confluence_fetcher.search("invalid query")
    assert results == []


def test_attachment_handling(confluence_fetcher, mock_confluence_client):
    # Mock get_attachments response
    mock_confluence_client.get_attachments_from_content.return_value = {
        "results": [
            {
                "id": "att123",
                "title": "test.txt",
                "metadata": {"mediaType": "text/plain"},
                "size": 1024,
                "container": {"key": "TEAM"},
            }
        ]
    }

    # Test get_attachments
    attachments = confluence_fetcher.get_attachments("12345")
    assert len(attachments) == 1
    assert isinstance(attachments[0], AttachmentInfo)
    assert attachments[0].id == "att123"
    assert attachments[0].filename == "test.txt"

    # Test get_attachment_content
    mock_confluence_client.get_attachment_content.return_value = b"test content"
    content = confluence_fetcher.get_attachment_content("att123")
    assert content == b"test content"
    mock_confluence_client.get_attachment_content.assert_called_once()

    # Mock get_page_by_id response for add_attachment
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "space": {"key": "TEAM"},
    }

    # Test add_attachment
    mock_confluence_client.attach_file.return_value = {
        "id": "att456",
        "title": "new.txt",
        "metadata": {"mediaType": "text/plain"},
        "size": 512,
        "container": {"key": "TEAM"},
        "_links": {"download": "/download/attachments/att456/new.txt"},
        "created": "2023-01-01T00:00:00.000Z",
    }

    # Create a temporary test file
    test_file = Path("test.txt")
    test_file.write_text("test content")

    result = confluence_fetcher.add_attachment("12345", test_file)
    assert isinstance(result, AttachmentInfo)
    assert result.id == "att456"
    assert result.filename == "new.txt"
    assert result.container["key"] == "TEAM"
    mock_confluence_client.attach_file.assert_called_once()

    # Clean up
    test_file.unlink()

    # Test delete_attachment
    mock_confluence_client.delete_attachment.return_value = True
    assert confluence_fetcher.delete_attachment("att123") is True
    mock_confluence_client.delete_attachment.assert_called_once()


def test_update_page_section(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<h1>Test Section</h1><p>Old content</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.update_page_section(
        page_id="12345",
        heading="Test Section",
        new_content="Updated content",
        minor_edit=True,
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["version"] == 2
    mock_confluence_client.update_page.assert_called_once()


def test_insert_after_section(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "<h1>Test Section</h1><p>Existing content</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.insert_after_section(
        page_id="12345",
        heading="Test Section",
        new_content="New content",
        minor_edit=True,
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["version"] == 2
    mock_confluence_client.update_page.assert_called_once()


def test_append_to_list_in_section(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {"storage": {"value": "h1. Test Section\n* Item 1\n* Item 2"}},
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    # Mock update response
    mock_confluence_client.update_page.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {
            "storage": {"value": "h1. Test Section\n* Item 1\n* Item 2\n* Item 3"}
        },
        "version": {"number": 2},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.append_to_list_in_section(
        page_id="12345",
        heading="Test Section",
        list_marker="*",
        new_item="Item 3",
        minor_edit=True,
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["version"] == 2
    mock_confluence_client.update_page.assert_called_once()


def test_update_table_in_section(
    confluence_fetcher, mock_confluence_client, mock_preprocessor
):
    # Mock get_page_by_id response
    mock_confluence_client.get_page_by_id.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {
            "storage": {
                "value": "h1. Test Section\n||Header 1||Header 2||\n|Value 1|Value 2|\n|Old 1|Old 2|"
            }
        },
        "version": {"number": 1},
        "space": {"key": "TEAM"},
    }

    # Mock update response
    mock_confluence_client.update_page.return_value = {
        "id": "12345",
        "title": "Test Page",
        "body": {
            "storage": {
                "value": "h1. Test Section\n||Header 1||Header 2||\n|Value 1|Value 2|\n|New 1|New 2|"
            }
        },
        "version": {"number": 2},
        "space": {"key": "TEAM"},
    }

    result = confluence_fetcher.update_table_in_section(
        page_id="12345",
        heading="Test Section",
        table_start="||Header 1||Header 2||",
        row_identifier="Old 1",
        new_values=["New 1", "New 2"],
        minor_edit=True,
    )

    assert isinstance(result, Document)
    assert result.metadata["page_id"] == "12345"
    assert result.metadata["version"] == 2
    mock_confluence_client.update_page.assert_called_once()
