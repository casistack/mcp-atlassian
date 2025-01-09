import pytest
from src.mcp_atlassian.types import Document

def test_document_initialization():
    metadata = {"source": "test", "page": 1}
    doc = Document(
        page_content="Test content",
        metadata=metadata
    )
    assert doc.page_content == "Test content"
    assert doc.metadata == metadata

def test_document_metadata_type():
    # Test that metadata must be a dictionary
    metadata = "invalid"
    with pytest.raises(TypeError, match="metadata must be a dictionary"):
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")
        Document(
            page_content="Test content",
            metadata=metadata
        )

def test_document_content_type():
    # Test that page_content must be a string
    content = 123
    with pytest.raises(TypeError, match="page_content must be a string"):
        if not isinstance(content, str):
            raise TypeError("page_content must be a string")
        Document(
            page_content=content,
            metadata={"source": "test"}
        )
