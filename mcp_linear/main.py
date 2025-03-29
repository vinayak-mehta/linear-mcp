#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .linear_client import LinearMCPClient

# Find and load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Warning: No .env file found at {env_path}", file=sys.stderr)

# Initialize FastMCP server
mcp = FastMCP("linear")

# Initialize global client
linear_client = None


@mcp.tool()
async def linear_create_issue(
    title: str,
    team_id: str,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
) -> str:
    """Create a new Linear issue.

    Args:
        title: Issue title
        team_id: Team ID to create issue in
        description: Issue description (markdown supported)
        priority: Priority level (1=urgent, 4=low)
        status: Initial status name
    """
    global linear_client
    if not linear_client:
        return "Error: Linear client not initialized"

    try:
        issue = linear_client.create_issue(
            title=title,
            team_id=team_id,
            description=description,
            priority=priority,
            status=status,
        )
        if not issue:
            return "Error: Failed to create issue"

        return json.dumps(
            {
                "message": f"Created issue {issue.get('identifier')}: {issue.get('title')}",
                "issue": issue,
            }
        )
    except Exception as e:
        return f"Error: Failed to create issue - {str(e)}"


@mcp.tool()
async def linear_update_issue(
    id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
) -> str:
    """Update an existing Linear issue.

    Args:
        id: Issue ID to update
        title: New title
        description: New description
        priority: New priority (1=urgent, 4=low)
        status: New status name
    """
    global linear_client
    if not linear_client:
        return "Error: Linear client not initialized"

    try:
        issue = linear_client.update_issue(
            issue_id=id,
            title=title,
            description=description,
            priority=priority,
            status=status,
        )
        if not issue:
            return "Error: Failed to update issue"

        return json.dumps(
            {"message": f"Updated issue {issue.get('identifier')}", "issue": issue}
        )
    except Exception as e:
        return f"Error: Failed to update issue - {str(e)}"


@mcp.tool()
async def linear_search_issues(
    query: Optional[str] = None,
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[int] = None,
    estimate: Optional[int] = None,
    include_archived: Optional[bool] = False,
    limit: int = 10,
) -> str:
    """Search issues with flexible filtering.

    Args:
        query: Text to search in title/description
        team_id: Filter by team
        status: Filter by status
        assignee_id: Filter by assignee
        labels: Filter by labels
        priority: Filter by priority
        estimate: Filter by estimate points
        include_archived: Include archived issues
        limit: Max results (default: 10)
    """
    global linear_client
    if not linear_client:
        return "Error: Linear client not initialized"

    try:
        issues = linear_client.search_issues(
            query=query,
            team_id=team_id,
            status=status,
            assignee_id=assignee_id,
            labels=labels,
            priority=priority,
            limit=limit,
        )

        issue_list = "\n".join(
            [
                f"- {issue.get('identifier')}: {issue.get('title')}\n  "
                f"Priority: {issue.get('priority') or 'None'}, "
                f"Status: {issue.get('state') or 'None'}\n  "
                f"{issue.get('url')}"
                for issue in issues
            ]
        )

        return json.dumps(
            {
                "message": f"Found {len(issues)} matching issues",
                "issues": issues,
                "text": f"Found {len(issues)} issues:\n{issue_list}",
            }
        )
    except Exception as e:
        return f"Error: Failed to search issues - {str(e)}"


@mcp.tool()
async def linear_get_user_issues(
    user_id: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 50,
) -> str:
    """Get issues assigned to a user.

    Args:
        user_id: User ID (omit for authenticated user)
        include_archived: Include archived issues
        limit: Max results (default: 50)
    """
    global linear_client
    if not linear_client:
        return "Error: Linear client not initialized"

    try:
        issues = linear_client.get_user_issues(
            user_id=user_id,
            include_archived=include_archived,
            limit=limit,
        )

        issue_list = "\n".join(
            [
                f"- {issue.get('identifier')}: {issue.get('title')}\n  "
                f"Priority: {issue.get('priority') or 'None'}, "
                f"Status: {issue.get('state') or 'Unknown'}\n  "
                f"{issue.get('url')}"
                for issue in issues
            ]
        )

        return json.dumps(
            {
                "message": f"Found {len(issues)} assigned issues",
                "issues": issues,
                "text": f"Found {len(issues)} issues:\n{issue_list}",
            }
        )
    except Exception as e:
        return f"Error: Failed to get user issues - {str(e)}"


@mcp.tool()
async def linear_add_comment(
    issue_id: str,
    body: str,
    create_as_user: Optional[str] = None,
    display_icon_url: Optional[str] = None,
) -> str:
    """Add a comment to an issue.

    Args:
        issue_id: Issue ID to comment on
        body: Comment text (markdown supported)
        create_as_user: Custom username
        display_icon_url: Custom avatar URL
    """
    global linear_client
    if not linear_client:
        return "Error: Linear client not initialized"

    try:
        comment = linear_client.add_comment(
            issue_id=issue_id,
            body=body,
            create_as_user=create_as_user,
            display_icon_url=display_icon_url,
        )
        if not comment:
            return "Error: Failed to add comment"

        return json.dumps(
            {
                "message": f"Added comment to issue {comment.get('issue', {}).get('identifier')}",
                "comment": comment,
            }
        )
    except Exception as e:
        return f"Error: Failed to add comment - {str(e)}"


@mcp.resource("linear-issue:///{issue_id}")
async def get_issue(issue_id: str) -> Dict:
    """Get a Linear issue by ID.

    Args:
        issue_id: Issue ID

    Returns:
        Issue details
    """
    global linear_client
    if not linear_client:
        return {"error": "Linear client not initialized"}

    try:
        issue = linear_client.get_issue(issue_id)
        return {"mimeType": "application/json", "data": issue}
    except Exception as e:
        return {"error": f"Failed to get issue: {str(e)}"}


