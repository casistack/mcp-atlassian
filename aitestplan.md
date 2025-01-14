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
6. Make sure you are using the actual method in our code base this way we will know if theres an issue in our code base. 

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
5. Draw.io Tools

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

#### 2.4 confluence_update_page ✅
- **Description**: Update existing Confluence page
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Title update works (version incremented correctly)
  - ✅ Content update with rich formatting works
  - ✅ Version numbers increment correctly
  - ✅ Non-existent page handling works
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified
  - ✅ Cleanup works correctly

#### 2.5 delete_confluence_page
- **Description**: Delete a Confluence page
- **Test Scenarios**:
  - Delete existing page
  - Delete non-existent page
  - Delete page with children

### 3. Jira Tools

#### 3.1 jira_get_issue ✅
- **Description**: Get details of a specific Jira issue
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Basic issue retrieval works:
    - Project detection
    - Issue type selection
    - Issue creation
    - Issue metadata retrieval
  - ✅ Expanded fields retrieval works:
    - Description
    - Created/Updated dates
    - Additional metadata
  - ✅ Non-existent issue handling works
  - ✅ Cleanup works correctly
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 3.2 jira_search ✅
- **Description**: Search Jira issues using JQL
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Basic JQL search works:
    - Project-based search
    - Multiple results returned
    - Full metadata (key, summary, status, type)
  - ✅ Custom fields search works:
    - Type filtering
    - Field combinations
  - ✅ Limit parameter works:
    - Successfully limited to 2 results
    - Maintains result order
  - ✅ Invalid JQL handling works:
    - Proper error message
    - Graceful failure
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 3.3 jira_get_project_issues ✅
- **Description**: Get all issues for a project
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Default limit retrieval works:
    - Successfully gets all project issues
    - Full metadata returned (key, summary, status, type)
    - Proper ordering maintained
  - ✅ Custom limit works:
    - Successfully limited to 2 results
    - Correct metadata returned
    - Most recent issues returned first
  - ✅ Non-existent project handling works:
    - Proper error message returned
    - Clear validation message about invalid project
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 3.4 create_jira_issue ✅
- **Description**: Create new Jira issue
- **Status**: WORKING
- **Test Results**:
  - ✅ Basic issue creation works:
    - Project detection
    - Issue type selection
    - Basic fields (summary, description)
    - Status verification
  - ✅ Labels handling works
  - ✅ Priority and custom fields removed for simplicity
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified

#### 3.5 update_jira_issue ⚠️
- **Description**: Update existing Jira issue
- **Status**: PARTIALLY WORKING
- **Test Results**:
  - ❌ Basic fields update not working (summary, description, priority)
  - ✅ Status update works
  - ✅ Labels update works
  - ❌ Custom fields update not tested
  - ✅ Error handling for non-existent issues works
  - ⚠️ Needs further investigation on basic fields update failure

#### 3.6 add_jira_comment ❌
- **Description**: Add comment to Jira issue
- **Status**: NOT WORKING
- **Test Results**:
  - ❌ Basic comment addition fails
  - ❌ Formatted comment fails
  - ❌ Mentions and links fails
  - ✅ Error handling works as expected
  - ⚠️ Needs implementation fix in JiraFetcher class

#### 3.7 delete_jira_issue ❌
- **Description**: Delete a Jira issue
- **Status**: NOT IMPLEMENTED
- **Test Results**:
  - ❌ Tool not found in available tools
  - ⚠️ Need to add delete_jira_issue to available tools
  - ⚠️ Need to implement cleanup functionality

### 4. Template Tools

#### 4.1 get_confluence_templates ✅
- **Description**: Get available Confluence templates
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Get all templates works
  - ✅ Space-specific templates works
  - ✅ Non-existent space handling works
  - ✅ Error handling works correctly
  - ✅ Direct code integration verified

#### 4.2 get_jira_templates ✅
- **Description**: Get available Jira templates
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Implementation correctly uses Jira API endpoints:
    - Uses createmeta for project-specific templates
    - Uses issue_types for global templates
  - ✅ Error handling works correctly
  - ✅ Returns empty list when no templates exist
  - ✅ Proper debug logging implemented
  - ✅ Non-existent project handling works
- **Notes**:
  - Currently returns empty list because no templates are configured in the Jira instance
  - This is expected behavior, not a bug
  - To get templates, would need to:
    - Configure issue types in Jira
    - Set up project-specific templates
    - Have proper permissions

#### 4.3 create_from_confluence_template ✅
- **Description**: Create a page from a Confluence template
- **Status**: TESTED & WORKING
- **Test Results**:
  - ✅ Basic template usage with parameters works
  - ✅ Template usage without parameters works
  - ✅ Invalid template handling works correctly
  - ✅ Page cleanup works correctly
  - ✅ Error handling works as expected
  - ✅ Direct code integration verified
  - ✅ Returns proper response format:
    - page_id
    - title
    - url
    - content

#### 4.4 create_from_jira_template
- **Description**: Create issue from Jira template
- **Test Scenarios**:
  - Create with basic template
  - Create with parameters
  - Create with invalid template

### 5. Draw.io Tools

#### 5.1 create_diagram ⚠️
- **Description**: Create new draw.io diagrams in Confluence pages
- **Status**: NEEDS TESTING
- **Test Scenarios**:
  - Create network diagram with multiple nodes and connections
  - Create flowchart with decision points
  - Create cloud architecture diagram
  - Test all shape types and connectors
  - Test styling options
  - Test error handling

#### 5.2 update_diagram ⚠️
- **Description**: Update existing draw.io diagrams
- **Status**: NEEDS TESTING
- **Test Scenarios**:
  - Update element positions
  - Add new elements
  - Modify connections
  - Update styles
  - Test error handling for invalid macro IDs

#### 5.3 get_diagram ⚠️
- **Description**: Retrieve diagram data and metadata
- **Status**: NEEDS TESTING
- **Test Scenarios**:
  - Get diagram content
  - Get diagram metadata
  - Test error handling for non-existent diagrams
  - Verify data structure matches schema

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

## Next Steps

1. Priority Fixes Needed:
   - Implement delete_jira_issue tool for proper test cleanup
   - Fix basic fields update in update_jira_issue
   - Fix comment functionality in add_jira_comment
   - Add better error logging for debugging failures

2. Investigation Needed:
   - Root cause of basic fields update failure
   - Why comment addition is failing
   - Proper way to handle status transitions

3. Future Improvements:
   - Add retry logic for failed operations
   - Implement proper test cleanup
   - Add more detailed error messages
   - Add validation for field values before updates

