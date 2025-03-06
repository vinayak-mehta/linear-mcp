#!/usr/bin/env python3

import argparse
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

        return json.dumps({"message": "Created new issue", "issue": issue})
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

        return json.dumps({"message": "Updated issue", "issue": issue})
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
        return json.dumps(
            {
                "message": f"Found {len(issues)} matching issues",
                "issues": issues,
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
        return json.dumps(
            {
                "message": f"Found {len(issues)} assigned issues",
                "issues": issues,
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

        return json.dumps({"message": "Added comment", "comment": comment})
    except Exception as e:
        return f"Error: Failed to add comment - {str(e)}"


def initialize_client(api_key: str) -> None:
    """Initialize the Linear client.

    Args:
        api_key: Linear API key
    """
    global linear_client
    try:
        linear_client = LinearMCPClient.create(api_key)
    except Exception as e:
        print(f"Error initializing Linear client: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Linear MCP CLI")
    parser.add_argument(
        "--api-key",
        help="Linear API key",
        default=os.environ.get("LINEAR_API_KEY"),
    )
    args = parser.parse_args()

    if not args.api_key:
        print(
            "Error: Linear API key not provided. Set LINEAR_API_KEY environment variable or use --api-key",
            file=sys.stderr,
        )
        sys.exit(1)

    initialize_client(args.api_key)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
