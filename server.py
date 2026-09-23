import json
import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from pydantic import Field

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_DATA_PATH = Path(__file__).parent / "data" / "asana.json"
_db: dict = json.loads(_DATA_PATH.read_text())


def _match(record: dict, field: str, value: str) -> bool:
    """Case-insensitive substring match on a field."""
    return value.lower() in str(record.get(field, "")).lower()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="asana-mock",
    version="1.0.0",
    instructions=(
        "Mock Asana project management for Olaplex hair care brand. Query workspaces, "
        "projects, tasks, sections, subtasks, comments, tags, portfolios, and goals. "
        "Use asana_task_search to find tasks across projects. Key projects: No.9 Bond "
        "Protector Launch, Henkel Integration, Holiday Campaign 2026, Scalp Serum "
        "Development, E-commerce Migration."
    ),
)

# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_workspace_get_all() -> list[dict]:
    """Return all Asana workspaces."""
    return _db["workspaces"]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_user_get_all(
    team_gid: Optional[str] = Field(default=None, description="Filter users by team GID (not directly stored on user; returns all workspace members when provided)"),
    workspace_gid: Optional[str] = Field(default=None, description="Filter users by workspace GID"),
) -> list[dict]:
    """Return all users. Optionally filter by workspace GID."""
    results = _db["users"]
    if workspace_gid:
        results = [
            u for u in results
            if any(w["gid"] == workspace_gid for w in u.get("workspaces", []))
        ]
    return results


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_team_get_all(
    workspace_gid: Optional[str] = Field(default=None, description="Filter teams by workspace/organization GID"),
) -> list[dict]:
    """Return all teams. Optionally filter by workspace GID."""
    results = _db["teams"]
    if workspace_gid:
        results = [t for t in results if t.get("organization_gid") == workspace_gid]
    return results


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_project_get_all(
    team_gid: Optional[str] = Field(default=None, description="Filter projects by team GID"),
    workspace_gid: Optional[str] = Field(default=None, description="Filter projects by workspace GID"),
    archived: Optional[bool] = Field(default=None, description="Filter by archived status (true/false)"),
    search: Optional[str] = Field(default=None, description="Partial match on project name"),
) -> list[dict]:
    """Return all projects. Filter by team, workspace, archived status, or name search."""
    results = _db["projects"]
    if team_gid:
        results = [p for p in results if p.get("team_gid") == team_gid]
    if workspace_gid:
        results = [p for p in results if p.get("workspace_gid") == workspace_gid]
    if archived is not None:
        is_archived = archived
        results = [p for p in results if p.get("completed", False) == is_archived]
    if search:
        results = [p for p in results if _match(p, "name", search)]
    return results


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_section_get_all(
    project_gid: Optional[str] = Field(default=None, description="Filter sections by project GID"),
    project_name: Optional[str] = Field(default=None, description="Filter sections by project name (partial match)"),
) -> list[dict]:
    """Return sections. Filter by project GID or project name."""
    results = _db["sections"]
    if project_gid:
        results = [s for s in results if s.get("project_gid") == project_gid]
    if project_name:
        results = [s for s in results if _match(s, "project_name", project_name)]
    return results


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_task_get_all(
    project_gid: Optional[str] = Field(default=None, description="Filter tasks by project GID"),
    project_name: Optional[str] = Field(default=None, description="Filter tasks by project name (partial match)"),
    section_gid: Optional[str] = Field(default=None, description="Filter tasks by section GID"),
    assignee_name: Optional[str] = Field(default=None, description="Filter tasks by assignee name (partial match)"),
    completed: Optional[bool] = Field(default=None, description="Filter by completion status"),
    tag: Optional[str] = Field(default=None, description="Filter tasks that include this tag name"),
    priority: Optional[str] = Field(default=None, description="Filter by priority: high | medium | low"),
    search: Optional[str] = Field(default=None, description="Partial match on task name or notes"),
) -> list[dict]:
    """Return tasks with optional filters for project, section, assignee, completion, tag, priority, or text search."""
    results = _db["tasks"]
    if project_gid:
        results = [t for t in results if t.get("project_gid") == project_gid]
    if project_name:
        results = [t for t in results if _match(t, "project_name", project_name)]
    if section_gid:
        results = [t for t in results if t.get("section_gid") == section_gid]
    if assignee_name:
        results = [t for t in results if _match(t, "assignee_name", assignee_name)]
    if completed is not None:
        results = [t for t in results if t.get("completed") == completed]
    if tag:
        tag_lower = tag.lower()
        results = [t for t in results if tag_lower in [tg.lower() for tg in t.get("tags", [])]]
    if priority:
        results = [t for t in results if _match(t, "priority", priority)]
    if search:
        results = [
            t for t in results
            if _match(t, "name", search) or _match(t, "notes", search)
        ]
    return results


@mcp.tool()
def asana_task_get_by_gid(
    gid: str = Field(description="The GID of the task to retrieve"),
) -> dict:
    """Get a single task by its GID."""
    for task in _db["tasks"]:
        if task["gid"] == gid:
            return task
    return {"error": f"Task with gid '{gid}' not found."}


