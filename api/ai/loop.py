"""
Streaming agentic loop for the AI Command Center — READ + governed WRITE.

SSE events emitted:
    {"type":"status",  "message": "..."}                progress line
    {"type":"tool",    "name": "...", "phase":"running|done"}
    {"type":"token",   "text": "..."}                   a chunk of the answer
    {"type":"assistant_tool_calls", "tool_calls":[...], "tool_results":[...]}
                                                         (state for the frontend to resume)
    {"type":"confirm", "id","name","summary","args","risk"}   one per pending write
    {"type":"done"}
    {"type":"error",   "message": "..."}

Governance (one inviolable rule: the server is the ONLY thing that executes a write):
  • READ tool calls execute inline (as before).
  • SAFE write calls execute inline when auto_run is on; otherwise they wait for confirm.
  • RISKY write calls ALWAYS wait for human confirmation.
  • When anything needs confirmation the loop emits the assistant state + confirm events,
    then ends the request. The frontend approves/rejects and re-POSTs an enriched history
    (with __APPROVED__/__REJECTED__ tool markers) plus a decisions[] array; the apply pass
    below executes approved writes (perm re-check + audit) before resuming the model.
"""
import json

from .client import get_client, COMMAND_MODEL, SYSTEM_PROMPT, MAX_TOOL_ITERATIONS
from .tools import (
    TOOL_SCHEMAS, TOOL_LABELS, run_tool,
    WRITE_TOOLS, risk_of, summarize_write, run_write_tool, log_rejected,
)

APPROVED = "__APPROVED__"
REJECTED_PREFIX = "__REJECTED__"


def _sse(payload):
    return f"data: {json.dumps(payload, default=str)}\n\n"


