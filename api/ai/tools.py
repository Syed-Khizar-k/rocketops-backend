"""
Tool registry for the AI Command Center (READ-ONLY, v1).

Each tool is a plain Python function returning JSON-serializable data, paired with
an OpenAI function schema. The model never touches the ORM directly — it can only
call these typed, bounded functions. Results are kept compact to control tokens.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.utils.text import slugify

from api.models import (
    Product, Service, Blog, BlogCategory, ContactSubmission, TeamMember, Faq, Testimonial,
)
from crm.models import Contact, Company, Deal, Activity, PipelineStage, AIActionLog
from crm.permissions import is_crm_admin


def _money(v):
    return round(float(v or 0), 2)


# ── Site tools ────────────────────────────────────────────────────────────────
def get_business_overview():
    """High-level counts across the whole RocketOps estate."""
    blogs = Blog.objects.all()
    return {
        "products": Product.objects.count(),
        "services": Service.objects.count(),
        "team_members": TeamMember.objects.count(),
        "blog_posts": {
            "total": blogs.count(),
            "published": blogs.filter(status="published").count(),
            "draft": blogs.filter(status="draft").count(),
        },
        "website_contact_submissions": ContactSubmission.objects.count(),
        "crm_contacts": Contact.objects.count(),
        "crm_open_deals": Deal.objects.filter(status="open").count(),
        "crm_open_deal_value": _money(
            Deal.objects.filter(status="open").aggregate(v=Sum("amount"))["v"]
        ),
    }


def list_products():
    """All RocketOps products with a short description."""
    return [
        {"title": p.title, "slug": p.slug, "description": (p.description or "")[:240]}
        for p in Product.objects.all()[:50]
    ]


def list_services():
    """All RocketOps services offered."""
    return [
        {"title": s.header_title, "slug": s.slug, "description": (s.description or "")[:240]}
        for s in Service.objects.all()[:50]
    ]


def list_blog_posts(status="all", limit=20):
    qs = Blog.objects.all()
    if status in ("published", "draft"):
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")[: min(int(limit or 20), 50)]
    return [
        {
            "title": b.title,
            "slug": b.slug,
            "status": b.status,
            "views": b.views,
            "published_at": b.published_at.isoformat() if b.published_at else None,
            "category": b.category.name if b.category else None,
        }
        for b in qs
    ]


def recent_contact_submissions(limit=10):
    """Latest raw website contact-form enquiries (newest first)."""
    qs = ContactSubmission.objects.order_by("-created_at")[: min(int(limit or 10), 30)]
    return [
        {
            "name": f"{s.first_name} {s.last_name}".strip(),
            "email": s.email,
            "company": s.company or "",
            "country": s.country,
            "interested_in": s.reach,
            "message": (s.details or "")[:300],
            "submitted_at": s.created_at.isoformat(),
        }
        for s in qs
    ]


# ── CRM tools ─────────────────────────────────────────────────────────────────
def crm_summary():
    """Snapshot of the CRM: contacts by lifecycle/status, deals, revenue."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    by_lifecycle = dict(
        Contact.objects.values_list("lifecycle_stage").annotate(c=Count("id"))
    )
    by_status = dict(Contact.objects.values_list("status").annotate(c=Count("id")))
    open_deals = Deal.objects.filter(status="open")
    won_month = Deal.objects.filter(status="won", closed_at__gte=month_start)

    return {
        "total_contacts": Contact.objects.count(),
        "new_leads_last_7d": Contact.objects.filter(created_at__gte=week_ago).count(),
        "contacts_by_lifecycle": by_lifecycle,
        "contacts_by_status": by_status,
        "open_deals": {
            "count": open_deals.count(),
            "value": _money(open_deals.aggregate(v=Sum("amount"))["v"]),
        },
        "won_this_month": {
            "count": won_month.count(),
            "value": _money(won_month.aggregate(v=Sum("amount"))["v"]),
        },
        "open_tasks": Activity.objects.filter(type="task", is_done=False).count(),
    }


def crm_list_leads(lifecycle=None, status=None, limit=15):
    qs = Contact.objects.select_related("company", "owner").all()
    if lifecycle:
        qs = qs.filter(lifecycle_stage=lifecycle)
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")[: min(int(limit or 15), 40)]
    return [
        {
            "name": c.full_name or c.email,
            "email": c.email,
            "company": c.company.name if c.company else "",
            "lifecycle": c.lifecycle_stage,
            "status": c.status,
            "source": c.source,
            "owner": c.owner.get_username() if c.owner else "unassigned",
            "created_at": c.created_at.isoformat(),
        }
        for c in qs
    ]


def crm_list_deals(status=None, limit=15):
    qs = Deal.objects.select_related("stage", "owner", "company", "contact").all()
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-amount")[: min(int(limit or 15), 40)]
    return [
        {
            "name": d.name,
            "amount": _money(d.amount),
            "currency": d.currency,
            "status": d.status,
            "stage": d.stage.name if d.stage else None,
            "company": d.company.name if d.company else "",
            "contact": d.contact.full_name if d.contact else "",
            "owner": d.owner.get_username() if d.owner else "unassigned",
            "expected_close": d.expected_close_date.isoformat() if d.expected_close_date else None,
        }
        for d in qs
    ]


