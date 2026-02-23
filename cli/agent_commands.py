from __future__ import annotations

import json
import re
from typing import Any, Optional, TypedDict, List, Dict, Tuple, Annotated

from dotenv import load_dotenv
from domain.enums import Priority

from langchain_groq import ChatGroq
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages


# ============================================================
# State
# ============================================================
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: int


# ============================================================
# Prompt (keep it short + strict)
# ============================================================
SYSTEM_PROMPT = """
You are Tree, the TaskMgr Agent for a CLI task manager.

Rules:
- You MUST use tools to read or modify any data.
- Never invent tasks/notes. Never guess IDs.
- If user asks to list/show tasks -> call list_tasks immediately.
- If user asks about notes for a task:
  - If task ID is provided -> list_notes(task_id)
  - If only a title/keyword is provided -> find_tasks(query) first, then list_notes(task_id)
- If a tool returns ok=false -> explain the error and STOP.
- Keep responses short. No tutorials. No code samples. No JSON dumps.
""".strip()


# ============================================================
# Helpers
# ============================================================
def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None or isinstance(x, bool):
            return None
        if isinstance(x, int):
            return x
        s = str(x).strip()
        if not s:
            return None
        return int(s)
    except Exception:
        return None


def _extract_first_int(text: str) -> Optional[int]:
    m = re.search(r"\b(\d+)\b", text or "")
    return _safe_int(m.group(1)) if m else None


def _format_tasks(tasks: List[dict], limit: int = 30) -> str:
    if not tasks:
        return "No tasks."
    lines = ["ID | STATUS | PRIORITY | TITLE", "-" * 55]
    for t in tasks[:limit]:
        tid = t.get("id", "")
        st = t.get("status", "")
        pr = t.get("priority", "")
        title = t.get("title", "")
        lines.append(f"{tid} | {st} | {pr} | {title}")
    if len(tasks) > limit:
        lines.append(f"...and {len(tasks) - limit} more")
    return "\n".join(lines)


def _format_notes(notes: List[dict], limit: int = 30) -> str:
    if not notes:
        return "No notes for this task."
    lines = ["NOTE_ID | TASK_ID | CONTENT", "-" * 55]
    for n in notes[:limit]:
        nid = n.get("id", "")
        tid = n.get("task_id", "")
        content = n.get("content", "")
        lines.append(f"{nid} | {tid} | {content}")
    if len(notes) > limit:
        lines.append(f"...and {len(notes) - limit} more")
    return "\n".join(lines)


def _parse_tool_payload(content: Any) -> Optional[dict]:
    """
    ToolMessage.content is often JSON-string; sometimes dict.
    """
    if content is None:
        return None
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        s = content.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except Exception:
            return None
    return None


def _extract_last_tool_payload(messages: List[BaseMessage]) -> Optional[dict]:
    for m in reversed(messages):
        if isinstance(m, ToolMessage):
            payload = _parse_tool_payload(m.content)
            if isinstance(payload, dict):
                return payload
    return None


def _render_from_payload(payload: dict) -> Optional[str]:
    """
    Convert tool results to deterministic CLI output.
    """
    if payload.get("ok") is False:
        return f"[ERROR] {payload.get('error', 'Unknown error')}"

    if "tasks" in payload and isinstance(payload["tasks"], list):
        return _format_tasks(payload["tasks"])

    if "matches" in payload and isinstance(payload["matches"], list):
        # For find_tasks, show short table and ask user to pick if multiple.
        matches = payload["matches"]
        if not matches:
            return "No matching tasks."
        if len(matches) == 1:
            t = matches[0]
            return f"Found 1 task: {t.get('id')} | {t.get('status')} | {t.get('priority')} | {t.get('title')}"
        lines = ["ID | STATUS | PRIORITY | TITLE", "-" * 55]
        for t in matches[:20]:
            lines.append(f"{t.get('id')} | {t.get('status')} | {t.get('priority')} | {t.get('title')}")
        lines.append("Multiple matches. Reply with the ID you mean.")
        return "\n".join(lines)

    if "notes" in payload and isinstance(payload["notes"], list):
        return _format_notes(payload["notes"])

    if "deleted" in payload:
        return f"[OK] Deleted {payload['deleted']} item(s)."

    if "deleted_task_id" in payload:
        return f"[OK] Deleted task {payload['deleted_task_id']}."

    if "deleted_note_id" in payload:
        return f"[OK] Deleted note {payload['deleted_note_id']}."

    if "task" in payload and isinstance(payload["task"], dict):
        t = payload["task"]
        # keep it short and consistent
        return f"[OK] Task saved: {t.get('id')} | {t.get('status')} | {t.get('priority')} | {t.get('title')}"

    if "note" in payload and isinstance(payload["note"], dict):
        n = payload["note"]
        return f"[OK] Note added: {n.get('id')} (task {n.get('task_id')})"

    if "message" in payload:
        return str(payload["message"])

    return None


