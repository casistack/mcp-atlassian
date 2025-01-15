# MCP Atlassian

Model Context Protocol (MCP) server for Atlassian Cloud products (Confluence and Jira). This integration is designed specifically for Atlassian Cloud instances and does not support Atlassian Server or Data Center deployments.

<a href="https://glama.ai/mcp/servers/kc33m1kh5m"><img width="380" height="200" src="https://glama.ai/mcp/servers/kc33m1kh5m/badge" alt="Atlassian MCP server" /></a>

## Feature Demo
![Demo](https://github.com/user-attachments/assets/995d96a8-4cf3-4a03-abe1-a9f6aea27ac0)

## Features

### Core Features
- Search and read Confluence spaces/pages with advanced CQL support
- Create and update Confluence pages with professional rich formatting
- Manage Confluence page comments, sections, and attachments
- Search and read Jira issues with JQL support
- Create and update Jira issues with custom fields
- Get project issues and metadata with expanded fields
- Unified search across Confluence and Jira
- Template-based content creation with variable substitution
- Advanced content formatting and section management

### Advanced Capabilities
- **Unified Search**
  - Cross-platform search (Confluence and Jira)
  - Content excerpts and smart truncation
  - Results sorted by last modified date
  - Advanced filtering with CQL/JQL support

- **Content Management**
  - Section-based updates with intelligent merging
  - Rich content formatting with professional layouts
  - Template management with variable substitution
  - Attachment handling with metadata support
  - Comment management with formatting options
  - Batch content operations
  - Content validation and error handling

- **Advanced Formatting**
  - Headings (h1-h6) with proper hierarchy
  - Nested lists (bullet and numbered)
  - Code blocks with language support and line numbers
  - Tables with rich formatting and sorting
  - Information panels and callouts with titles
  - Status indicators with color support
  - Expandable sections with custom titles
  - Multi-column layouts
  - Interactive elements (tabs, expanders)
  - Warning and notification panels
  - Table of contents with customizable levels

## API

### Resources

- `confluence://{space_key}`: Access Confluence spaces and pages
- `confluence://{space_key}/pages/{title}`: Access specific Confluence pages
- `jira://{project_key}`: Access Jira project and its issues
- `jira://{project_key}/issues/{issue_key}`: Access specific Jira issues

### Tools

#### Confluence Tools

- **confluence_search**
  - Search Confluence content using CQL (Confluence Query Language)
  - Inputs:
    - `query` (string): CQL query string (e.g. 'type=page AND space=DEV')
    - `limit` (number, optional): Results limit (1-50, default: 10)
  - Returns:
    - Array of search results with page_id, title, space, url, last_modified, type, excerpt, and author

- **confluence_get_page**
  - Retrieve content and metadata of a specific Confluence page
  - Inputs:
    - `page_id` (string): Confluence page ID
    - `include_metadata` (boolean, optional): Include page metadata (default: true)

- **confluence_get_comments**
  - Retrieve all comments for a specific Confluence page
  - Input: `page_id` (string)
  - Returns: Array of comments with author info and timestamps

- **confluence_create_page**
  - Create new Confluence page with professional formatting
  - Inputs:
    - `space_key` (string): Space key
    - `title` (string): Page title
    - `content` (array): Content blocks in rich text format
      - Supported blocks: heading, text, list, table, panel, status, code, toc
      - Each block type has specific properties (e.g., level for headings)

- **confluence_update_page**
  - Update existing Confluence page with rich formatting
  - Inputs:
    - `page_id` (string): Page ID
    - `title` (string, optional): New title
    - `content` (array): Content blocks (same format as create_page)
    - `minor_edit` (boolean, optional): Mark as minor edit

#### Jira Tools

- **jira_get_issue**
  - Retrieve detailed information about a Jira issue
  - Inputs:
    - `issue_key` (string): Jira issue key (e.g., 'PROJ-123')
    - `expand` (string, optional): Fields to expand

- **jira_search**
  - Search Jira issues using JQL (Jira Query Language)
  - Inputs:
    - `jql` (string): JQL query string
    - `fields` (string, optional): Comma-separated fields (default: "*all")
    - `limit` (number, optional): Results limit (1-50, default: 10)

- **jira_create_issue**
  - Create a new Jira issue with custom fields
  - Inputs:
    - `project_key` (string): Project key
    - `summary` (string): Issue summary
    - `description` (string): Issue description
    - `issue_type` (string, optional): Issue type (default: 'Task')
    - `priority` (string, optional): Priority level
    - `assignee` (string, optional): Username to assign
    - `labels` (array, optional): Labels to add
    - `custom_fields` (object, optional): Custom field values

- **jira_update_issue**
  - Update existing Jira issue
  - Inputs:
    - `issue_key` (string): Issue key to update
    - `summary` (string, optional): New summary
    - `description` (string, optional): New description
    - `status` (string, optional): New status
    - `priority` (string, optional): New priority
    - `assignee` (string, optional): New assignee
    - `labels` (array, optional): New labels
    - `custom_fields` (object, optional): New custom field values

#### Template Tools

- **create_from_confluence_template**
  - Create Confluence page using predefined template
  - Inputs:
    - `template_id` (string): Template ID
    - `space_key` (string): Target space key
    - `title` (string): Page title
    - `template_parameters` (object, optional): Variable substitutions

- **create_from_jira_template**
  - Create Jira issue using predefined template
  - Inputs:
    - `template_id` (string): Template ID
    - `project_key` (string): Target project key
    - `summary` (string): Issue summary
    - `template_parameters` (object, optional): Variable substitutions

## Usage with Claude Desktop

1. Get API tokens from: https://id.atlassian.com/manage-profile/security/api-tokens

2. Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@domain.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your.email@domain.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

<details>
<summary>Alternative configuration using <code>uv</code></summary>

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-atlassian",
        "run",
        "mcp-atlassian"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@domain.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your.email@domain.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```
Replace `/path/to/mcp-atlassian` with the actual path where you've cloned the repository.
</details>

## Dependencies
- atlassian-python-api (≥3.41.16)
- beautifulsoup4 (≥4.12.3)
- httpx (≥0.28.0)
- mcp[cli] (≥1.0.0)
- python-dotenv (≥1.0.1)
- markdownify (≥0.11.6)

## Security

- Never share API tokens
- Keep .env files secure and private
- See [SECURITY.md](SECURITY.md) for best practices

## License

Licensed under MIT - see [LICENSE](LICENSE) file. This is not an official Atlassian product.