def crm_pipeline():
    """Open-deal counts and value grouped by pipeline stage."""
    out = []
    for stage in PipelineStage.objects.all():
        agg = Deal.objects.filter(stage=stage, status="open").aggregate(
            c=Count("id"), v=Sum("amount")
        )
        out.append({"stage": stage.name, "open_deals": agg["c"] or 0, "value": _money(agg["v"])})
    return out


def crm_list_tasks(open_only=True, limit=20):
    qs = Activity.objects.filter(type="task").select_related("contact", "owner")
    if open_only:
        qs = qs.filter(is_done=False)
    qs = qs.order_by("due_date")[: min(int(limit or 20), 40)]
    return [
        {
            "subject": t.subject,
            "contact": t.contact.full_name if t.contact else "",
            "owner": t.owner.get_username() if t.owner else "unassigned",
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "done": t.is_done,
        }
        for t in qs
    ]


def crm_find_contact(query, limit=10):
    """
    Find CRM contacts by (partial) name, email, or company. Returns matches WITH
    their contact_id so they can be acted on. Use this to resolve a person mentioned
    by name before creating a task / logging activity / assigning a deal.
    """
    q = (query or "").strip()
    if not q:
        return {"matches": [], "note": "Provide a name, email, or company to search."}
    qs = Contact.objects.select_related("company", "owner").filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) |
        Q(email__icontains=q) | Q(company__name__icontains=q)
    )
    # Also match the full "first last" name against the query.
    matches = [
        {
            "contact_id": c.id,
            "name": c.full_name,
            "email": c.email,
            "company": c.company.name if c.company else "",
            "lifecycle": c.lifecycle_stage,
            "status": c.status,
            "owner": c.owner.get_username() if c.owner else "unassigned",
        }
        for c in qs.order_by("-created_at")[: min(int(limit or 10), 25)]
    ]
    # Fallback: token-based match on the combined name (handles word order / extra words).
    if not matches:
        tokens = [t for t in q.lower().split() if len(t) > 1]
        for c in Contact.objects.select_related("company", "owner").all()[:500]:
            full = c.full_name.lower()
            if tokens and any(t in full for t in tokens):
                matches.append({
                    "contact_id": c.id, "name": c.full_name, "email": c.email,
                    "company": c.company.name if c.company else "",
                    "lifecycle": c.lifecycle_stage, "status": c.status,
                    "owner": c.owner.get_username() if c.owner else "unassigned",
                })
            if len(matches) >= int(limit or 10):
                break
    return {"matches": matches, "count": len(matches)}


# ── Registry ──────────────────────────────────────────────────────────────────
TOOL_FUNCTIONS = {
    "get_business_overview": get_business_overview,
    "list_products": list_products,
    "list_services": list_services,
    "list_blog_posts": list_blog_posts,
    "recent_contact_submissions": recent_contact_submissions,
    "crm_summary": crm_summary,
    "crm_list_leads": crm_list_leads,
    "crm_list_deals": crm_list_deals,
    "crm_pipeline": crm_pipeline,
    "crm_list_tasks": crm_list_tasks,
    "crm_find_contact": crm_find_contact,
}

# Human-readable status shown in the live console while a tool runs.
TOOL_LABELS = {
    "get_business_overview": "Scanning business overview",
    "list_products": "Reading products",
    "list_services": "Reading services",
    "list_blog_posts": "Reading blog posts",
    "recent_contact_submissions": "Fetching website enquiries",
    "crm_summary": "Querying CRM summary",
    "crm_list_leads": "Querying CRM leads",
    "crm_list_deals": "Querying CRM deals",
    "crm_pipeline": "Reading deal pipeline",
    "crm_list_tasks": "Reading CRM tasks",
    "crm_find_contact": "Finding contact",
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_business_overview",
            "description": "High-level counts across the whole RocketOps estate: products, services, team, blog posts (published/draft), website submissions, CRM contacts and open-deal value. Use for 'status of the business' style questions.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_products",
            "description": "List all RocketOps products with short descriptions.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": "List all RocketOps services offered.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_blog_posts",
            "description": "List blog posts, optionally filtered by status. Includes views and publish date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["all", "published", "draft"], "description": "Filter by status (default all)."},
                    "limit": {"type": "integer", "description": "Max posts (default 20, cap 50)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recent_contact_submissions",
            "description": "Latest raw website contact-form enquiries (name, company, what they're interested in, message).",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Max rows (default 10, cap 30)."}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_summary",
            "description": "CRM snapshot. 'total_contacts' is the total number of leads/contacts in the CRM (use this for 'how many leads/contacts are there'). Also returns counts by lifecycle stage and status, new leads in last 7 days, open-deal count+value, deals won this month, open tasks.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_list_leads",
            "description": "List CRM contacts (a.k.a. leads / prospects / people). By DEFAULT returns ALL contacts regardless of stage. The everyday word 'lead' means ANY contact, NOT the 'lead' lifecycle stage — so do NOT pass 'lifecycle' unless the user explicitly asks for one specific stage (e.g. 'show me customers' or 'sql leads'). This is the right tool to LIST or show contact details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lifecycle": {"type": "string", "enum": ["lead", "mql", "sql", "customer", "churned"]},
                    "status": {"type": "string", "enum": ["new", "working", "qualified", "unqualified"]},
                    "limit": {"type": "integer", "description": "Max rows (default 15, cap 40)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_find_contact",
            "description": "Find CRM contacts by partial name, email, or company, returning their contact_id. ALWAYS use this to resolve a person referred to by name before creating a task, logging activity, or assigning a deal to them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name, email, or company to search for."},
                    "limit": {"type": "integer", "description": "Max matches (default 10)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_list_deals",
            "description": "List CRM deals (highest value first), optionally filtered by status (open/won/lost).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["open", "won", "lost"]},
                    "limit": {"type": "integer", "description": "Max rows (default 15, cap 40)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_pipeline",
            "description": "Open-deal counts and total value grouped by pipeline stage (the sales funnel).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_list_tasks",
            "description": "List CRM follow-up tasks. By default only open (incomplete) tasks, soonest due first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "open_only": {"type": "boolean", "description": "Only incomplete tasks (default true)."},
                    "limit": {"type": "integer", "description": "Max rows (default 20, cap 40)."},
                },
            },
        },
    },
]


