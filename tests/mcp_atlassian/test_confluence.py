import pytest
from unittest.mock import MagicMock, patch
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.config import ConfluenceConfig
from mcp_atlassian.types import Document


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("CONFLUENCE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("CONFLUENCE_USERNAME", "test@example.com")
    monkeypatch.setenv("CONFLUENCE_API_TOKEN", "test-token")


@pytest.fixture
def mock_confluence():
    """Create a mock Confluence client."""
    return MagicMock()


@pytest.fixture
def mock_preprocessor():
    """Create a mock TextPreprocessor."""
    return MagicMock()


class TestConfluenceFetcher:
    def test_initialization_success(self, mock_env_vars):
        """Test successful initialization with valid environment variables."""
        fetcher = ConfluenceFetcher()
        assert isinstance(fetcher.config, ConfluenceConfig)
        assert fetcher.config.url == "https://test.atlassian.net"
        assert fetcher.config.username == "test@example.com"
        assert fetcher.config.api_token == "test-token"

    def test_initialization_missing_env_vars(self, monkeypatch):
        """Test initialization fails with missing environment variables."""
        # Clear environment variables
        monkeypatch.delenv("CONFLUENCE_URL", raising=False)
        monkeypatch.delenv("CONFLUENCE_USERNAME", raising=False)
        monkeypatch.delenv("CONFLUENCE_API_TOKEN", raising=False)

        with pytest.raises(
            ValueError, match="Missing required Confluence environment variables"
        ):
            ConfluenceFetcher()

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_get_spaces(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test getting Confluence spaces."""
        # Setup mock response
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.get_all_spaces.return_value = {
            "results": [
                {"id": "1", "key": "SPACE1", "name": "Space 1"},
                {"id": "2", "key": "SPACE2", "name": "Space 2"},
            ]
        }

        fetcher = ConfluenceFetcher()
        spaces = fetcher.get_spaces(start=0, limit=10)

        # Verify the response
        assert spaces["results"][0]["key"] == "SPACE1"
        assert spaces["results"][1]["key"] == "SPACE2"

        # Verify the API call
        mock_confluence.get_all_spaces.assert_called_once_with(start=0, limit=10)

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_get_page_content(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test getting page content."""
        # Setup mock response
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.get_page_by_id.return_value = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "SPACE1", "name": "Test Space"},
            "body": {
                "storage": {"value": "<p>test content</p>", "representation": "storage"}
            },
            "version": {
                "number": 1,
                "by": {"displayName": "Test User"},
                "when": "2024-01-09T12:00:00Z",
            },
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "processed text",
            "processed html",
        )

        fetcher = ConfluenceFetcher()
        doc = fetcher.get_page_content("123")

        assert isinstance(doc, Document)
        assert doc.page_content == "processed text"  # clean_html=True by default
        assert doc.metadata["page_id"] == "123"
        assert doc.metadata["title"] == "Test Page"
        assert doc.metadata["version"] == 1
        assert doc.metadata["space_key"] == "SPACE1"
        assert doc.metadata["author_name"] == "Test User"

        # Test with clean_html=False
        doc = fetcher.get_page_content("123", clean_html=False)
        assert doc.page_content == "processed html"

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_get_page_by_title(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test getting page by title."""
        # Setup mock response
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.get_page_by_title.return_value = {
            "id": "123",
            "title": "Test Page",
            "body": {
                "storage": {"value": "<p>test content</p>", "representation": "storage"}
            },
            "version": {"number": 1},
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor._clean_html_content.return_value = "cleaned content"

        fetcher = ConfluenceFetcher()
        doc = fetcher.get_page_by_title("SPACE1", "Test Page")

        assert isinstance(doc, Document)
        assert doc.page_content == "cleaned content"  # clean_html=True by default
        assert doc.metadata["page_id"] == "123"
        assert doc.metadata["title"] == "Test Page"
        assert doc.metadata["version"] == 1
        assert doc.metadata["space_key"] == "SPACE1"

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_create_page(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test creating a new page."""
        # Setup mock responses
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.create_page.return_value = {
            "id": "123",
            "title": "New Page",
            "space": {"key": "SPACE1"},
            "version": {"number": 1},
        }

        # Mock get_page_content response for the created page
        mock_confluence.get_page_by_id.return_value = {
            "id": "123",
            "title": "New Page",
            "space": {"key": "SPACE1"},
            "body": {"storage": {"value": "<p>new content</p>"}},
            "version": {"number": 1},
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "processed text",
            "processed html",
        )

        fetcher = ConfluenceFetcher()
        doc = fetcher.create_page(
            space_key="SPACE1",
            title="New Page",
            body="<p>new content</p>",
            parent_id="456",
        )

        assert isinstance(doc, Document)
        assert doc.metadata["page_id"] == "123"
        assert doc.metadata["title"] == "New Page"
        mock_confluence.create_page.assert_called_once_with(
            space="SPACE1",
            title="New Page",
            body="<p>new content</p>",
            parent_id="456",
            representation="storage",
        )

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_update_page(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test updating an existing page."""
        # Setup mock responses
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.update_page.return_value = {
            "id": "123",
            "title": "Updated Page",
            "space": {"key": "SPACE1"},
            "version": {"number": 2},
        }

        # Mock get_page_content response for the updated page
        mock_confluence.get_page_by_id.return_value = {
            "id": "123",
            "title": "Updated Page",
            "space": {"key": "SPACE1"},
            "body": {"storage": {"value": "<p>updated content</p>"}},
            "version": {"number": 2},
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "processed text",
            "processed html",
        )

        fetcher = ConfluenceFetcher()
        doc = fetcher.update_page(
            page_id="123",
            title="Updated Page",
            body="<p>updated content</p>",
            minor_edit=True,
        )

        assert isinstance(doc, Document)
        assert doc.metadata["page_id"] == "123"
        assert doc.metadata["title"] == "Updated Page"
        assert doc.metadata["version"] == 2

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_search(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test searching content."""
        # Setup mock responses
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.cql.return_value = {
            "results": [
                {
                    "content": {
                        "id": "123",
                        "type": "page",
                        "title": "Test Page",
                        "space": {"key": "SPACE1"},
                    }
                }
            ]
        }

        # Mock get_page_content response for the found page
        mock_confluence.get_page_by_id.return_value = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "SPACE1"},
            "body": {"storage": {"value": "<p>test content</p>"}},
            "version": {"number": 1},
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "processed text",
            "processed html",
        )

        fetcher = ConfluenceFetcher()
        docs = fetcher.search("text ~ 'test'", limit=10)

        assert len(docs) == 1
        assert isinstance(docs[0], Document)
        assert docs[0].metadata["page_id"] == "123"
        assert docs[0].metadata["title"] == "Test Page"
        mock_confluence.cql.assert_called_once_with("text ~ 'test'", limit=10)

    @patch("mcp_atlassian.confluence.Confluence")
    @patch("mcp_atlassian.confluence.TextPreprocessor")
    def test_get_page_comments(
        self, mock_preprocessor_class, mock_confluence_class, mock_env_vars
    ):
        """Test getting page comments."""
        # Setup mock responses
        mock_confluence = mock_confluence_class.return_value
        mock_confluence.get_page_by_id.return_value = {
            "space": {"key": "SPACE1", "name": "Test Space"}
        }
        mock_confluence.get_page_comments.return_value = {
            "results": [
                {
                    "id": "comment1",
                    "body": {"view": {"value": "<p>test comment</p>"}},
                    "version": {
                        "by": {"displayName": "Test User"},
                        "when": "2024-01-09T12:00:00Z",
                    },
                }
            ]
        }

        # Setup mock preprocessor
        mock_preprocessor = mock_preprocessor_class.return_value
        mock_preprocessor.process_html_content.return_value = (
            "processed text",
            "processed html",
        )

        fetcher = ConfluenceFetcher()
        comments = fetcher.get_page_comments("123")

        assert len(comments) == 1
        assert isinstance(comments[0], Document)
        assert (
            comments[0].page_content == "processed text"
        )  # clean_html=True by default
        assert comments[0].metadata["comment_id"] == "comment1"
        assert comments[0].metadata["author_name"] == "Test User"
        assert comments[0].metadata["type"] == "comment"
