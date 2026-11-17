import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("copilot.audit")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DIR = BASE_DIR / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
GLOBAL_AUDIT_FILE = LOGS_DIR / "copilot_audit.log"

# Buffer en memoria de las ultimas entradas de auditoria para inspeccion rapida en UI y API
_RECENT_LOGS: list[dict[str, Any]] = []
_MAX_RECENT_LOGS = 100

def _append_to_file(file_path: Path, entry_str: str) -> None:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry_str + "\n")
    except Exception as e:
        logger.error(f"Error escribiendo en log de auditoria {file_path}: {e}")

def log_prompt(session_id: str, case_id: str, user_message: str, system_prompt_snippet: str = "") -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "type": "PROMPT",
        "case_id": case_id,
        "session_id": session_id,
        "user_message": user_message,
        "system_prompt_snippet": system_prompt_snippet[:500] if system_prompt_snippet else ""
    }
    _RECENT_LOGS.append(entry)
    if len(_RECENT_LOGS) > _MAX_RECENT_LOGS:
        _RECENT_LOGS.pop(0)

    log_line = (
        f"[{ts}] [PROMPT] Case: {case_id} | Session: {session_id} | "
        f"User Message: {user_message}"
    )
    logger.info(log_line)

    case_log_file = BASE_DIR / "data" / "cases" / case_id / "copilot_audit.log"
    entry_formatted = (
        f"================================================================================\n"
        f"[{ts}] [PROMPT] Case: {case_id} | Session: {session_id}\n"
        f"User Message: {user_message}\n"
        f"System Prompt Preview: {system_prompt_snippet[:300]}...\n"
    )
    _append_to_file(GLOBAL_AUDIT_FILE, entry_formatted)
    _append_to_file(case_log_file, entry_formatted)

def log_tool_call(
    session_id: str,
    case_id: str,
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    modified: bool,
    diff: str = ""
) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "type": "MCP_TOOL_CALL",
        "case_id": case_id,
        "session_id": session_id,
        "tool": tool_name,
        "args": args,
        "result": str(result)[:500],
        "modified": modified,
        "diff": diff
    }
    _RECENT_LOGS.append(entry)
    if len(_RECENT_LOGS) > _MAX_RECENT_LOGS:
        _RECENT_LOGS.pop(0)

    mod_str = "TRUE" if modified else "FALSE"
    log_line = (
        f"[{ts}] [MCP_TOOL_CALL] Case: {case_id} | Tool: {tool_name} | "
        f"Modified: {mod_str} | Diff: {diff} | Args: {json.dumps(args, default=str)}"
    )
    logger.info(log_line)

    case_log_file = BASE_DIR / "data" / "cases" / case_id / "copilot_audit.log"
    entry_formatted = (
        f"--------------------------------------------------------------------------------\n"
        f"[{ts}] [MCP_TOOL_CALL] Tool: {tool_name} | Case: {case_id}\n"
        f"Args: {json.dumps(args, indent=2, default=str)}\n"
        f"Result: {str(result)[:300]}\n"
        f"Realmente modificado: {mod_str}\n"
        f"Detalle modificacion: {diff}\n"
    )
    _append_to_file(GLOBAL_AUDIT_FILE, entry_formatted)
    _append_to_file(case_log_file, entry_formatted)

def log_response(
    session_id: str,
    case_id: str,
    reply: str,
    tools_count: int = 0,
    changes_applied: bool = False
) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "type": "RESPONSE",
        "case_id": case_id,
        "session_id": session_id,
        "reply": reply[:500],
        "tools_count": tools_count,
        "changes_applied": changes_applied
    }
    _RECENT_LOGS.append(entry)
    if len(_RECENT_LOGS) > _MAX_RECENT_LOGS:
        _RECENT_LOGS.pop(0)

    mod_str = "YES" if changes_applied else "NO"
    log_line = (
        f"[{ts}] [RESPONSE] Case: {case_id} | Session: {session_id} | "
        f"Tools: {tools_count} | Changes Applied: {mod_str} | Reply preview: {reply[:120]}..."
    )
    logger.info(log_line)

    case_log_file = BASE_DIR / "data" / "cases" / case_id / "copilot_audit.log"
    entry_formatted = (
        f"--------------------------------------------------------------------------------\n"
        f"[{ts}] [RESPONSE] Case: {case_id} | Session: {session_id}\n"
        f"Tools executed: {tools_count} | Cambios aplicados: {mod_str}\n"
        f"Reply:\n{reply}\n"
        f"================================================================================\n"
    )
    _append_to_file(GLOBAL_AUDIT_FILE, entry_formatted)
    _append_to_file(case_log_file, entry_formatted)

def get_recent_logs(case_id: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    if case_id:
        filtered = [l for l in _RECENT_LOGS if l.get("case_id") == case_id]
        return filtered[-limit:]
    return _RECENT_LOGS[-limit:]
