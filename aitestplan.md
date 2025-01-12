# MCP Atlassian AI Tools Test Plan

## Testing Guidelines

### Test File: test_mcp.py
This file serves as our primary testing tool, simulating exactly how the AI would interact with our MCP tools.

### Testing Approach
1. Each test directly calls the actual functions from our codebase
2. Tests simulate AI's tool usage pattern:
   - Tool validation
   - Parameter handling
   - Response processing
   - Error handling
3. Results must be in the exact format the AI expects
4. All edge cases must be tested
5. Real data from Confluence/Jira is used for testing
6. Make sure you are using the actual method in our code base this way we will know if theres an issue. 

### Success Criteria
- Tool functions exactly as documented
- Returns properly formatted data
- Handles errors gracefully
- Works with real Atlassian data
- Matches AI's expected interaction pattern

## Tool Categories
1. Search Tools
2. Confluence Tools
3. Jira Tools
4. Template Tools

## Tools and Test Scenarios

### 1. Search Tools

#### 1.1 unified_search ✅
- **Description**: Cross-platform search across Confluence and Jira
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Basic search works with proper JSON response
  - ✅ Platform filtering works (Confluence/Jira)
  - ✅ Custom limit respected
  - ✅ Special characters handled correctly
  - ✅ Empty query handled properly
  - ✅ Response format matches AI requirements

#### 1.2 confluence_search ✅
- **Description**: Search Confluence content using CQL
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Title search works (found "Project Best Practices")
  - ✅ CQL query works (space + text search)
  - ✅ Limit works (tested with limit=2)
  - ✅ Space-specific search works (IS space)
  - ✅ Invalid query handled gracefully
  - ✅ Metadata correctly returned:
    - Title
    - Space info
    - URL
    - Last Modified
    - Author
    - Content preview
  - ✅ Direct code integration verified

### 2. Confluence Tools

#### 2.1 confluence_get_page ✅
- **Description**: Get content of a specific Confluence page
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Get page with metadata works:
    - Title
    - Space info
    - Version number
    - Last Modified timestamp
    - Author information
  - ✅ Get page content works (without metadata)
  - ✅ Non-existent page handling works:
    - Proper error message
    - No crash on invalid ID
  - ✅ Special characters handling works
  - ✅ Direct code integration verified
  - ✅ Error handling works correctly

#### 2.2 confluence_get_comments ✅
- **Description**: Get comments for a Confluence page
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Successfully retrieves comments from existing pages
  - ✅ Properly handles pages without comments
  - ✅ Correctly handles non-existent page errors
  - ✅ Successfully checks for special characters in comments
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 2.3 confluence_create_page ✅
- **Description**: Create new Confluence page with rich formatting
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Basic page creation works
  - ✅ Rich formatting works (headings, lists, tables, status, code)
  - ✅ Parent page handling works (with permission checks)
  - ✅ Invalid space handling works
  - ✅ Cleanup works correctly
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 2.4 confluence_update_page
- **Description**: Update existing Confluence page
- **Test Scenarios**:
  - Update page title
  - Update page content
  - Update with rich formatting
  - Update non-existent page

#### 2.5 delete_confluence_page
- **Description**: Delete a Confluence page
- **Test Scenarios**:
  - Delete existing page
  - Delete non-existent page
  - Delete page with children

### 3. Jira Tools

#### 3.1 jira_get_issue
- **Description**: Get details of a specific Jira issue
- **Test Scenarios**:
  - Get basic issue details
  - Get issue with expanded fields
  - Get non-existent issue

#### 3.2 jira_search
- **Description**: Search Jira issues using JQL
- **Test Scenarios**:
  - Search with basic JQL
  - Search with custom fields
  - Search with limit
  - Search with invalid JQL

#### 3.3 jira_get_project_issues
- **Description**: Get all issues for a project
- **Test Scenarios**:
  - Get issues with default limit
  - Get issues with custom limit
  - Get issues from non-existent project

#### 3.4 create_jira_issue
- **Description**: Create new Jira issue
- **Test Scenarios**:
  - Create basic issue
  - Create issue with custom fields
  - Create issue with attachments
  - Create issue with invalid project

#### 3.5 update_jira_issue
- **Description**: Update existing Jira issue
- **Test Scenarios**:
  - Update basic fields
  - Update custom fields
  - Update status
  - Update non-existent issue

#### 3.6 add_jira_comment
- **Description**: Add comment to Jira issue
- **Test Scenarios**:
  - Add basic comment
  - Add formatted comment
  - Add comment to non-existent issue

### 4. Template Tools

#### 4.1 get_confluence_templates
- **Description**: Get available Confluence templates
- **Test Scenarios**:
  - Get all templates
  - Get space-specific templates
  - Get templates from non-existent space

#### 4.2 get_jira_templates
- **Description**: Get available Jira templates
- **Test Scenarios**:
  - Get all templates
  - Get project-specific templates
  - Get templates from non-existent project

#### 4.3 create_from_confluence_template
- **Description**: Create page from Confluence template
- **Test Scenarios**:
  - Create with basic template
  - Create with parameters
  - Create with invalid template

#### 4.4 create_from_jira_template
- **Description**: Create issue from Jira template
- **Test Scenarios**:
  - Create with basic template
  - Create with parameters
  - Create with invalid template

## Test Implementation Plan

1. Each tool will be tested using test_mcp.py as a base
2. Tests will be organized in separate files under testlive/
3. Each test will:
   - Validate configuration
   - Test the main functionality
   - Test edge cases
   - Test error conditions
 

## Test Data Requirements

1. Valid Confluence space and pages
2. Valid Jira project and issues
3. Test templates for both platforms
4. Test attachments
5. Test user accounts with appropriate permissions

## Error Handling Tests

For each tool, test:
1. Invalid authentication
2. Network errors
3. Permission errors
4. Rate limiting
5. Invalid input data
6. Edge cases (empty/null values)

## Success Criteria

1. All tools function as documented
2. Error handling works correctly
3. Rate limiting is respected
4. Data integrity is maintained