def _rebuild_messages(history):
    """Faithfully rebuild OpenAI messages from the enriched client history."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role == "user":
            if (content or "").strip():
                messages.append({"role": "user", "content": content})
        elif role == "assistant":
            tcs = m.get("tool_calls")
            if tcs:
                messages.append({"role": "assistant", "content": content, "tool_calls": tcs})
            elif (content or "").strip():
                messages.append({"role": "assistant", "content": content})
        elif role == "tool" and m.get("tool_call_id"):
            messages.append({
                "role": "tool",
                "tool_call_id": m["tool_call_id"],
                "content": content if content is not None else "",
            })
    return messages


def _find_tool_call(messages, tool_call_id):
    """Return (name, args_dict) for a tool_call_id from the assistant messages."""
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            if tc.get("id") == tool_call_id:
                fn = tc.get("function", {})
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                return fn.get("name"), args
    return None, {}


def _ensure_tool_results(messages):
    """Guarantee every assistant tool_call has a matching tool message (no OpenAI 400)."""
    declared = []
    for m in messages:
        if m.get("role") == "assistant":
            for tc in (m.get("tool_calls") or []):
                declared.append(tc.get("id"))
    provided = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
    for tcid in declared:
        if tcid not in provided:
            messages.append({
                "role": "tool",
                "tool_call_id": tcid,
                "content": json.dumps({"error": "No result recorded for this action."}),
            })


def _apply_decisions(messages, decisions, user):
    """
    Resume pass: turn __APPROVED__ / __REJECTED__ tool markers into real results.
    Yields SSE strings for executed-write progress. Mutates `messages` in place.
    """
    dmap = {d.get("id"): d for d in (decisions or []) if isinstance(d, dict)}
    for m in messages:
        if m.get("role") != "tool":
            continue
        content = m.get("content")
        tcid = m.get("tool_call_id")
        if content == APPROVED:
            name, args = _find_tool_call(messages, tcid)
            dec = dmap.get(tcid)
            if name and name in WRITE_TOOLS and dec and dec.get("approved"):
                label = TOOL_LABELS.get(name, f"Running {name}")
                yield _sse({"type": "status", "message": label})
                yield _sse({"type": "tool", "name": name, "phase": "running"})
                result = run_write_tool(name, args, user, tcid)
                yield _sse({"type": "tool", "name": name, "phase": "done"})
                m["content"] = json.dumps(result, default=str)
            else:
                m["content"] = json.dumps({"error": "Action was not approved or is unknown."})
        elif isinstance(content, str) and content.startswith(REJECTED_PREFIX):
            name, args = _find_tool_call(messages, tcid)
            log_rejected(user, name or "?", args, tcid)
            m["content"] = json.dumps({"declined": True, "note": "The operator declined this action."})


def stream_answer(history, user, decisions=None, auto_run=True):
    """Generator yielding SSE strings. `user` is the authenticated admin (request.user)."""
    try:
        client = get_client()
    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})
        yield _sse({"type": "done"})
        return

    messages = _rebuild_messages(history)
    if len(messages) == 1:
        yield _sse({"type": "error", "message": "No question provided."})
        yield _sse({"type": "done"})
        return

    try:
        # Resume: execute any approved writes / normalize rejects before talking to the model.
        if any(m.get("role") == "tool" and (
            m.get("content") == APPROVED or str(m.get("content", "")).startswith(REJECTED_PREFIX)
        ) for m in messages):
            for ev in _apply_decisions(messages, decisions, user):
                yield ev
        _ensure_tool_results(messages)

        for _ in range(MAX_TOOL_ITERATIONS):
            stream = client.chat.completions.create(
                model=COMMAND_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
                stream=True,
            )

            content_parts = []
            tool_calls = {}
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    content_parts.append(delta.content)
                    yield _sse({"type": "token", "text": delta.content})
                if delta and delta.tool_calls:
                    for tc in delta.tool_calls:
                        slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                        if tc.id:
                            slot["id"] = tc.id
                        if tc.function and tc.function.name:
                            slot["name"] = tc.function.name
                        if tc.function and tc.function.arguments:
                            slot["args"] += tc.function.arguments

            # No tool calls → final answer delivered.
            if not tool_calls:
                yield _sse({"type": "done"})
                return

            ordered = [tool_calls[i] for i in sorted(tool_calls.keys())]
            assistant_tool_calls = [
                {
                    "id": c["id"] or f"call_{i}",
                    "type": "function",
                    "function": {"name": c["name"], "arguments": c["args"] or "{}"},
                }
                for i, c in enumerate(ordered)
            ]
            messages.append({
                "role": "assistant",
                "content": "".join(content_parts) or None,
                "tool_calls": assistant_tool_calls,
            })

            auto_results = []       # tool results we executed inline this turn
            pending = []            # (id, name, args, risk) needing confirmation

            for i, c in enumerate(ordered):
                name = c["name"]
                tcid = c["id"] or f"call_{i}"
                try:
                    args = json.loads(c["args"]) if c["args"] else {}
                except json.JSONDecodeError:
                    args = {}

                is_write = name in WRITE_TOOLS
                risky = bool(is_write and risk_of(name, args))
                run_now = (not is_write) or (is_write and not risky and auto_run)

                if run_now:
                    yield _sse({"type": "status", "message": TOOL_LABELS.get(name, f"Running {name}")})
                    yield _sse({"type": "tool", "name": name, "phase": "running"})
                    result = run_write_tool(name, args, user, tcid) if is_write else run_tool(name, args)
                    yield _sse({"type": "tool", "name": name, "phase": "done"})
                    tool_msg = {"role": "tool", "tool_call_id": tcid, "content": json.dumps(result, default=str)}
                    messages.append(tool_msg)
                    auto_results.append({"tool_call_id": tcid, "content": tool_msg["content"]})
                else:
                    pending.append((tcid, name, args, risk_of(name, args) or "confirm"))

            # Anything needs confirmation → hand state to the client and pause.
            if pending:
                yield _sse({
                    "type": "assistant_tool_calls",
                    "tool_calls": assistant_tool_calls,
                    "tool_results": auto_results,
                })
                for tcid, name, args, risk in pending:
                    yield _sse({
                        "type": "confirm",
                        "id": tcid,
                        "name": name,
                        "summary": summarize_write(name, args),
                        "args": args,
                        "risk": risk,
                    })
                yield _sse({"type": "done"})
                return
            # else: everything ran inline → loop back for the model's next step.

        yield _sse({
            "type": "token",
            "text": "\n\n(I reached my step limit while working on that — please refine the request.)",
        })
        yield _sse({"type": "done"})
    except Exception as e:
        yield _sse({"type": "error", "message": f"AI error: {e}"})
        yield _sse({"type": "done"})