# ============================================================
# Tools (bind your services)
# ============================================================
def build_tools(task_service, note_service, auth_service, session_ctx):
    def _auth_error() -> Optional[str]:
        if not session_ctx.is_authenticated:
            return "Not authenticated. Please login first."
        return None

    @tool("list_tasks")
    def list_tasks(priority: Optional[str] = None, status: Optional[str] = None) -> dict:
        """List tasks for the current user. Optional filters: priority, status."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        try:
            tasks = task_service.list_tasks()  # list[dict]
        except Exception as e:
            return {"ok": False, "error": str(e)}

        if priority:
            p = priority.upper().strip()
            tasks = [t for t in tasks if str(t.get("priority", "")).upper() == p]

        if status:
            s = status.upper().strip()
            tasks = [t for t in tasks if str(t.get("status", "")).upper() == s]

        def sort_key(t: dict):
            st = str(t.get("status", "")).upper()
            pr = str(t.get("priority", "MEDIUM")).upper()
            st_rank = 0 if st == "PENDING" else 1
            pr_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(pr, 1)
            return (st_rank, pr_rank, t.get("id", 0))

        tasks = sorted(tasks, key=sort_key)
        return {"ok": True, "tasks": tasks}

    @tool("find_tasks")
    def find_tasks(query: str) -> dict:
        """Searches for tasks belonging to the current user where the task title contains the provided keyword.
The search must be case-insensitive and return all matching tasks in a structured response format.
This function does not modify data. It only retrieves filtered results."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        q = (query or "").strip().lower()
        if not q:
            return {"ok": False, "error": "Empty query."}

        try:
            tasks = task_service.list_tasks()
        except Exception as e:
            return {"ok": False, "error": str(e)}

        matches = [t for t in tasks if q in str(t.get("title", "")).lower()]
        return {"ok": True, "matches": matches}

    @tool("add_task")
    def add_task(title: str, description: Optional[str] = None, priority: str = "MEDIUM") -> dict:
        """Creates a new task for the current authenticated user with the specified title.
Optionally accepts a description and priority level.
If no priority is provided, the default value is "MEDIUM".
The task must be initialized with a default status of "PENDING" and assigned a unique integer ID."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        pr = (priority or "MEDIUM").upper().strip()
        try:
            pr_enum = Priority(pr)
        except Exception:
            pr_enum = Priority.MEDIUM

        try:
            task = task_service.create_task(
                title=(title or "").strip(),
                description=description,
                priority=pr_enum,
                category=None,
                due_date=None,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "task": task}

    @tool("mark_task_done")
    def mark_task_done(task_id: Any) -> dict:
        """Marks an existing task as completed using its integer task_id.