def run_tool(name, arguments):
    """Execute a registered READ tool by name with a dict of arguments."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**(arguments or {}))
    except TypeError:
        # Be forgiving about unexpected/missing kwargs from the model.
        try:
            return fn()
        except Exception as e:  # pragma: no cover
            return {"error": str(e)}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE LAYER — governed actions (create / update / delete across CRM + site)
#
#  Rules enforced here (server is the ONLY place writes happen):
#   • Every write re-checks the caller's permission against the target object.
#   • Reps may only modify records they own; deletes + site content = admins only.
#   • Each call runs in a transaction and is recorded to AIActionLog.
#  Risk is computed per-call by risk_of(); risky calls require human confirmation.
# ══════════════════════════════════════════════════════════════════════════════
User = get_user_model()


class WriteError(Exception):
    """Raised by a write tool to signal a user-facing failure (perm/validation)."""


def _admin(user):
    # CRM-admin level = superuser or "CRM Admin" group. NOT plain is_staff — a Sales Rep
    # may be is_staff (to reach the console) yet must stay owner-scoped with no deletes.
    return is_crm_admin(user)


def _require_admin(user):
    if not _admin(user):
        raise WriteError("This action requires admin access.")


def _can_modify(user, obj):
    if _admin(user):
        return True
    return getattr(obj, "owner_id", None) == getattr(user, "id", None)


def _require_modify(user, obj, what="record"):
    if not _can_modify(user, obj):
        raise WriteError(f"You can only modify your own {what}.")


def _resolve_user(username):
    if not username:
        return None
    u = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()
    if not u:
        raise WriteError(f"No user matching '{username}'.")
    return u


def _resolve_company(name, create=True):
    if not name:
        return None
    c = Company.objects.filter(name__iexact=name).first()
    if c:
        return c
    if create:
        return Company.objects.create(name=name)
    raise WriteError(f"No company named '{name}'.")


def _resolve_stage(stage):
    if stage is None:
        return None
    s = PipelineStage.objects.filter(name__iexact=str(stage)).first()
    if not s and str(stage).isdigit():
        s = PipelineStage.objects.filter(pk=int(stage)).first()
    if not s:
        raise WriteError(f"No pipeline stage '{stage}'.")
    return s


def _get(model, pk, what):
    obj = model.objects.filter(pk=pk).first()
    if not obj:
        raise WriteError(f"No {what} with id {pk}.")
    return obj


def _resolve_contact_ref(contact_id=None, contact=None):
    """Resolve a contact from an explicit id OR a name/email string (fallback)."""
    if contact_id:
        return _get(Contact, contact_id, "contact")
    if contact:
        matches = crm_find_contact(contact).get("matches", [])
        if len(matches) == 1:
            return _get(Contact, matches[0]["contact_id"], "contact")
        if not matches:
            raise WriteError(f"No contact matching '{contact}'.")
        opts = ", ".join(f"{m['name']} (id {m['contact_id']})" for m in matches[:6])
        raise WriteError(f"Multiple contacts match '{contact}': {opts}. Re-run with the contact_id.")
    return None


def _blog(ref):
    """Resolve a blog by id or slug."""
    b = None
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        b = Blog.objects.filter(pk=int(ref)).first()
    if not b and ref:
        b = Blog.objects.filter(slug__iexact=str(ref)).first() or Blog.objects.filter(title__iexact=str(ref)).first()
    if not b:
        raise WriteError(f"No blog post matching '{ref}'.")
    return b


# ── CRM writes ────────────────────────────────────────────────────────────────
def crm_create_contact(user, first_name, last_name="", email="", phone="", job_title="",
                       company=None, lifecycle_stage="lead", status="new", source="manual",
                       tags="", **_):
    c = Contact.objects.create(
        first_name=first_name, last_name=last_name or "", email=email or "", phone=phone or "",
        job_title=job_title or "", company=_resolve_company(company), owner=user,
        lifecycle_stage=lifecycle_stage or "lead", status=status or "new",
        source=source or "manual", tags=tags or "",
    )
    return {"ok": True, "contact_id": c.id, "name": c.full_name}


def crm_update_contact(user, contact_id, first_name=None, last_name=None, email=None, phone=None,
                       job_title=None, lifecycle_stage=None, status=None, tags=None,
                       company=None, owner=None, **_):
    c = _get(Contact, contact_id, "contact")
    _require_modify(user, c, "contact")
    for field, val in (("first_name", first_name), ("last_name", last_name), ("email", email),
                       ("phone", phone), ("job_title", job_title), ("lifecycle_stage", lifecycle_stage),
                       ("status", status), ("tags", tags)):
        if val is not None:
            setattr(c, field, val)
    if company is not None:
        c.company = _resolve_company(company)
    if owner is not None:
        c.owner = _resolve_user(owner)
    c.save()
    return {"ok": True, "contact_id": c.id, "name": c.full_name, "lifecycle": c.lifecycle_stage, "status": c.status}


def crm_assign_owner(user, owner, contact_id=None, deal_id=None, contact=None, **_):
    new_owner = _resolve_user(owner)
    if contact_id or contact:
        c = _resolve_contact_ref(contact_id, contact); _require_modify(user, c, "contact")
        c.owner = new_owner; c.save()
        return {"ok": True, "contact_id": c.id, "owner": new_owner.get_username()}
    if deal_id:
        d = _get(Deal, deal_id, "deal"); _require_modify(user, d, "deal")
        d.owner = new_owner; d.save()
        return {"ok": True, "deal_id": d.id, "owner": new_owner.get_username()}
    raise WriteError("Provide a contact_id or deal_id to assign.")


def crm_create_company(user, name, website="", industry="", size="", country="", phone="", notes="", **_):
    c = Company.objects.create(name=name, website=website or "", industry=industry or "",
                               size=size or "", country=country or "", phone=phone or "",
                               notes=notes or "", owner=user)
    return {"ok": True, "company_id": c.id, "name": c.name}


def crm_update_company(user, company_id, name=None, website=None, industry=None, size=None,
                       country=None, phone=None, notes=None, **_):
    c = _get(Company, company_id, "company")
    _require_modify(user, c, "company")
    for field, val in (("name", name), ("website", website), ("industry", industry),
                       ("size", size), ("country", country), ("phone", phone), ("notes", notes)):
        if val is not None:
            setattr(c, field, val)
    c.save()
    return {"ok": True, "company_id": c.id, "name": c.name}


def crm_create_deal(user, name, amount=0, currency="USD", company=None, contact_id=None,
                    stage=None, expected_close_date=None, contact=None, **_):
    contact_obj = _resolve_contact_ref(contact_id, contact)
    d = Deal.objects.create(
        name=name, amount=amount or 0, currency=currency or "USD",
        company=_resolve_company(company), contact=contact_obj, owner=user,
        stage=_resolve_stage(stage) if stage else PipelineStage.objects.filter(is_won=False, is_lost=False).order_by("order").first(),
        expected_close_date=expected_close_date or None,
    )
    return {"ok": True, "deal_id": d.id, "name": d.name, "stage": d.stage.name if d.stage else None, "status": d.status}


def crm_update_deal(user, deal_id, name=None, amount=None, currency=None, stage=None,
                    expected_close_date=None, owner=None, **_):
    d = _get(Deal, deal_id, "deal")
    _require_modify(user, d, "deal")
    if name is not None:
        d.name = name
    if amount is not None:
        d.amount = amount
    if currency is not None:
        d.currency = currency
    if expected_close_date is not None:
        d.expected_close_date = expected_close_date or None
    if owner is not None:
        d.owner = _resolve_user(owner)
    if stage is not None:
        d.stage = _resolve_stage(stage)
    d.save()
    return {"ok": True, "deal_id": d.id, "name": d.name, "stage": d.stage.name if d.stage else None, "status": d.status}


def crm_move_deal(user, deal_id, stage, **_):
    d = _get(Deal, deal_id, "deal")
    _require_modify(user, d, "deal")
    d.stage = _resolve_stage(stage)
    d.save()
    return {"ok": True, "deal_id": d.id, "stage": d.stage.name if d.stage else None, "status": d.status}


def crm_set_deal_outcome(user, deal_id, outcome, lost_reason="", **_):
    d = _get(Deal, deal_id, "deal")
    _require_modify(user, d, "deal")
    outcome = (outcome or "").lower()
    flag = {"won": "is_won", "lost": "is_lost"}.get(outcome)
    if not flag:
        raise WriteError("outcome must be 'won' or 'lost'.")
    stage = PipelineStage.objects.filter(**{flag: True}).order_by("order").first()
    if not stage:
        raise WriteError(f"No '{outcome}' stage configured.")
    d.stage = stage
    if outcome == "lost" and lost_reason:
        d.lost_reason = lost_reason
    d.save()
    return {"ok": True, "deal_id": d.id, "status": d.status}


def crm_log_activity(user, type="note", subject="", body="", contact_id=None, deal_id=None, contact=None, **_):
    if type not in ("note", "call", "email", "meeting"):
        raise WriteError("type must be note, call, email or meeting (use crm_create_task for tasks).")
    contact_obj = _resolve_contact_ref(contact_id, contact)
    deal = _get(Deal, deal_id, "deal") if deal_id else None
    a = Activity.objects.create(type=type, subject=subject or "", body=body or "",
                                contact=contact_obj, deal=deal, owner=user)
    return {"ok": True, "activity_id": a.id, "type": a.type,
            "contact": contact_obj.full_name if contact_obj else None}


def crm_create_task(user, subject, due_date=None, contact_id=None, deal_id=None, body="", contact=None, **_):
    contact_obj = _resolve_contact_ref(contact_id, contact)
    deal = _get(Deal, deal_id, "deal") if deal_id else None
    a = Activity.objects.create(type="task", subject=subject, body=body or "",
                                contact=contact_obj, deal=deal, owner=user, due_date=due_date or None)
    return {"ok": True, "task_id": a.id, "subject": a.subject,
            "contact": contact_obj.full_name if contact_obj else None,
            "due_date": a.due_date.isoformat() if a.due_date else None}


def crm_complete_task(user, task_id, **_):
    a = _get(Activity, task_id, "task")
    _require_modify(user, a, "task")
    a.is_done = True
    a.save()
    return {"ok": True, "task_id": a.id, "done": a.is_done}


def crm_delete_contact(user, contact_id, **_):
    _require_admin(user)
    c = _get(Contact, contact_id, "contact")
    name = c.full_name
    c.delete()
    return {"ok": True, "deleted": "contact", "name": name}


def crm_delete_deal(user, deal_id, **_):
    _require_admin(user)
    d = _get(Deal, deal_id, "deal")
    name = d.name
    d.delete()
    return {"ok": True, "deleted": "deal", "name": name}


# ── Site / content writes (admin only) ────────────────────────────────────────
def content_create_blog_draft(user, title, excerpt="", content="", category=None,
                              meta_title="", meta_description="", focus_keyword="", keywords="", **_):
    _require_admin(user)
    cat = None
    if category:
        cat = BlogCategory.objects.filter(name__iexact=category).first() or \
            BlogCategory.objects.create(name=category)
    b = Blog.objects.create(
        title=title, excerpt=excerpt or title, content=content or "",
        category=cat, status="draft",
        meta_title=meta_title or "", meta_description=meta_description or "",
        focus_keyword=focus_keyword or "", keywords=keywords or "",
        cover_image="",  # editable later in admin
    )
    return {"ok": True, "blog_id": b.id, "slug": b.slug, "status": b.status}


def content_update_blog(user, blog, title=None, excerpt=None, content=None, category=None,
                        meta_title=None, meta_description=None, focus_keyword=None, keywords=None, **_):
    _require_admin(user)
    b = _blog(blog)
    for field, val in (("title", title), ("excerpt", excerpt), ("content", content),
                       ("meta_title", meta_title), ("meta_description", meta_description),
                       ("focus_keyword", focus_keyword), ("keywords", keywords)):
        if val is not None:
            setattr(b, field, val)
    if category is not None:
        b.category = BlogCategory.objects.filter(name__iexact=category).first() or \
            BlogCategory.objects.create(name=category)
    b.save()
    return {"ok": True, "blog_id": b.id, "slug": b.slug, "title": b.title}


def content_set_blog_status(user, blog, status, **_):
    _require_admin(user)
    if status not in ("published", "draft"):
        raise WriteError("status must be 'published' or 'draft'.")
    b = _blog(blog)
    b.status = status
    b.save()
    return {"ok": True, "blog_id": b.id, "slug": b.slug, "status": b.status}


def content_delete_blog(user, blog, **_):
    _require_admin(user)
    b = _blog(blog)
    title = b.title
    b.delete()
    return {"ok": True, "deleted": "blog", "title": title}


def content_update_product(user, product_id, title=None, description=None, detailed_description=None, link=None, **_):
    _require_admin(user)
    p = _get(Product, product_id, "product")
    for field, val in (("title", title), ("description", description),
                       ("detailed_description", detailed_description), ("link", link)):
        if val is not None:
            setattr(p, field, val)
    p.save()
    return {"ok": True, "product_id": p.id, "title": p.title, "slug": p.slug}


def content_update_service(user, service_id, header_title=None, description=None, **_):
    _require_admin(user)
    s = _get(Service, service_id, "service")
    if header_title is not None:
        s.header_title = header_title
    if description is not None:
        s.description = description
    s.save()
    return {"ok": True, "service_id": s.id, "title": s.header_title}


def content_manage_faq(user, action, faq_id=None, question=None, answer=None, is_active=None, **_):
    _require_admin(user)
    action = (action or "").lower()
    if action == "create":
        f = Faq.objects.create(question=question or "", answer=answer or "",
                               is_active=True if is_active is None else is_active)
        return {"ok": True, "faq_id": f.id, "action": "created"}
    f = _get(Faq, faq_id, "FAQ")
    if action == "delete":
        f.delete()
        return {"ok": True, "deleted": "faq", "id": faq_id}
    if action == "update":
        if question is not None:
            f.question = question
        if answer is not None:
            f.answer = answer
        if is_active is not None:
            f.is_active = is_active
        f.save()
        return {"ok": True, "faq_id": f.id, "action": "updated"}
    raise WriteError("action must be create, update or delete.")


def content_manage_testimonial(user, action, testimonial_id=None, quote=None, author=None,
                               title=None, is_active=None, **_):
    _require_admin(user)
    action = (action or "").lower()
    if action == "create":
        t = Testimonial.objects.create(quote=quote or "", author=author or "", title=title or "",
                                       is_active=True if is_active is None else is_active)
        return {"ok": True, "testimonial_id": t.id, "action": "created"}
    t = _get(Testimonial, testimonial_id, "testimonial")
    if action == "delete":
        t.delete()
        return {"ok": True, "deleted": "testimonial", "id": testimonial_id}
    if action == "update":
        for field, val in (("quote", quote), ("author", author), ("title", title)):
            if val is not None:
                setattr(t, field, val)
        if is_active is not None:
            t.is_active = is_active
        t.save()
        return {"ok": True, "testimonial_id": t.id, "action": "updated"}
    raise WriteError("action must be create, update or delete.")


# ── Write registry, risk model, summaries, dispatch ───────────────────────────
WRITE_FUNCTIONS = {
    "crm_create_contact": crm_create_contact,
    "crm_update_contact": crm_update_contact,
    "crm_assign_owner": crm_assign_owner,
    "crm_create_company": crm_create_company,
    "crm_update_company": crm_update_company,
    "crm_create_deal": crm_create_deal,
    "crm_update_deal": crm_update_deal,
    "crm_move_deal": crm_move_deal,
    "crm_set_deal_outcome": crm_set_deal_outcome,
    "crm_log_activity": crm_log_activity,
    "crm_create_task": crm_create_task,
    "crm_complete_task": crm_complete_task,
    "crm_delete_contact": crm_delete_contact,
    "crm_delete_deal": crm_delete_deal,
    "content_create_blog_draft": content_create_blog_draft,
    "content_update_blog": content_update_blog,
    "content_set_blog_status": content_set_blog_status,
    "content_delete_blog": content_delete_blog,
    "content_update_product": content_update_product,
    "content_update_service": content_update_service,
    "content_manage_faq": content_manage_faq,
    "content_manage_testimonial": content_manage_testimonial,
}
WRITE_TOOLS = set(WRITE_FUNCTIONS.keys())

# Tools that ALWAYS require confirmation regardless of the auto-run toggle.
_ALWAYS_RISKY = {
    "crm_set_deal_outcome": "close_deal",
    "crm_delete_contact": "delete",
    "crm_delete_deal": "delete",
    "content_set_blog_status": "publish",
    "content_delete_blog": "delete",
}


def _stage_is_closing(stage):
    try:
        s = _resolve_stage(stage)
    except WriteError:
        return False
    return bool(s and (s.is_won or s.is_lost))


def risk_of(name, args):
    """Return a risk label (str) if the call needs confirmation, else None."""
    args = args or {}
    if name in _ALWAYS_RISKY:
        return _ALWAYS_RISKY[name]
    if name == "crm_update_contact" and args.get("lifecycle_stage") == "churned":
        return "churn"
    if name in ("crm_update_deal", "crm_move_deal") and args.get("stage") and _stage_is_closing(args["stage"]):
        return "close_deal"
    if name in ("content_manage_faq", "content_manage_testimonial") and (args.get("action") or "").lower() == "delete":
        return "delete"
    if name in ("content_manage_faq", "content_manage_testimonial") and args.get("is_active") is False:
        return "deactivate"
    return None


def _name_lookup(model, pk, attr, what):
    obj = model.objects.filter(pk=pk).first()
    return getattr(obj, attr) if obj else f"{what} #{pk}"


def summarize_write(name, args):
    """Human-readable one-liner shown on the confirmation card."""
    a = args or {}
    try:
        if name == "crm_delete_contact":
            return f"Delete contact: {_name_lookup(Contact, a.get('contact_id'), 'full_name', 'contact')}"
        if name == "crm_delete_deal":
            return f"Delete deal: {_name_lookup(Deal, a.get('deal_id'), 'name', 'deal')}"
        if name == "crm_set_deal_outcome":
            return f"Mark deal \"{_name_lookup(Deal, a.get('deal_id'), 'name', 'deal')}\" as {a.get('outcome', '?').upper()}"
        if name in ("crm_update_deal", "crm_move_deal") and a.get("stage"):
            return f"Move deal \"{_name_lookup(Deal, a.get('deal_id'), 'name', 'deal')}\" → {a.get('stage')}"
        if name == "crm_update_contact" and a.get("lifecycle_stage") == "churned":
            return f"Mark contact \"{_name_lookup(Contact, a.get('contact_id'), 'full_name', 'contact')}\" as churned"
        if name == "content_set_blog_status":
            return f"Set blog \"{a.get('blog')}\" status → {a.get('status')}"
        if name == "content_delete_blog":
            return f"Delete blog post: {a.get('blog')}"
        if name in ("content_manage_faq", "content_manage_testimonial"):
            return f"{(a.get('action') or '').title()} {name.replace('content_manage_', '')}"
    except Exception:
        pass
    return f"{name}({json.dumps(a, default=str)})"


def _audit(user, name, args, result, status, tool_call_id):
    try:
        AIActionLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            tool=name, args=args or {}, result=result if isinstance(result, dict) else {"value": result},
            status=status, tool_call_id=tool_call_id or "",
        )
    except Exception:
        pass  # auditing must never break the action flow


def run_write_tool(name, args, user, tool_call_id=""):
    """Execute a WRITE tool inside a transaction, then record it to the audit log."""
    fn = WRITE_FUNCTIONS.get(name)
    if fn is None:
        result = {"error": f"Unknown action: {name}"}
        _audit(user, name, args, result, "error", tool_call_id)
        return result
    try:
        with transaction.atomic():
            result = fn(user, **(args or {}))
        _audit(user, name, args, result, "success", tool_call_id)
        return result
    except WriteError as e:
        result = {"error": str(e)}
        _audit(user, name, args, result, "error", tool_call_id)
        return result
    except Exception as e:  # pragma: no cover
        result = {"error": f"{type(e).__name__}: {e}"}
        _audit(user, name, args, result, "error", tool_call_id)
        return result


def log_rejected(user, name, args, tool_call_id=""):
    _audit(user, name, args, {"declined": True}, "rejected", tool_call_id)


WRITE_LABELS = {
    "crm_create_contact": "Creating contact",
    "crm_update_contact": "Updating contact",
    "crm_assign_owner": "Reassigning owner",
    "crm_create_company": "Creating company",
    "crm_update_company": "Updating company",
    "crm_create_deal": "Creating deal",
    "crm_update_deal": "Updating deal",
    "crm_move_deal": "Moving deal",
    "crm_set_deal_outcome": "Closing deal",
    "crm_log_activity": "Logging activity",
    "crm_create_task": "Creating task",
    "crm_complete_task": "Completing task",
    "crm_delete_contact": "Deleting contact",
    "crm_delete_deal": "Deleting deal",
    "content_create_blog_draft": "Drafting blog post",
    "content_update_blog": "Updating blog post",
    "content_set_blog_status": "Changing blog status",
    "content_delete_blog": "Deleting blog post",
    "content_update_product": "Updating product",
    "content_update_service": "Updating service",
    "content_manage_faq": "Managing FAQ",
    "content_manage_testimonial": "Managing testimonial",
}
TOOL_LABELS.update(WRITE_LABELS)


def _fn_schema(name, description, properties, required=None):
    params = {"type": "object", "properties": properties}
    if required:
        params["required"] = required
    return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}


_S = {"type": "string"}
_I = {"type": "integer"}
_N = {"type": "number"}
_B = {"type": "boolean"}

WRITE_SCHEMAS = [
    _fn_schema("crm_create_contact", "Create a new CRM contact/lead. Owner defaults to you.",
               {"first_name": _S, "last_name": _S, "email": _S, "phone": _S, "job_title": _S,
                "company": {"type": "string", "description": "Company name (created if new)."},
                "lifecycle_stage": {"type": "string", "enum": ["lead", "mql", "sql", "customer", "churned"]},
                "status": {"type": "string", "enum": ["new", "working", "qualified", "unqualified"]},
                "tags": _S}, ["first_name"]),
    _fn_schema("crm_update_contact", "Update fields on an existing contact (by contact_id). Find the id first with crm_list_leads.",
               {"contact_id": _I, "first_name": _S, "last_name": _S, "email": _S, "phone": _S,
                "job_title": _S, "lifecycle_stage": {"type": "string", "enum": ["lead", "mql", "sql", "customer", "churned"]},
                "status": {"type": "string", "enum": ["new", "working", "qualified", "unqualified"]},
                "tags": _S, "company": _S, "owner": {"type": "string", "description": "username/email of new owner"}},
               ["contact_id"]),
    _fn_schema("crm_assign_owner", "Assign/reassign the owner of a contact or deal (by username/email).",
               {"owner": _S, "contact_id": _I, "deal_id": _I,
                "contact": {"type": "string", "description": "Contact name or email (alternative to contact_id)."}},
               ["owner"]),
    _fn_schema("crm_create_company", "Create a CRM company/account.",
               {"name": _S, "website": _S, "industry": _S,
                "size": {"type": "string", "enum": ["1-10", "11-50", "51-200", "201-1000", "1000+"]},
                "country": _S, "phone": _S, "notes": _S}, ["name"]),
    _fn_schema("crm_update_company", "Update a company by company_id.",
               {"company_id": _I, "name": _S, "website": _S, "industry": _S, "size": _S,
                "country": _S, "phone": _S, "notes": _S}, ["company_id"]),
    _fn_schema("crm_create_deal", "Create a deal/opportunity. Defaults to the first open stage if none given.",
               {"name": _S, "amount": _N, "currency": _S,
                "company": {"type": "string", "description": "Company name (created if new)."},
                "contact_id": _I, "contact": {"type": "string", "description": "Contact name or email (alternative to contact_id)."},
                "stage": {"type": "string", "description": "Stage name."},
                "expected_close_date": {"type": "string", "description": "YYYY-MM-DD"}}, ["name"]),
    _fn_schema("crm_update_deal", "Update a deal (by deal_id): name, amount, currency, stage, owner, expected_close_date.",
               {"deal_id": _I, "name": _S, "amount": _N, "currency": _S, "stage": _S,
                "expected_close_date": _S, "owner": _S}, ["deal_id"]),
    _fn_schema("crm_move_deal", "Move a deal to a pipeline stage (by name).",
               {"deal_id": _I, "stage": _S}, ["deal_id", "stage"]),
    _fn_schema("crm_set_deal_outcome", "Mark a deal won or lost (closes it).",
               {"deal_id": _I, "outcome": {"type": "string", "enum": ["won", "lost"]}, "lost_reason": _S},
               ["deal_id", "outcome"]),
    _fn_schema("crm_log_activity", "Log a note/call/email/meeting against a contact and/or deal.",
               {"type": {"type": "string", "enum": ["note", "call", "email", "meeting"]},
                "subject": _S, "body": _S, "contact_id": _I, "deal_id": _I,
                "contact": {"type": "string", "description": "Contact name or email (alternative to contact_id)."}},
               ["type"]),
    _fn_schema("crm_create_task", "Create a follow-up task (optionally with a due date and linked contact/deal). You may pass the contact's name/email in 'contact' instead of contact_id.",
               {"subject": _S, "due_date": {"type": "string", "description": "ISO datetime, e.g. 2026-06-20T10:00:00Z"},
                "contact_id": _I, "deal_id": _I, "body": _S,
                "contact": {"type": "string", "description": "Contact name or email (alternative to contact_id)."}},
               ["subject"]),
    _fn_schema("crm_complete_task", "Mark a task done (by task_id).", {"task_id": _I}, ["task_id"]),
    _fn_schema("crm_delete_contact", "Permanently delete a contact (admin only, requires confirmation).",
               {"contact_id": _I}, ["contact_id"]),
    _fn_schema("crm_delete_deal", "Permanently delete a deal (admin only, requires confirmation).",
               {"deal_id": _I}, ["deal_id"]),
    _fn_schema("content_create_blog_draft", "Create a DRAFT blog post (not published). Add a cover image later in the admin.",
               {"title": _S, "excerpt": _S, "content": {"type": "string", "description": "HTML body."},
                "category": _S, "meta_title": _S, "meta_description": _S, "focus_keyword": _S, "keywords": _S},
               ["title"]),
    _fn_schema("content_update_blog", "Update a blog post's text/SEO (by slug or id). Does not change publish status.",
               {"blog": {"type": "string", "description": "slug or id"}, "title": _S, "excerpt": _S,
                "content": _S, "category": _S, "meta_title": _S, "meta_description": _S,
                "focus_keyword": _S, "keywords": _S}, ["blog"]),
    _fn_schema("content_set_blog_status", "Publish or unpublish a blog post (by slug or id).",
               {"blog": _S, "status": {"type": "string", "enum": ["published", "draft"]}}, ["blog", "status"]),
    _fn_schema("content_delete_blog", "Permanently delete a blog post (admin only, requires confirmation).",
               {"blog": _S}, ["blog"]),
    _fn_schema("content_update_product", "Update a product's text (by product_id).",
               {"product_id": _I, "title": _S, "description": _S, "detailed_description": _S, "link": _S},
               ["product_id"]),
    _fn_schema("content_update_service", "Update a service's title/description (by service_id).",
               {"service_id": _I, "header_title": _S, "description": _S}, ["service_id"]),
    _fn_schema("content_manage_faq", "Create, update or delete a site FAQ.",
               {"action": {"type": "string", "enum": ["create", "update", "delete"]},
                "faq_id": _I, "question": _S, "answer": _S, "is_active": _B}, ["action"]),
    _fn_schema("content_manage_testimonial", "Create, update or delete a testimonial.",
               {"action": {"type": "string", "enum": ["create", "update", "delete"]},
                "testimonial_id": _I, "quote": _S, "author": _S, "title": _S, "is_active": _B}, ["action"]),
]

# Expose all tools (read + write) to the model.
TOOL_SCHEMAS = TOOL_SCHEMAS + WRITE_SCHEMAS
