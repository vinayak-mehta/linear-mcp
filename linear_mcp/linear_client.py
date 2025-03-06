from typing import Dict, List, Optional

import httpx


class LinearMCPClient:
    API_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str):
        """Initialize the Linear client.

        Args:
            api_key: Linear API key
        """
        self.api_key = api_key
        self.client = httpx.Client(
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
            }
        )

    @classmethod
    def create(cls, api_key: str) -> "LinearMCPClient":
        """Create a new Linear client instance.

        Args:
            api_key: Linear API key

        Returns:
            LinearMCPClient instance
        """
        return cls(api_key)

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query
            variables: Optional query variables

        Returns:
            Query response
        """
        response = self.client.post(
            self.API_URL,
            json={"query": query, "variables": variables or {}},
        )
        response.raise_for_status()
        return response.json()

    def list_issues(self, limit: int = 50) -> List[Dict]:
        """List recent issues.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of issues with basic details
        """
        query = """
        query ListIssues($first: Int!) {
            issues(first: $first, orderBy: updatedAt) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    url
                }
            }
        }
        """

        result = self._execute_query(query, {"first": limit})
        issues = result.get("data", {}).get("issues", {}).get("nodes", [])

        return [
            {
                "uri": f"linear-issue:///{issue['id']}",
                "mimeType": "application/json",
                "name": issue["title"],
                "description": f"Linear issue {issue['identifier']}: {issue['title']}",
                "metadata": {
                    "identifier": issue["identifier"],
                    "priority": issue.get("priority"),
                    "status": issue.get("state", {}).get("name"),
                    "assignee": issue.get("assignee", {}).get("name"),
                    "team": issue.get("team", {}).get("name"),
                },
            }
            for issue in issues
        ]

    def get_issue(self, issue_id: str) -> Dict:
        """Get details for a specific issue.

        Args:
            issue_id: Issue ID

        Returns:
            Issue details
        """
        query = """
        query GetIssue($id: ID!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                state {
                    name
                }
                assignee {
                    name
                }
                team {
                    name
                }
                url
            }
        }
        """

        result = self._execute_query(query, {"id": issue_id})
        issue = result.get("data", {}).get("issue", {})

        if not issue:
            raise ValueError(f"Issue {issue_id} not found")

        return {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue["description"],
            "priority": issue.get("priority"),
            "status": issue.get("state", {}).get("name"),
            "assignee": issue.get("assignee", {}).get("name"),
            "team": issue.get("team", {}).get("name"),
            "url": issue["url"],
        }

    def create_issue(
        self,
        title: str,
        team_id: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Create a new Linear issue.

        Args:
            title: Issue title
            team_id: Team ID
            description: Optional issue description (markdown supported)
            priority: Optional priority level (0-4)
            status: Optional initial status name

        Returns:
            Created issue details if successful, None otherwise
        """
        # First get the state ID if status is provided
        state_id = None
        if status:
            state_query = """
            query States($teamId: String!) {
                team(id: $teamId) {
                    states {
                        nodes {
                            id
                            name
                        }
                    }
                }
            }
            """
            state_result = self._execute_query(state_query, {"teamId": team_id})
            states = (
                state_result.get("data", {})
                .get("team", {})
                .get("states", {})
                .get("nodes", [])
            )
            for state in states:
                if state["name"].lower() == status.lower():
                    state_id = state["id"]
                    break

        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    state {
                        id
                        name
                    }
                    team {
                        id
                        key
                    }
                    url
                    createdAt
                }
            }
        }
        """
        variables = {
            "input": {
                "title": title,
                "teamId": team_id,
                "description": description,
                "priority": priority,
                "stateId": state_id,
            }
        }

        result = self._execute_query(mutation, variables)
        issue_result = result.get("data", {}).get("issueCreate", {})

        if not issue_result.get("success"):
            return None

        issue = issue_result.get("issue", {})
        return {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue["description"],
            "priority": issue.get("priority"),
            "state": issue["state"]["name"] if issue.get("state") else None,
            "team": issue["team"]["key"],
            "url": issue["url"],
            "created_at": issue["createdAt"],
        }

    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict]:
        """Update an existing Linear issue.

        Args:
            issue_id: Issue ID to update
            title: Optional new title
            description: Optional new description
            priority: Optional new priority (0-4)
            status: Optional new status name

        Returns:
            Updated issue details if successful, None otherwise
        """
        # First get the state ID if status is provided
        state_id = None
        if status:
            # Get the team ID first
            issue_query = """
            query Issue($id: String!) {
                issue(id: $id) {
                    team {
                        id
                    }
                }
            }
            """
            issue_result = self._execute_query(issue_query, {"id": issue_id})
            team_id = (
                issue_result.get("data", {}).get("issue", {}).get("team", {}).get("id")
            )

            if team_id:
                state_query = """
                query States($teamId: String!) {
                    team(id: $teamId) {
                        states {
                            nodes {
                                id
                                name
                            }
                        }
                    }
                }
                """
                state_result = self._execute_query(state_query, {"teamId": team_id})
                states = (
                    state_result.get("data", {})
                    .get("team", {})
                    .get("states", {})
                    .get("nodes", [])
                )
                for state in states:
                    if state["name"].lower() == status.lower():
                        state_id = state["id"]
                        break

        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    state {
                        name
                    }
                    team {
                        key
                    }
                    url
                    updatedAt
                }
            }
        }
        """

        update_input = {}
        if title is not None:
            update_input["title"] = title
        if description is not None:
            update_input["description"] = description
        if priority is not None:
            update_input["priority"] = priority
        if state_id is not None:
            update_input["stateId"] = state_id

        variables = {
            "id": issue_id,
            "input": update_input,
        }

        result = self._execute_query(mutation, variables)
        issue_result = result.get("data", {}).get("issueUpdate", {})

        if not issue_result.get("success"):
            return None

        issue = issue_result.get("issue", {})
        return {
            "id": issue["id"],
            "identifier": issue["identifier"],
            "title": issue["title"],
            "description": issue["description"],
            "priority": issue.get("priority"),
            "state": issue["state"]["name"] if issue.get("state") else None,
            "team": issue["team"]["key"],
            "url": issue["url"],
            "updated_at": issue["updatedAt"],
        }

    def search_issues(
        self,
        query: Optional[str] = None,
        team_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search issues with flexible filtering.

        Args:
            query: Optional text to search in title/description
            team_id: Optional team ID or key filter
            status: Optional status name filter
            assignee_id: Optional assignee ID filter
            labels: Optional list of label names to filter by
            priority: Optional priority level filter (0-4)
            limit: Maximum number of results to return

        Returns:
            List of matching issues
        """
        # If team_id looks like a team key (string without dashes), get the actual team ID
        if team_id and "-" not in team_id:
            team_query = """
            query Team($key: String!) {
                team(key: $key) {
                    id
                }
            }
            """
            team_result = self._execute_query(team_query, {"key": team_id})
            team_data = team_result.get("data", {}).get("team", {})
            if team_data:
                team_id = team_data.get("id")

        gql_query = """
        query SearchIssues($first: Int!, $filter: IssueFilter) {
            issues(first: $first, filter: $filter) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    state {
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        key
                    }
                    labels {
                        nodes {
                            name
                        }
                    }
                    url
                    createdAt
                }
            }
        }
        """

        filter_conditions = {}
        if query:
            filter_conditions["or"] = [
                {"title": {"contains": query}},
                {"description": {"contains": query}},
            ]
        if team_id:
            filter_conditions["team"] = {"id": {"eq": team_id}}
        if status:
            filter_conditions["state"] = {"name": {"eq": status}}
        if assignee_id:
            filter_conditions["assignee"] = {"id": {"eq": assignee_id}}
        if labels:
            filter_conditions["labels"] = {"some": {"name": {"in": labels}}}
        if priority is not None:
            filter_conditions["priority"] = {"eq": priority}

        variables = {
            "first": limit,
            "filter": filter_conditions,
        }

        try:
            result = self._execute_query(gql_query, variables)
            data = result.get("data", {})
            if not data:
                error = result.get("errors", [{}])[0].get("message", "Unknown error")
                raise Exception(error)

            issues = data.get("issues", {}).get("nodes", [])
            return [
                {
                    "id": issue["id"],
                    "identifier": issue["identifier"],
                    "title": issue["title"],
                    "description": issue.get("description"),
                    "priority": issue.get("priority"),
                    "state": issue.get("state", {}).get("name"),
                    "assignee": {
                        "id": issue["assignee"]["id"],
                        "name": issue["assignee"]["name"],
                    }
                    if issue.get("assignee")
                    else None,
                    "team": {
                        "id": issue["team"]["id"],
                        "key": issue["team"]["key"],
                    }
                    if issue.get("team")
                    else None,
                    "labels": [
                        label["name"]
                        for label in issue.get("labels", {}).get("nodes", [])
                    ]
                    if issue.get("labels")
                    else [],
                    "url": issue["url"],
                    "created_at": issue["createdAt"],
                }
                for issue in issues
            ]
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    def get_user_issues(
        self,
        user_id: Optional[str] = None,
        include_archived: bool = False,
        limit: int = 50,
    ) -> List[Dict]:
        """Get issues assigned to a user.

        Args:
            user_id: Optional user ID (omit for authenticated user)
            include_archived: Whether to include archived issues
            limit: Maximum number of results to return

        Returns:
            List of issues assigned to the user
        """
        if user_id:
            query = """
            query UserIssues($userId: String!, $first: Int!, $includeArchived: Boolean) {
                user(id: $userId) {
                    assignedIssues(first: $first, includeArchived: $includeArchived) {
                        nodes {
                            id
                            identifier
                            title
                            description
                            priority
                            state {
                                name
                            }
                            team {
                                key
                            }
                            url
                            createdAt
                            archivedAt
                        }
                    }
                }
            }
            """
            variables = {
                "userId": user_id,
                "first": limit,
                "includeArchived": include_archived,
            }
            result = self._execute_query(query, variables)
            issues = (
                result.get("data", {})
                .get("user", {})
                .get("assignedIssues", {})
                .get("nodes", [])
            )
        else:
            query = """
            query ViewerIssues($first: Int!, $includeArchived: Boolean) {
                viewer {
                    assignedIssues(first: $first, includeArchived: $includeArchived) {
                        nodes {
                            id
                            identifier
                            title
                            description
                            priority
                            state {
                                name
                            }
                            team {
                                key
                            }
                            url
                            createdAt
                            archivedAt
                        }
                    }
                }
            }
            """
            variables = {
                "first": limit,
                "includeArchived": include_archived,
            }
            result = self._execute_query(query, variables)
            issues = (
                result.get("data", {})
                .get("viewer", {})
                .get("assignedIssues", {})
                .get("nodes", [])
            )

        return [
            {
                "id": issue["id"],
                "identifier": issue["identifier"],
                "title": issue["title"],
                "description": issue.get("description"),
                "priority": issue.get("priority"),
                "state": issue["state"]["name"] if issue.get("state") else None,
                "team": issue["team"]["key"],
                "url": issue["url"],
                "created_at": issue["createdAt"],
                "archived_at": issue.get("archivedAt"),
            }
            for issue in issues
        ]

    def add_comment(
        self,
        issue_id: str,
        body: str,
        create_as_user: Optional[str] = None,
        display_icon_url: Optional[str] = None,
    ) -> Optional[Dict]:
        """Add a comment to an issue.

        Args:
            issue_id: Issue ID to comment on
            body: Comment text (markdown supported)
            create_as_user: Optional custom username
            display_icon_url: Optional custom avatar URL

        Returns:
            Created comment details if successful, None otherwise
        """
        mutation = """
        mutation CreateComment($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    user {
                        name
                    }
                    createdAt
                }
            }
        }
        """

        variables = {
            "input": {
                "issueId": issue_id,
                "body": body,
            }
        }

        if create_as_user:
            variables["input"]["createAsUser"] = create_as_user
        if display_icon_url:
            variables["input"]["displayIconUrl"] = display_icon_url

        result = self._execute_query(mutation, variables)
        comment_result = result.get("data", {}).get("commentCreate", {})

        if not comment_result.get("success"):
            return None

        comment = comment_result.get("comment", {})
        return {
            "id": comment["id"],
            "body": comment["body"],
            "user": comment["user"]["name"] if comment.get("user") else None,
            "created_at": comment["createdAt"],
        }

    def get_team_issues(self, team_id: str) -> List[Dict]:
        """Get issues for a specific team.

        Args:
            team_id: Team ID

        Returns:
            List of team issues
        """
        query = """
        query GetTeamIssues($teamId: ID!) {
            team(id: $teamId) {
                issues {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        state {
                            name
                        }
                        assignee {
                            name
                        }
                        url
                    }
                }
            }
        }
        """

        result = self._execute_query(query, {"teamId": team_id})

        if not result.get("data", {}).get("team"):
            raise ValueError(f"Team {team_id} not found")

        issues = (
            result.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
        )

        return [
            {
                "id": issue["id"],
                "identifier": issue["identifier"],
                "title": issue["title"],
                "description": issue.get("description"),
                "priority": issue.get("priority"),
                "status": issue.get("state", {}).get("name"),
                "assignee": issue.get("assignee", {}).get("name"),
                "url": issue["url"],
            }
            for issue in issues
        ]

    def get_viewer(self) -> Dict:
        """Get information about the authenticated user.

        Returns:
            User information including teams and organization
        """
        query = """
        query {
            viewer {
                id
                name
                email
                admin
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
            }
            organization {
                id
                name
                urlKey
            }
        }
        """

        result = self._execute_query(query)

        viewer = result.get("data", {}).get("viewer", {})
        organization = result.get("data", {}).get("organization", {})

        return {
            "id": viewer["id"],
            "name": viewer["name"],
            "email": viewer.get("email"),
            "admin": viewer.get("admin"),
            "teams": [
                {"id": team["id"], "name": team["name"], "key": team["key"]}
                for team in viewer.get("teams", {}).get("nodes", [])
            ],
            "organization": {
                "id": organization["id"],
                "name": organization["name"],
                "urlKey": organization["urlKey"],
            },
        }

    def get_organization(self) -> Dict:
        """Get information about the organization.

        Returns:
            Organization information including teams and users
        """
        query = """
        query {
            organization {
                id
                name
                urlKey
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
                users {
                    nodes {
                        id
                        name
                        email
                        admin
                        active
                    }
                }
            }
        }
        """

        result = self._execute_query(query)

        organization = result.get("data", {}).get("organization", {})

        return {
            "id": organization["id"],
            "name": organization["name"],
            "urlKey": organization["urlKey"],
            "teams": [
                {"id": team["id"], "name": team["name"], "key": team["key"]}
                for team in organization.get("teams", {}).get("nodes", [])
            ],
            "users": [
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user.get("email"),
                    "admin": user.get("admin"),
                    "active": user.get("active"),
                }
                for user in organization.get("users", {}).get("nodes", [])
            ],
        }
