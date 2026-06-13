"""
Command Center API.

POST /api/command-center/query  → SSE stream of the AI's answer (admin only).
GET  /api/command-center/health → cheap status/config probe (admin only).

Auth: reuses the project's Token/Session auth. Restricted to staff/superusers
(the Command Center is a super-admin surface).
"""
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .loop import stream_answer


def _trim_history(history, max_turns=16):
    """
    Keep the most recent turns without ever splitting an assistant message that
    carries tool_calls from its following tool-result messages (that would make
    OpenAI 400). We trim from the front but snap the cut to a safe boundary.
    """
    history = [m for m in history if isinstance(m, dict)]
    if len(history) <= max_turns:
        return history
    cut = len(history) - max_turns
    # Never start the window on a 'tool' message (its assistant parent would be gone),
    # and never orphan an assistant-with-tool_calls. Walk the cut forward to a 'user'
    # or plain 'assistant' boundary.
    while cut < len(history):
        m = history[cut]
        role = m.get("role")
        if role == "tool":
            cut += 1
            continue
        if role == "assistant" and m.get("tool_calls"):
            cut += 1
            continue
        break
    return history[cut:]


@api_view(["POST"])
@permission_classes([IsAdminUser])
def command_center_query(request):
    data = request.data or {}
    # Accept either a single {"question": "..."} or {"messages": [...]} history.
    history = data.get("messages")
    if not history:
        question = (data.get("question") or "").strip()
        history = [{"role": "user", "content": question}] if question else []

    history = _trim_history(history)
    decisions = data.get("decisions") or []
    auto_run = data.get("auto_run")
    auto_run = True if auto_run is None else bool(auto_run)

    response = StreamingHttpResponse(
        stream_answer(history, request.user, decisions=decisions, auto_run=auto_run),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # disable proxy buffering (nginx)
    return response


@api_view(["GET"])
@permission_classes([IsAdminUser])
def command_center_health(request):
    return Response({
        "configured": bool(settings.OPENAI_API_KEY),
        "model": settings.OPENAI_COMMAND_MODEL,
        "user": request.user.get_username(),
    })
