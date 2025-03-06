# Linear MCP

A Linear MCP (Model Control Protocol) implementation that allows you to interact with Linear through Claude. This MCP provides functionality to list, search, read, create, and update Linear issues using Linear's GraphQL API.

## Features

- Create and update issues with support for:
  - Title and description (markdown supported)
  - Priority levels (1=urgent to 4=low)
  - Status/state assignment
  - Team assignment
- Search issues with flexible filtering:
  - Text search in title/description
  - Filter by team (using ID or key)
  - Filter by status
  - Filter by assignee
  - Filter by labels
  - Filter by priority
- View user's assigned issues
  - Support for both authenticated user and specific users
  - Option to include archived issues
- Add comments to issues
  - Markdown support
  - Custom username and avatar options

## Installation

1. Clone this repository
2. Install the package:
```bash
pip install -e .
```

## Configuration

You'll need a Linear API key to use this MCP. You can get one from your Linear settings page:

1. Go to your Linear settings
2. Navigate to "API" section
3. Create a new API key

Then, either:
- Set the `LINEAR_API_KEY` environment variable:
  ```bash
  export LINEAR_API_KEY="your_api_key_here"
  ```
- Or create a `.env` file in the project root:
  ```
  LINEAR_API_KEY=your_api_key_here
  ```
- Or pass the API key directly using the `--api-key` flag

## Usage

Run the MCP:

```bash
linear-mcp
```

Or with a direct API key:

```bash
linear-mcp --api-key "your_api_key_here"
```

## Available Tools

### 1. linear_create_issue

Create a new Linear issue.

**Required Parameters:**
- `title` (string): Issue title
- `team_id` (string): Team ID to create issue in (can be team ID or key)

**Optional Parameters:**
- `description` (string): Issue description (markdown supported)
- `priority` (number): Priority level (1=urgent, 2=high, 3=normal, 4=low)
- `status` (string): Initial status name (e.g., "Todo", "In Progress")

**Example Prompts:**
- "Create a new urgent issue in the engineering team titled 'Fix login bug' with description 'Users are unable to log in using SSO'"
- "Create a high priority issue for team 'product' called 'Update onboarding flow' and set it to In Progress"
- "Create an issue titled 'Improve error handling' in eng team with normal priority and this description: '- Add better validation\n- Improve error messages\n- Add retry logic'"

### 2. linear_update_issue

Update an existing Linear issue.

**Required Parameters:**
- `id` (string): Issue ID to update (e.g., "ISS-123")

**Optional Parameters:**
- `title` (string): New title
- `description` (string): New description (markdown supported)
- `priority` (number): New priority level (1=urgent to 4=low)
- `status` (string): New status name

**Example Prompts:**
- "Update issue ISS-123 to high priority and change status to In Review"
- "Change the title of issue ISS-456 to 'Refactor authentication system'"
- "Update ISS-789's description to add these reproduction steps: '1. Log in\n2. Navigate to settings\n3. Error occurs'"

### 3. linear_search_issues

Search issues with flexible filtering.

**Optional Parameters:**
- `query` (string): Text to search in title/description
- `team_id` (string): Filter by team (accepts team ID or key)
- `status` (string): Filter by status name
- `assignee_id` (string): Filter by assignee
- `labels` (string[]): Filter by labels
- `priority` (number): Filter by priority level (1-4)
- `limit` (number): Max results (default: 10)

**Example Prompts:**
- "Find all urgent priority issues in the engineering team"
- "Search for issues containing 'login' or 'authentication' with status In Progress"
- "Show me the last 20 issues labeled as 'bug' assigned to user_123"
- "Find all high priority issues in the product team that are in review"

### 4. linear_get_user_issues

Get issues assigned to a user.

**Optional Parameters:**
- `user_id` (string): User ID (omit for authenticated user)
- `include_archived` (boolean): Include archived issues (default: false)
- `limit` (number): Max results (default: 50)

**Example Prompts:**
- "Show me all my assigned issues"
- "Get the last 30 issues assigned to user_123"
- "List all issues assigned to me, including archived ones"
- "Show active issues assigned to user_456 with a limit of 10"

### 5. linear_add_comment

Add a comment to an issue.

**Required Parameters:**
- `issue_id` (string): Issue ID to comment on
- `body` (string): Comment text (markdown supported)

**Optional Parameters:**
- `create_as_user` (string): Custom username for the comment
- `display_icon_url` (string): Custom avatar URL for the comment

**Example Prompts:**
- "Add a comment to ISS-123: 'Fixed in latest deployment, please verify'"
- "Comment on ISS-456 as CI Bot: 'All tests passing in main branch'"
- "Add comment to ISS-789: '### Testing Results\n- ✅ Unit tests\n- ✅ Integration tests\n- ⚠️ Performance test pending'"
- "Leave a comment on ISS-234 with bot avatar: 'Automated security scan completed successfully'"

## Notes

- Priority levels:
  - 1: Urgent
  - 2: High
  - 3: Normal
  - 4: Low
- Team IDs can be provided as either:
  - Team key (e.g., "eng", "product")
  - Full team ID (e.g., "team_123")
- Status names should match your Linear workspace's configured states
- All timestamps are in ISO 8601 format
- Markdown is supported in descriptions and comments
- When writing prompts:
  - You don't need to specify all parameters
  - Use natural language
  - The system will understand common variations
  - You can combine multiple criteria in a single search
  - Issue IDs can be written with or without the "ISS-" prefix