The function must verify that the task exists and belongs to the current user before updating its status to "COMPLETED"."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        tid = _safe_int(task_id)
        if tid is None:
            return {"ok": False, "error": "task_id must be an integer."}

        try:
            task = task_service.mark_done(tid)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "task": task}

    @tool("delete_task")
    def delete_task(task_id: Any) -> dict:
        """Deletes a task permanently using its integer task_id.
The function must ensure the task exists and belongs to the current user before removal."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        tid = _safe_int(task_id)
        if tid is None:
            return {"ok": False, "error": "task_id must be an integer."}

        try:
            task_service.delete_task(tid)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "deleted_task_id": tid}

    @tool("logout")
    def logout() -> dict:
        """End the current user session and clear any active authentication state."""
        if not session_ctx.is_authenticated:
            return {"ok": True, "message": "Already logged out."}
        try:
            auth_service.logout()
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "message": "Logged out."}

    @tool("list_notes")
    def list_notes(task_id: Any) -> dict:
        """Retrieve and return all notes associated with the specified task ID for the current user."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        tid = _safe_int(task_id)
        if tid is None:
            print(tid)
            print(type(tid))
            return {"ok": False, "error": "task_id must be an integer."}

        try:
            notes = note_service.list_notes(tid)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "notes": notes}

    @tool("add_note")
    def add_note(task_id: Any, content: str) -> dict:
        """Add a new note with the given content to the specified task for the current user."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        tid = _safe_int(task_id)
        if tid is None:
            print(tid)
            print(type(tid))

            return {"ok": False, "error": "task_id must be an integer."}

        if not (content or "").strip():
            return {"ok": False, "error": "content is required."}

        try:
            note = note_service.add_note(tid, content.strip())
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "note": note}

    @tool("delete_note")
    def delete_note(note_id: Any) -> dict:
        """Delete the note identified by the given note ID for the current user."""
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        nid = _safe_int(note_id)
        if nid is None:
            return {"ok": False, "error": "note_id must be an integer."}

        try:
            note_service.delete_note(nid)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "deleted_note_id": nid}

    @tool("delete_completed_tasks")
    def delete_completed_tasks() -> dict:
        "Delete all tasks marked as completed for the current user."
        err = _auth_error()
        if err:
            return {"ok": False, "error": err}

        try:
            tasks = task_service.list_tasks()
        except Exception as e:
            return {"ok": False, "error": str(e)}

        completed = [t for t in tasks if str(t.get("status", "")).upper() == "COMPLETED"]
        if not completed:
            return {"ok": True, "deleted": 0}

        deleted = 0
        for t in completed:
            tid = _safe_int(t.get("id"))
            if tid is None:
                continue
            try:
                task_service.delete_task(tid)
                deleted += 1
            except Exception:
                continue

        return {"ok": True, "deleted": deleted}

    return [
        list_tasks,
        find_tasks,
        add_task,
        mark_task_done,
        list_notes,
        add_note,
        delete_note,
        delete_task,
        logout,
        delete_completed_tasks,
    ]


# ============================================================
# Graph: tool-calling agent <-> tools until no more tool calls
# Then we stop and render tool output ourselves (no final LLM).
# ============================================================
def build_graph(llm_tools, tools):
    # IMPORTANT: handle_tool_errors=True prevents crashes and converts tool errors into ToolMessages.
    tool_node = ToolNode(tools, handle_tool_errors=True)

    def agent_node(state: AgentState) -> AgentState:
        resp = llm_tools.invoke(state["messages"])
        return {"messages": [resp], "user_id": state["user_id"]}

    def route(state: AgentState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            if last.tool_calls:
                return "tools"
        return END

    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)

    g.set_entry_point("agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")

    return g.compile()


# ============================================================
# Fast-path (deterministic shortcuts, no LLM)
# ============================================================
def _fast_path(
    user_text: str,
    task_service,
    note_service,
    graph_cache: dict,
    user_key: str,
) -> Optional[str]:
    t = _normalize(user_text)

    # ---- pending confirmation: delete_completed_tasks ----
    pending: Dict[str, dict] = graph_cache.setdefault("pending", {})
    pend = pending.get(user_key)

    if pend and pend.get("type") == "delete_completed_tasks_confirm":
        if t in {"yes", "y", "ok", "okay", "confirm", "do it"}:
            pending.pop(user_key, None)
            # run the real operation
            deleted = 0
            tasks = task_service.list_tasks()
            completed = [x for x in tasks if str(x.get("status", "")).upper() == "COMPLETED"]
            for x in completed:
                tid = _safe_int(x.get("id"))
                if tid is None:
                    continue
                try:
                    task_service.delete_task(tid)
                    deleted += 1
                except Exception:
                    continue
            return f"[OK] Deleted {deleted} completed task(s)."
        if t in {"no", "n", "cancel", "stop"}:
            pending.pop(user_key, None)
            return "[OK] Cancelled."
        return "Reply with yes/no."

    # ---- list tasks ----
    if t in {"show tasks", "list tasks", "show all tasks", "tasks", "show me all the tasks"}:
        tasks = task_service.list_tasks()
        return _format_tasks(tasks)

    # ---- most important ----
    if "most important" in t or "important tasks" in t:
        tasks = task_service.list_tasks()
        tasks = [
            x
            for x in tasks
            if str(x.get("priority", "")).upper() == "HIGH"
            and str(x.get("status", "")).upper() == "PENDING"
        ]
        return _format_tasks(tasks)

    # ---- list notes by explicit id ----
    if any(k in t for k in ["show notes", "list notes", "what are the notes", "notes for task"]):
        task_id = _extract_first_int(t)
        if task_id is None:
            return "Which task? Give the task ID (example: /show notes 2)."
        notes = note_service.list_notes(task_id)
        return _format_notes(notes)

    # ---- delete completed tasks -> confirmation ----
    if any(k in t for k in ["delete completed tasks", "remove completed tasks", "delete all completed tasks"]):
        pending[user_key] = {"type": "delete_completed_tasks_confirm"}
        return "This will permanently delete all COMPLETED tasks. Continue? (yes/no)"

    return None


# ============================================================
# Entry point for / commands
# ============================================================
def handle_slash(
    raw_line: str,
    *,
    task_service,
    note_service,
    auth_service,
    session_ctx,
    graph_cache,
) -> str:
    load_dotenv()

    if not raw_line.startswith("/"):
        return ""

    user_text = raw_line[1:].strip()
    if not user_text:
        return "Type something after /"

    if not session_ctx.is_authenticated:
        return "Not authenticated. Login first."

    user_key = f"user:{getattr(session_ctx.user, 'id', 'anon')}"

    # ---- deterministic fast path (no LLM) ----
    try:
        fp = _fast_path(user_text, task_service, note_service, graph_cache, user_key)
        if fp is not None:
            return fp
    except Exception:
        # If fast path fails, fall back to LLM.
        pass

    # ---- tools + graph build/cache ----
    tools = build_tools(
        task_service=task_service,
        note_service=note_service,
        auth_service=auth_service,
        session_ctx=session_ctx,
    )

    tool_names: Tuple[str, ...] = tuple(sorted(t.name for t in tools))
    if graph_cache.get("tool_names") != tool_names or "graph" not in graph_cache:
        graph_cache["tool_names"] = tool_names

        llm_tools = ChatGroq(
            model=graph_cache.get("model", "llama-3.3-70b-versatile"),
            temperature=0.2,
        ).bind_tools(tools)

        graph_cache["graph"] = build_graph(llm_tools=llm_tools, tools=tools)

    graph = graph_cache["graph"]

    # ---- history ----
    histories: Dict[str, List[BaseMessage]] = graph_cache.setdefault("histories", {})
    history = histories.get(user_key)
    if not history:
        history = [SystemMessage(content=SYSTEM_PROMPT)]
        histories[user_key] = history

    history.append(HumanMessage(content=user_text))

    MAX_MSGS = 25
    if len(history) > MAX_MSGS:
        history[:] = [history[0]] + history[-(MAX_MSGS - 1) :]

    state: AgentState = {
        "messages": history,
        "user_id": int(getattr(session_ctx.user, "id", 0)),
    }

    # Higher recursion_limit is fine now because we stop when tool_calls end.
    out = graph.invoke(state, config={"recursion_limit": 50})
    histories[user_key] = out["messages"]

    # ---- deterministic rendering: prefer tool payload ----
    payload = _extract_last_tool_payload(out["messages"])
    if payload:
        rendered = _render_from_payload(payload)
        if rendered:
            return rendered

    # If no tool payload, fall back to last AI message content (still kept strict by SYSTEM_PROMPT).
    last = out["messages"][-1]
    if isinstance(last, AIMessage) and last.content:
        # guardrail: avoid JSON dumps
        text = str(last.content).strip()
        if text.startswith("{") or text.startswith("["):
            return "Done."
        return text

    return "Done."