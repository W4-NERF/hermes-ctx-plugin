"""CLI commands for the CTX memory plugin: ``hermes ctx <status|sync|query|store|search|get>``.

Self-contained (stdlib only) — imported at argparse setup time before the
provider itself is loaded. Active-provider gating applies: the commands only
appear when ``memory.provider: ctx`` is set.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_CONFIG_FILENAME = "ctx.json"
_ENTRY_SEPARATOR = "§"


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return Path(str(get_hermes_home()))
    except Exception:
        return Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))


def _load_config() -> dict[str, Any]:
    config: dict[str, Any] = {}
    path = _hermes_home() / _CONFIG_FILENAME
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                config = raw
        except Exception:
            pass
    return config


def _base_url() -> str:
    return (os.environ.get("CTX_BASE_URL", "").strip() or str(_load_config().get("ctx_base_url") or "")).rstrip("/")


def _api_key() -> str:
    return os.environ.get("CTX_KEY", "").strip()


def _request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 20.0) -> dict[str, Any]:
    url = f"{_base_url()}{path}"
    headers = {
        "X-Context-Key": _api_key(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw) if raw.strip() else {"success": True}
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        return {"success": False, "error": f"HTTP {exc.code}: {body or exc.reason}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _parse_memory_file(path: Path) -> list:
    """Split a MEMORY.md/USER.md into entries on '§' separator lines."""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    parts = [p.strip() for p in text.split(_ENTRY_SEPARATOR)]
    return [p for p in parts if p]


def _derive_title(content: str, max_len: int = 60, prefix: str = "") -> str:
    import re

    text = re.sub(r"\s+", " ", content.strip())
    text = re.sub(r"[`#>]", "", text)
    if not text:
        return f"{prefix}untitled".strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip(" ,.;:-") + "…"
    return f"{prefix}{text}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_status(args) -> None:
    base = _base_url()
    key = _api_key()
    print("CTX memory plugin — status")
    print(f"  base URL: {base or '(not set)'}")
    print(f"  key:      {'set' if key else 'NOT set'}")
    if not (base and key):
        print("  ✗ Configure CTX_BASE_URL/CTX_KEY (env or ctx.json) first.")
        return
    info = _request("GET", "/api/whoami", timeout=10.0)
    if info.get("success"):
        scope, label, role = info.get("home_scope") or "?", info.get("label") or "?", info.get("role") or "?"
        print(f"  ✓ connected · scope: {scope} · label: {label} · role: {role}")
    else:
        print(f"  ✗ {info.get('error') or 'whoami failed'}")
    cfg = _load_config()
    if cfg:
        print("  ctx.json settings:")
        for k, v in sorted(cfg.items()):
            print(f"    {k}: {v}")


def cmd_sync(args) -> None:
    """Push built-in MEMORY.md/USER.md entries to CTX (agent-briefing/reference)."""
    base, key = _base_url(), _api_key()
    if not (base and key):
        print("✗ CTX not configured (CTX_BASE_URL/CTX_KEY).")
        return
    home = _hermes_home()
    sources = [
        (home / "memories" / "MEMORY.md", "agent-briefing", "memory"),
        (home / "memories" / "USER.md", "reference", "user"),
    ]
    total = 0
    for path, category, label in sources:
        entries = _parse_memory_file(path)
        stored = 0
        prefix = "memory: " if label == "memory" else "user: "
        for entry in entries:
            resp = _request(
                "POST",
                "/api/store",
                {
                    "category": category,
                    "title": _derive_title(entry, prefix=prefix),
                    "content": entry,
                    "sensitivity": "personal",
                },
                timeout=15.0,
            )
            if resp.get("success"):
                stored += 1
            else:
                print(f"  ✗ {label}: {resp.get('error')}")
        total += stored
        print(f"  {label}: {stored}/{len(entries)} entries mirrored")
    print(f"Done — {total} blocks stored/updated.")


def cmd_query(args) -> None:
    resp = _request(
        "POST",
        "/api/query",
        {"query": args.text, "synthesize": bool(args.synthesize), "include_content": True},
        timeout=120.0 if args.synthesize else 20.0,
    )
    if not resp.get("success"):
        print(f"✗ {resp.get('error')}")
        return
    if args.synthesize and resp.get("answer"):
        print(resp["answer"])
    for source in resp.get("sources") or []:
        print(f"- [{source.get('category')}] {source.get('title')}  (id: {source.get('id')})")
    if not resp.get("sources"):
        print("(no hits)")


def cmd_store(args) -> None:
    resp = _request(
        "POST",
        "/api/store",
        {
            "category": args.category,
            "title": args.title,
            "content": args.content,
            "sensitivity": getattr(args, "sensitivity", None) or "personal",
        },
        timeout=15.0,
    )
    if resp.get("success"):
        print(f"✓ stored: [{args.category}] {args.title}" + (f" (id: {resp.get('id')})" if resp.get("id") else ""))
    else:
        print(f"✗ {resp.get('error')}")


def cmd_search(args) -> None:
    payload: dict[str, Any] = {"query": args.text}
    if getattr(args, "category", None):
        payload["category"] = args.category
    resp = _request("POST", "/api/search", payload, timeout=15.0)
    if not resp.get("success"):
        print(f"✗ {resp.get('error')}")
        return
    results = resp.get("results") or []
    print(f"{resp.get('count', len(results))} result(s):")
    for item in results:
        print(f"- [{item.get('category')}] {item.get('title')}  (id: {item.get('id')})")


def cmd_get(args) -> None:
    resp = _request("POST", "/api/manage", {"action": "get", "data": {"id": args.block_id}}, timeout=15.0)
    if not resp.get("success"):
        print(f"✗ {resp.get('error')}")
        return
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def ctx_command(args) -> None:
    sub = getattr(args, "ctx_command", None)
    if sub == "status":
        cmd_status(args)
    elif sub == "sync":
        cmd_sync(args)
    elif sub == "query":
        cmd_query(args)
    elif sub == "store":
        cmd_store(args)
    elif sub == "search":
        cmd_search(args)
    elif sub == "get":
        cmd_get(args)
    else:
        print("Usage: hermes ctx <status|sync|query|store|search|get>")
        sys.exit(2)


def register_cli(subparser) -> None:
    """Build the ``hermes ctx`` argparse tree (called by plugin CLI discovery)."""
    subs = subparser.add_subparsers(dest="ctx_command")

    p_status = subs.add_parser("status", help="Show CTX connection status")
    p_status.set_defaults(func=ctx_command)

    p_sync = subs.add_parser("sync", help="Mirror built-in MEMORY.md/USER.md entries to CTX")
    p_sync.set_defaults(func=ctx_command)

    p_query = subs.add_parser("query", help="Query CTX (retrieval, optional LLM synthesis)")
    p_query.add_argument("text", help="The question or topic")
    p_query.add_argument("--synthesize", action="store_true", help="Run LLM synthesis (slower)")
    p_query.set_defaults(func=ctx_command)

    p_store = subs.add_parser("store", help="Store a knowledge block")
    p_store.add_argument("category", help="Block category")
    p_store.add_argument("title", help="Block title")
    p_store.add_argument("content", help="Block content")
    p_store.add_argument("--sensitivity", default="personal", choices=["credentials", "personal", "internal", "public"])
    p_store.set_defaults(func=ctx_command)

    p_search = subs.add_parser("search", help="Lightweight search (no LLM)")
    p_search.add_argument("text", help="Search query")
    p_search.add_argument("--category", help="Optional category filter")
    p_search.set_defaults(func=ctx_command)

    p_get = subs.add_parser("get", help="Fetch a full block by id")
    p_get.add_argument("block_id", help="CTX block id (UUID)")
    p_get.set_defaults(func=ctx_command)
