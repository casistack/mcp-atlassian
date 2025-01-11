# MCP Atlassian

Model Context Protocol (MCP) server for Atlassian Cloud products (Confluence and Jira). This integration is designed specifically for Atlassian Cloud instances and does not support Atlassian Server or Data Center deployments.

<a href="https://glama.ai/mcp/servers/kc33m1kh5m"><img width="380" height="200" src="https://glama.ai/mcp/servers/kc33m1kh5m/badge" alt="Atlassian MCP server" /></a>

## Feature Demo
![Demo](https://github.com/user-attachments/assets/995d96a8-4cf3-4a03-abe1-a9f6aea27ac0)

## Features

### Core Features
- Search and read Confluence spaces/pages
- Create and update Confluence pages with rich formatting
- Manage Confluence page comments and attachments
- Search and read Jira issues
- Create and update Jira issues
- Get project issues and metadata
- Unified search across Confluence and Jira
- Template-based content creation
- Advanced content formatting and section management

### Advanced Capabilities
- **Unified Search**
  - Cross-platform search (Confluence and Jira)
  - Content excerpts and smart truncation
  - Results sorted by last modified date

- **Content Management**
  - Section-based updates
  - Rich content formatting
  - Template management
  - Attachment handling
  - Comment management

- **Advanced Formatting**
  - Headings (h1-h6)
  - Nested lists
  - Code blocks with language support
  - Tables with rich formatting
  - Information panels and callouts
  - Status indicators
  - Expandable sections
  - Multi-column layouts

## API

### Resources

- `confluence://{space_key}`: Access Confluence spaces and pages
- `confluence://{space_key}/pages/{title}`: Access specific Confluence pages
- `jira://{project_key}`: Access Jira project and its issues
- `jira://{project_key}/issues/{issue_key}`: Access specific Jira issues

### Tools

#### Confluence Tools

- **confluence_search**
  - Search Confluence content using CQL
  - Inputs:
    - `query` (string): CQL query string
    - `limit` (number, optional): Results limit (1-50, default: 10)
  - Returns:
    - Array of search results with page_id, title, space, url, last_modified, type, and excerpt

- **confluence_get_page**
  - Get content of a specific Confluence page
  - Inputs:
    - `page_id` (string): Confluence page ID
    - `include_metadata` (boolean, optional): Include page metadata (default: true)

- **confluence_get_comments**
  - Get comments for a specific Confluence page
  - Input: `page_id` (string)

- **confluence_create_page**
  - Create a new Confluence page
  - Inputs:
    - `space_key` (string): Space key
    - `title` (string): Page title
    - `content` (string): Page content
    - `parent_id` (string, optional): Parent page ID

- **confluence_update_page**
  - Update existing Confluence page
  - Inputs:
    - `page_id` (string): Page ID
    - `content` (string): Updated content
    - `title` (string, optional): New title

#### Jira Tools

- **jira_get_issue**
  - Get details of a specific Jira issue
  - Inputs:
    - `issue_key` (string): Jira issue key (e.g., 'PROJ-123')
    - `expand` (string, optional): Fields to expand

- **jira_search**
  - Search Jira issues using JQL
  - Inputs:
    - `jql` (string): JQL query string
    - `fields` (string, optional): Comma-separated fields (default: "*all")
    - `limit` (number, optional): Results limit (1-50, default: 10)

- **jira_get_project_issues**
  - Get all issues for a specific Jira project
  - Inputs:
    - `project_key` (string): Project key
    - `limit` (number, optional): Results limit (1-50, default: 10)

- **jira_create_issue**
  - Create a new Jira issue
  - Inputs:
    - `project_key` (string): Project key
    - `summary` (string): Issue summary
    - `description` (string): Issue description
    - `issue_type` (string): Issue type (e.g., 'Task', 'Bug')

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