# ---------------------------------------------------------------------------
# Subtasks
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_subtask_get_all(
    parent_gid: Optional[str] = Field(default=None, description="Filter subtasks by parent task GID"),
    parent_name: Optional[str] = Field(default=None, description="Filter subtasks by parent task name (partial match)"),
) -> list[dict]:
    """Return subtasks. Filter by parent task GID or parent task name."""
    results = _db["subtasks"]
    if parent_gid:
        results = [s for s in results if s.get("parent_gid") == parent_gid]
    if parent_name:
        results = [s for s in results if _match(s, "parent_name", parent_name)]
    return results


# ---------------------------------------------------------------------------
# Stories (comments / activity)
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_story_get_all(
    task_gid: Optional[str] = Field(default=None, description="Filter stories by task GID"),
    task_name: Optional[str] = Field(default=None, description="Filter stories by task name (partial match)"),
) -> list[dict]:
    """Return stories (comments and activity) for tasks. Filter by task GID or task name."""
    results = _db["stories"]
    if task_gid:
        results = [s for s in results if s.get("task_gid") == task_gid]
    if task_name:
        results = [s for s in results if _match(s, "task_name", task_name)]
    return results


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_tag_get_all(
    workspace_gid: Optional[str] = Field(default=None, description="Filter tags by workspace GID"),
) -> list[dict]:
    """Return all tags. Optionally filter by workspace GID."""
    results = _db["tags"]
    if workspace_gid:
        results = [t for t in results if t.get("workspace_gid") == workspace_gid]
    return results


# ---------------------------------------------------------------------------
# Portfolios
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_portfolio_get_all(
    workspace_gid: Optional[str] = Field(default=None, description="Filter portfolios by workspace GID"),
    owner_name: Optional[str] = Field(default=None, description="Filter portfolios by owner name (partial match)"),
) -> list[dict]:
    """Return all portfolios. Filter by workspace GID or owner name."""
    results = _db["portfolios"]
    if workspace_gid:
        results = [p for p in results if p.get("workspace_gid") == workspace_gid]
    if owner_name:
        results = [p for p in results if _match(p, "owner_name", owner_name)]
    return results


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_goal_get_all(
    workspace_gid: Optional[str] = Field(default=None, description="Filter goals by workspace GID"),
    status: Optional[str] = Field(default=None, description="Filter by status: on_track | at_risk | off_track"),
    owner_name: Optional[str] = Field(default=None, description="Filter goals by owner name (partial match)"),
) -> list[dict]:
    """Return all goals. Filter by workspace GID, status, or owner name."""
    results = _db["goals"]
    if workspace_gid:
        results = [g for g in results if g.get("workspace_gid") == workspace_gid]
    if status:
        results = [g for g in results if _match(g, "status", status)]
    if owner_name:
        results = [g for g in results if _match(g, "owner_name", owner_name)]
    return results


# ---------------------------------------------------------------------------
# Task Search
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_task_search(
    query: str = Field(description="Search query matched against task name and notes (partial match)"),
    project_gid: Optional[str] = Field(default=None, description="Restrict search to a specific project GID"),
    completed: Optional[bool] = Field(default=None, description="Filter by completion status"),
    assignee_name: Optional[str] = Field(default=None, description="Filter by assignee name (partial match)"),
) -> list[dict]:
    """Advanced full-text search across all tasks by name and notes. Optionally filter by project, completion, or assignee."""
    results = _db["tasks"]
    results = [
        t for t in results
        if _match(t, "name", query) or _match(t, "notes", query)
    ]
    if project_gid:
        results = [t for t in results if t.get("project_gid") == project_gid]
    if completed is not None:
        results = [t for t in results if t.get("completed") == completed]
    if assignee_name:
        results = [t for t in results if _match(t, "assignee_name", assignee_name)]
    return results