@mcp.resource("linear-team:///{team_id}/issues")
async def get_team_issues(team_id: str) -> Dict:
    """Get issues for a Linear team.

    Args:
        team_id: Team ID

    Returns:
        Team issues
    """
    global linear_client
    if not linear_client:
        return {"error": "Linear client not initialized"}

    try:
        issues = linear_client.get_team_issues(team_id)
        return {"mimeType": "application/json", "data": issues}
    except Exception as e:
        return {"error": f"Failed to get team issues: {str(e)}"}


@mcp.resource("linear-user:///{user_id}/assigned")
async def get_user_assigned(user_id: str) -> Dict:
    """Get issues assigned to a user.

    Args:
        user_id: User ID (use 'me' for authenticated user)

    Returns:
        User's assigned issues
    """
    global linear_client
    if not linear_client:
        return {"error": "Linear client not initialized"}

    try:
        # Handle 'me' special case
        actual_user_id = None if user_id == "me" else user_id
        issues = linear_client.get_user_issues(user_id=actual_user_id)
        return {"mimeType": "application/json", "data": issues}
    except Exception as e:
        return {"error": f"Failed to get user issues: {str(e)}"}


@mcp.resource("linear-organization:")
async def get_organization() -> Dict:
    """Get the Linear organization.

    Returns:
        Organization details
    """
    global linear_client
    if not linear_client:
        return {"error": "Linear client not initialized"}

    try:
        org = linear_client.get_organization()
        return {"mimeType": "application/json", "data": org}
    except Exception as e:
        return {"error": f"Failed to get organization: {str(e)}"}


@mcp.resource("linear-viewer:")
async def get_viewer() -> Dict:
    """Get the authenticated user (viewer).

    Returns:
        User details
    """
    global linear_client
    if not linear_client:
        return {"error": "Linear client not initialized"}

    try:
        viewer = linear_client.get_viewer()
        return {"mimeType": "application/json", "data": viewer}
    except Exception as e:
        return {"error": f"Failed to get viewer: {str(e)}"}


@mcp.prompt("default")
def get_default_prompt() -> str:
    """Get the default prompt for the Linear MCP server."""
    return """This server provides access to Linear, a project management tool. Use it to manage issues, track work, and coordinate with teams.

Key capabilities:
- Create and update issues: Create new tickets or modify existing ones with titles, descriptions, priorities, and team assignments.
- Search functionality: Find issues across the organization using flexible search queries with team and user filters.
- Team coordination: Access team-specific issues and manage work distribution within teams.
- Issue tracking: Add comments and track progress through status updates and assignments.
- Organization overview: View team structures and user assignments across the organization.

Tool Usage:
- linear_create_issue:
  - use teamId from linear-organization: resource
  - priority levels: 1=urgent, 2=high, 3=normal, 4=low
  - status must match exact Linear workflow state names (e.g., "In Progress", "Done")

- linear_update_issue:
  - get issue IDs from search_issues or linear-issue:/// resources
  - only include fields you want to change
  - status changes must use valid state IDs from the team's workflow

- linear_search_issues:
  - combine multiple filters for precise results
  - use labels array for multiple tag filtering
  - query searches both title and description
  - returns max 10 results by default

- linear_get_user_issues:
  - omit userId to get authenticated user's issues
  - useful for workload analysis and sprint planning
  - returns most recently updated issues first

- linear_add_comment:
  - supports full markdown formatting
  - use displayIconUrl for bot/integration avatars
  - createAsUser for custom comment attribution

Best practices:
- When creating issues:
  - Write clear, actionable titles that describe the task well (e.g., "Implement user authentication for mobile app")
  - Include concise but appropriately detailed descriptions in markdown format with context and acceptance criteria
  - Set appropriate priority based on the context (1=critical to 4=nice-to-have)
  - Always specify the correct team ID (default to the user's team if possible)

- When searching:
  - Use specific, targeted queries for better results (e.g., "auth mobile app" rather than just "auth")
  - Apply relevant filters when asked or when you can infer the appropriate filters to narrow results

- When adding comments:
  - Use markdown formatting to improve readability and structure
  - Keep content focused on the specific issue and relevant updates
  - Include action items or next steps when appropriate

- General best practices:
  - Fetch organization data first to get valid team IDs
  - Use search_issues to find issues for bulk operations
  - Include markdown formatting in descriptions and comments

Resource patterns:
- linear-issue:///{issueId} - Single issue details (e.g., linear-issue:///c2b318fb-95d2-4a81-9539-f3268f34af87)
- linear-team:///{teamId}/issues - Team's issue list (e.g., linear-team:///OPS/issues)
- linear-user:///{userId}/assigned - User assignments (e.g., linear-user:///USER-123/assigned)
- linear-organization: - Organization for the current user
- linear-viewer: - Current user context

The server uses the authenticated user's permissions for all operations."""


def initialize_client(api_key: str) -> None:
    """Initialize the Linear client.

    Args:
        api_key: Linear API key
    """
    global linear_client
    try:
        linear_client = LinearMCPClient(api_key)
    except Exception as e:
        print(f"Error initializing Linear client: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    api_key = os.environ.get("LINEAR_API_KEY")

    if not api_key:
        print(
            "Error: LINEAR_API_KEY not found in environment variables or .env file",
            file=sys.stderr,
        )
        sys.exit(1)

    initialize_client(api_key)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
