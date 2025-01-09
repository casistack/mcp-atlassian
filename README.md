# MCP Atlassian Integration

A powerful integration between MCP (Master Control Program) and Atlassian products (Confluence and Jira), providing advanced content management, search, and automation capabilities.

## Features

### Cross-Platform Integration
- **Unified Search**
  - Search across both Confluence and Jira simultaneously
  - Configurable platform selection
  - Concurrent search execution
  - Unified result format with rich metadata
  - Content excerpts and smart truncation
  - Results sorted by last modified date

### Confluence Integration
- **Content Management**
  - Create and update pages
  - Section-based updates
  - Rich content formatting
  - Template management
  - Attachment handling
  - Comment management

- **Advanced Formatting**
  - Headings and subheadings (h1-h6)
  - Bullet and numbered lists with nesting
  - Code blocks with language support
  - Tables with headers and row management
  - Quotes and blockquotes
  - Links and cross-references
  - Text styling (bold, italic)
  - Information panels and callouts
  - Status indicators with color support
  - Expandable sections
  - Table of contents generation
  - Multi-column layouts
  - Task lists with checkboxes
  - Text highlighting
  - Dividers

### Jira Integration
- **Issue Management**
  - Create and update issues
  - Status transitions
  - Template-based creation
  - Rich description formatting
  - Attachment handling
  - Comment management

- **Project Features**
  - Project listing
  - Issue tracking
  - Template management
  - Custom field support
  - JQL search capabilities

### Template System
- **Template Management**
  - Discover available templates
  - Blueprint template support
  - Custom template support
  - Template variable extraction
  - Parameter validation
  - Dynamic content generation

- **Template Types**
  - Confluence page templates
  - Jira issue templates
  - Project templates
  - Custom templates

### Attachment Handling
- **File Management**
  - Upload attachments
  - Download attachment content
  - Update existing attachments
  - Delete attachments
  - Content type detection
  - Size limit enforcement

## Installation

1. Install the package:
   ```bash
   pip install mcp-atlassian
   ```

2. Set up environment variables:
   ```bash
   # Confluence settings
   CONFLUENCE_URL=https://your-instance.atlassian.net/wiki
   CONFLUENCE_USERNAME=your-email@domain.com
   CONFLUENCE_API_TOKEN=your-api-token

   # Jira settings
   JIRA_URL=https://your-instance.atlassian.net
   JIRA_USERNAME=your-email@domain.com
   JIRA_API_TOKEN=your-api-token
   ```

## Usage Examples

### Unified Search
```python
# Search across both platforms
results = unified_search.search("your query")

# Search specific platform
results = unified_search.search("your query", platforms=["confluence"])
```

### Content Creation with Templates
```python
# Create from Confluence template
page = create_from_confluence_template(
    template_id="template-123",
    space_key="DOCS",
    title="New Documentation",
    template_parameters={
        "author": "AI Assistant",
        "version": "1.0"
    }
)

# Create from Jira template
issue = create_from_jira_template(
    template_id="template-456",
    project_key="PROJ",
    summary="New Feature Request",
    template_parameters={
        "priority": "High",
        "components": ["Backend"]
    }
)
```

### Rich Content Formatting
```python
content = (
    MarkupFormatter.heading("Project Documentation", level=1) +
    MarkupFormatter.status("In Progress", color="blue") +
    MarkupFormatter.panel(
        "This is a beta release",
        title="Notice",
        panel_type="warning"
    ) +
    MarkupFormatter.table_of_contents()
)
```

### Section Management
```python
# Update specific section
update_confluence_section(
    page_id="123",
    heading="Implementation",
    content="Updated content..."
)

# Insert after section
insert_after_confluence_section(
    page_id="123",
    heading="Overview",
    content="New section content..."
)
```

### Attachment Handling
```python
# Add attachment
add_confluence_attachment(
    page_id="123",
    file_path="document.pdf"
)

# Get attachments
attachments = get_confluence_attachments(page_id="123")
```

## Dependencies
- atlassian-python-api (≥3.41.16)
- beautifulsoup4 (≥4.12.3)
- httpx (≥0.28.0)
- mcp[cli] (≥1.0.0)
- python-dotenv (≥1.0.1)
- markdownify (≥0.11.6)

## Contributing
Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security
For security concerns, please see our [Security Policy](SECURITY.md).