# ---------------------------------------------------------------------------
# Write: Task Create
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_task_create(
    project_gid: str = Field(description="GID of the project to add the task to"),
    section_gid: str = Field(description="GID of the section within the project"),
    name: str = Field(description="Task name"),
    notes: Optional[str] = Field(default="", description="Task description / notes"),
    assignee_name: Optional[str] = Field(default=None, description="Name of the assignee"),
    due_date: Optional[str] = Field(default=None, description="Due date in YYYY-MM-DD format"),
    priority: Optional[str] = Field(default="medium", description="Priority: high | medium | low"),
    tags_csv: Optional[str] = Field(default=None, description="Comma-separated tag names to apply to the task"),
) -> dict:
    """Create a new task in the specified project and section. Returns the created task."""
    import uuid
    from datetime import datetime

    # Resolve project name
    project_name = ""
    for proj in _db["projects"]:
        if proj["gid"] == project_gid:
            project_name = proj["name"]
            break

    # Resolve section name
    section_name = ""
    for sec in _db["sections"]:
        if sec["gid"] == section_gid:
            section_name = sec["name"]
            break

    # Resolve assignee gid
    assignee_gid = None
    if assignee_name:
        for user in _db["users"]:
            if assignee_name.lower() in user["name"].lower():
                assignee_gid = user["gid"]
                assignee_name = user["name"]
                break

    # Parse tags
    tags = []
    if tags_csv:
        tags = [t.strip() for t in tags_csv.split(",") if t.strip()]

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_task = {
        "gid": f"task-{uuid.uuid4().hex[:8]}",
        "name": name,
        "notes": notes or "",
        "project_gid": project_gid,
        "project_name": project_name,
        "section_gid": section_gid,
        "section_name": section_name,
        "assignee_gid": assignee_gid,
        "assignee_name": assignee_name,
        "due_date": due_date,
        "completed": False,
        "completed_at": None,
        "created_at": now,
        "modified_at": now,
        "tags": tags,
        "priority": priority or "medium",
        "resource_type": "task",
        "liked": False,
        "num_likes": 0,
        "parent_gid": None,
    }
    _db["tasks"].append(new_task)
    return new_task


# ---------------------------------------------------------------------------
# Write: Task Update
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_task_update(
    gid: str = Field(description="GID of the task to update"),
    name: Optional[str] = Field(default=None, description="New task name"),
    notes: Optional[str] = Field(default=None, description="New task notes / description"),
    completed: Optional[bool] = Field(default=None, description="Mark as completed (true) or incomplete (false)"),
    due_date: Optional[str] = Field(default=None, description="New due date in YYYY-MM-DD format"),
    priority: Optional[str] = Field(default=None, description="New priority: high | medium | low"),
    assignee_name: Optional[str] = Field(default=None, description="New assignee name"),
) -> dict:
    """Update fields on an existing task. Only provided fields are changed. Returns updated task."""
    from datetime import datetime

    for task in _db["tasks"]:
        if task["gid"] == gid:
            if name is not None:
                task["name"] = name
            if notes is not None:
                task["notes"] = notes
            if completed is not None:
                task["completed"] = completed
                if completed:
                    task["completed_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    task["completed_at"] = None
            if due_date is not None:
                task["due_date"] = due_date
            if priority is not None:
                task["priority"] = priority
            if assignee_name is not None:
                task["assignee_name"] = assignee_name
                for user in _db["users"]:
                    if assignee_name.lower() in user["name"].lower():
                        task["assignee_gid"] = user["gid"]
                        task["assignee_name"] = user["name"]
                        break
            task["modified_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            return task

    return {"error": f"Task with gid '{gid}' not found."}


# ---------------------------------------------------------------------------
# Write: Story Create (comment)
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_story_create(
    task_gid: str = Field(description="GID of the task to comment on"),
    text: str = Field(description="Comment text to add to the task"),
) -> dict:
    """Add a comment (story) to a task. Returns the created story."""
    import uuid
    from datetime import datetime

    task_name = ""
    for task in _db["tasks"]:
        if task["gid"] == task_gid:
            task_name = task["name"]
            break

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_story = {
        "gid": f"story-{uuid.uuid4().hex[:8]}",
        "resource_type": "story",
        "type": "comment",
        "text": text,
        "task_gid": task_gid,
        "task_name": task_name,
        "created_at": now,
        "created_by_gid": None,
        "created_by_name": "AI Assistant",
        "is_pinned": False,
    }
    _db["stories"].append(new_story)
    return new_story


# ---------------------------------------------------------------------------
# Write: Add Tag to Task
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_task_add_tag(
    task_gid: str = Field(description="GID of the task to tag"),
    tag_name: str = Field(description="Name of the tag to add"),
) -> dict:
    """Add a tag to a task's tags array. Returns the updated task."""
    from datetime import datetime

    for task in _db["tasks"]:
        if task["gid"] == task_gid:
            existing = [t.lower() for t in task.get("tags", [])]
            if tag_name.lower() not in existing:
                task.setdefault("tags", []).append(tag_name)
                task["modified_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            return task

    return {"error": f"Task with gid '{task_gid}' not found."}


# ---------------------------------------------------------------------------
# Write: Project Status Update
# ---------------------------------------------------------------------------


@mcp.tool()
def asana_project_status_update(
    project_gid: str = Field(description="GID of the project to update"),
    status: str = Field(description="New project status: active | archived | on_hold"),
    text: Optional[str] = Field(default=None, description="Status update text / notes to append to project notes"),
) -> dict:
    """Update a project's status and optionally append a status note. Returns the updated project."""
    from datetime import datetime

    for project in _db["projects"]:
        if project["gid"] == project_gid:
            project["status"] = status
            if text:
                existing_notes = project.get("notes", "")
                timestamp = datetime.utcnow().strftime("%Y-%m-%d")
                project["notes"] = f"{existing_notes}\n\n[{timestamp}] {text}".strip()
            project["modified_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            return project

    return {"error": f"Project with gid '{project_gid}' not found."}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
