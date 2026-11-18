import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from backend.app.models.chat import ChatRequest, ChatResponse, ToolExecutionLog
from backend.app.graphs.copilot_graph import copilot_graph
from backend.app.services.session_store import session_store

router = APIRouter(prefix="/chat", tags=["Chat Co-Pilot"])

@router.post("", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Bucle interactivo del Co-Pilot financiero (Respuesta JSON estandar):
    Recibe la consulta del usuario, inyecta el estado resumido del dashboard,
    el plan y las directrices empaticas, y ejecuta el ciclo ReAct con herramientas MCP.
    """
    case_id = request.case_id
    session_id = request.session_id or "default"
    thread_id = f"{case_id}_{session_id}"

    session = session_store.get_or_create(session_id, case_id)
    session.pending_charts.clear()
    session.last_change_applied = None

    # Configuracion de ejecucion con thread_id para checkpointer de memoria
    run_config = {
        "configurable": {
            "thread_id": thread_id,
            "session_id": session_id,
            "case_id": case_id
        }
    }

    user_msg = HumanMessage(content=request.message)
    messages_to_send = []

    try:
        current_state = copilot_graph.get_state(run_config)
    except Exception:
        current_state = None

    if (not current_state or not current_state.values.get("messages")) and request.history:
        for h in request.history:
            role = h.get("role")
            content = h.get("content", "")
            if not content:
                continue
            if role == "user":
                messages_to_send.append(HumanMessage(content=content))
            elif role == "assistant":
                messages_to_send.append(AIMessage(content=content))

    messages_to_send.append(user_msg)
    input_state = {
        "case_id": case_id,
        "session_id": session_id,
        "messages": messages_to_send
    }

    try:
        # Ejecutar LangGraph ciclico de forma asincrona
        result = await copilot_graph.ainvoke(input_state, config=run_config)
        messages = result.get("messages", [])

        # Extraer respuesta y ejecucion de herramientas
        reply_content = ""
        tool_logs: list[ToolExecutionLog] = []

        for m in messages:
            if isinstance(m, ToolMessage):
                t_name = getattr(m, "name", "tool")
                audit_match = next(
                    (a for a in reversed(session.recent_tool_audits) if a.get("tool") == t_name),
                    None
                )
                t_args = audit_match.get("args", {}) if audit_match else {}
                t_mod = audit_match.get("modified", False) if audit_match else False
                t_diff = audit_match.get("diff", "") if audit_match else ""
                tool_logs.append(
                    ToolExecutionLog(
                        tool=t_name,
                        args=t_args,
                        result=m.content,
                        modified=t_mod,
                        change_summary=t_diff
                    )
                )
            elif isinstance(m, AIMessage):
                if m.content:
                    reply_content = str(m.content)

        if not reply_content:
            raise HTTPException(
                status_code=502,
                detail="El modelo de chat finalizo su turno sin emitir una respuesta de texto."
            )

        # Capturar cualquier grafico pendiente generado por la herramienta display_chart
        chart_to_render = session.pending_charts[-1] if session.pending_charts else None
        has_changes = bool(session.last_change_applied) or any(t.modified for t in tool_logs)
        applied_desc = session.last_change_applied if session.last_change_applied else (
            ", ".join([t.change_summary for t in tool_logs if t.modified and t.change_summary])
        )

        return ChatResponse(
            reply=reply_content,
            tools_executed=tool_logs,
            tasks=session.tasks,
            dashboard=session.dashboard,
            chart_to_render=chart_to_render,
            changes_applied=has_changes,
            applied_summary=applied_desc if has_changes else None
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Fallo en la comunicacion con el modelo del Co-Pilot: {str(e)}"
        )

@router.post("/stream")
async def send_chat_message_stream(request: ChatRequest):
    """
    Bucle interactivo con Server-Sent Events (SSE) en tiempo real:
    Emite eventos on_tool_start, on_tool_end, tokens de texto y el estado mutado
    de la interfaz para que el frontend pinte los cambios en vivo.
    """
    case_id = request.case_id
    session_id = request.session_id or "default"
    thread_id = f"{case_id}_{session_id}"

    session = session_store.get_or_create(session_id, case_id)
    session.pending_charts.clear()
    session.last_change_applied = None

    # Configuracion de ejecucion con thread_id para checkpointer de memoria
    run_config = {
        "configurable": {
            "thread_id": thread_id,
            "session_id": session_id,
            "case_id": case_id
        }
    }

    user_msg = HumanMessage(content=request.message)
    messages_to_send = []

    try:
        current_state = copilot_graph.get_state(run_config)
    except Exception:
        current_state = None

    if (not current_state or not current_state.values.get("messages")) and request.history:
        for h in request.history:
            role = h.get("role")
            content = h.get("content", "")
            if not content:
                continue
            if role == "user":
                messages_to_send.append(HumanMessage(content=content))
            elif role == "assistant":
                messages_to_send.append(AIMessage(content=content))

    messages_to_send.append(user_msg)
    input_state = {
        "case_id": case_id,
        "session_id": session_id,
        "messages": messages_to_send
    }

    async def event_generator():
        try:
            full_reply_chunks = []
            async for event in copilot_graph.astream_events(input_state, config=run_config, version="v2"):
                kind = event["event"]

                # Notificar a la UI el inicio de ejecucion de una herramienta MCP
                if kind == "on_tool_start":
                    input_data = event.get("data", {}).get("input")
                    if not isinstance(input_data, (dict, list, str, int, float, bool)) and input_data is not None:
                        input_data = str(input_data)
                    yield ServerSentEvent(
                        data=json.dumps({
                            "type": "tool_start",
                            "tool": event.get("name"),
                            "input": input_data
                        }, ensure_ascii=False, default=str),
                        event="tool_start"
                    )

                # Notificar a la UI el fin de ejecucion de una herramienta MCP
                elif kind == "on_tool_end":
                    output_data = event.get("data", {}).get("output")
                    if hasattr(output_data, "content"):
                        output_str = str(output_data.content)
                    elif isinstance(output_data, (dict, list, str, int, float, bool)) or output_data is None:
                        output_str = output_data
                    else:
                        output_str = str(output_data)

                    tool_n = event.get("name")
                    audit_match = next(
                        (a for a in reversed(session.recent_tool_audits) if a.get("tool") == tool_n),
                        None
                    )
                    t_mod = audit_match.get("modified", False) if audit_match else False
                    t_diff = audit_match.get("diff", "") if audit_match else ""

                    yield ServerSentEvent(
                        data=json.dumps({
                            "type": "tool_end",
                            "tool": tool_n,
                            "output": output_str,
                            "modified": t_mod,
                            "diff": t_diff
                        }, ensure_ascii=False, default=str),
                        event="tool_end"
                    )

                # Emitir token de texto del modelo en streaming
                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        if isinstance(chunk.content, str):
                            text_piece = chunk.content
                        elif isinstance(chunk.content, list):
                            text_piece = "".join(
                                item.get("text", "") if isinstance(item, dict) else str(item)
                                for item in chunk.content
                            )
                        else:
                            text_piece = str(chunk.content)

                        if text_piece:
                            full_reply_chunks.append(text_piece)
                            yield ServerSentEvent(
                                data=json.dumps({
                                    "type": "token",
                                    "content": text_piece,
                                    "delta": text_piece
                                }, ensure_ascii=False, default=str),
                                event="token"
                            )

            # Emitir el estado actualizado final de la UI (tareas, dashboard, graficos)
            chart_to_render = session.pending_charts[-1] if session.pending_charts else None
            has_changes = bool(session.last_change_applied)
            yield ServerSentEvent(
                data=json.dumps({
                    "type": "state",
                    "tasks": [t.model_dump() for t in session.tasks],
                    "dashboard": session.dashboard.model_dump() if session.dashboard else None,
                    "chart_to_render": chart_to_render,
                    "full_reply": "".join(full_reply_chunks),
                    "changes_applied": has_changes,
                    "applied_summary": session.last_change_applied
                }, ensure_ascii=False, default=str),
                event="state"
            )

            # Fin del stream
            yield ServerSentEvent(
                data=json.dumps({"type": "done"}, ensure_ascii=False, default=str),
                event="done"
            )

        except Exception as e:
            yield ServerSentEvent(
                data=json.dumps({
                    "type": "error",
                    "detail": str(e)
                }, ensure_ascii=False, default=str),
                event="error"
            )

    return EventSourceResponse(event_generator())

@router.get("/audit-logs/{case_id}")
async def get_case_audit_logs(case_id: str, limit: int = 30):
    """Devuelve los registros de auditoria recientes de prompts, respuestas y llamadas MCP."""
    from backend.app.services.audit_logger import get_recent_logs
    logs = get_recent_logs(case_id=case_id, limit=limit)
    return {"case_id": case_id, "logs": logs}
