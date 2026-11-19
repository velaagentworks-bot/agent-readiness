#!/usr/bin/env python3
"""
Minimal MCP server for the Agent Readiness Pack.

Exposes a site's public docs/FAQ as tools over the Model Context Protocol
stdio transport. Standard library only; no install, no network, no API keys.

Usage:
    python3 server.py [--site site.json]

The server speaks newline-delimited JSON-RPC 2.0 on stdin/stdout, as the MCP
stdio transport specifies. It implements the subset an AI client needs:
initialize, notifications/initialized, ping, tools/list, tools/call.

Honesty limits (also in README.md):
  * It answers only from text saved in site.json at build time. It never
    invents an answer and never fetches the live site at request time.
  * If nothing matches, it says so.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"
SERVER_VERSION = "1.0.0"
MAX_TEXT_CHARS = 12000


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class Site:
    def __init__(self, data: dict) -> None:
        self.name = _clean(data.get("name") or "Site")
        self.url = _clean(data.get("url") or "")
        self.pages = []
        for page in data.get("pages") or []:
            url = _clean(page.get("url"))
            text = _clean(page.get("text"))
            if not url or not text:
                continue
            self.pages.append(
                {
                    "url": url,
                    "title": _clean(page.get("title")) or url,
                    "description": _clean(page.get("description")),
                    "text": text,
                }
            )
        if not self.pages:
            raise ValueError("site.json contains no usable pages")

    def list_pages(self) -> list[dict]:
        return [
            {"title": p["title"], "url": p["url"], "chars": len(p["text"])}
            for p in self.pages
        ]

    def get_page(self, ref: str) -> dict | None:
        ref = (ref or "").strip()
        if not ref:
            return None
        norm = ref.rstrip("/")
        for page in self.pages:
            if page["url"].rstrip("/") == norm:
                return page
        for page in self.pages:
            if page["url"].rstrip("/").endswith(norm) or norm.endswith(
                page["url"].rstrip("/")
            ):
                return page
        return None

    def search(self, query: str, limit: int = 5) -> list[dict]:
        terms = [t for t in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(t) > 1]
        limit = max(1, min(int(limit or 5), 10))
        if not terms:
            return [
                {
                    "title": p["title"],
                    "url": p["url"],
                    "excerpt": p["description"] or p["text"][:240],
                    "score": 0,
                }
                for p in self.pages[:limit]
            ]

        results = []
        for page in self.pages:
            haystack = f'{page["title"]} {page["description"]} {page["text"]}'.lower()
            score = sum(haystack.count(t) for t in terms)
            if score <= 0:
                continue
            title_hits = sum(page["title"].lower().count(t) for t in terms)
            score += title_hits * 3
            excerpt = self._excerpt(page["text"], terms)
            results.append(
                {
                    "title": page["title"],
                    "url": page["url"],
                    "excerpt": excerpt,
                    "score": score,
                }
            )
        results.sort(key=lambda r: (-r["score"], r["url"]))
        return results[:limit]

    @staticmethod
    def _excerpt(text: str, terms: list[str]) -> str:
        lower = text.lower()
        positions = [lower.find(t) for t in terms if lower.find(t) >= 0]
        start = max(0, (min(positions) if positions else 0) - 160)
        end = min(len(text), start + 420)
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        return f"{prefix}{text[start:end].strip()}{suffix}"


TOOLS = [
    {
        "name": "search_docs",
        "description": "Search this site's public documentation and return the most relevant passages with their source URLs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Words to search for."},
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (1-10). Default 5.",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_page",
        "description": "Return the saved public text of one page by its exact URL or URL path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Page URL or path, e.g. https://example.com/docs or /docs.",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "list_pages",
        "description": "List every page saved in this server, with its title, URL and text length.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class Server:
    def __init__(self, site: Site) -> None:
        self.site = site

    def handle(self, message: dict) -> dict | None:
        method = message.get("method")
        msg_id = message.get("id")
        is_notification = "id" not in message

        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": f"{self.site.name} docs", "version": SERVER_VERSION},
                "instructions": (
                    "Answers come only from the public pages saved in site.json. "
                    "Cite the returned source URL. If search finds nothing, say so."
                ),
            }
        elif method in ("notifications/initialized", "initialized"):
            return None
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            return self._call_tool(message, msg_id)
        else:
            if is_notification:
                return None
            return self._error(msg_id, -32601, f"Method not found: {method}")

        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _call_tool(self, message: dict, msg_id) -> dict:
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}

        if name == "search_docs":
            results = self.site.search(str(args.get("query", "")), args.get("limit", 5))
            payload = {"query": args.get("query", ""), "results": results}
            if not results:
                payload["note"] = "No saved page matched those words. Try different terms or list_pages."
            return self._tool_result(msg_id, payload)

        if name == "get_page":
            page = self.site.get_page(str(args.get("url", "")))
            if page is None:
                return self._tool_result(
                    msg_id,
                    {
                        "error": "No saved page matched that URL.",
                        "available": [p["url"] for p in self.site.pages],
                    },
                    is_error=True,
                )
            return self._tool_result(
                msg_id,
                {
                    "url": page["url"],
                    "title": page["title"],
                    "description": page["description"],
                    "text": page["text"][:MAX_TEXT_CHARS],
                    "truncated": len(page["text"]) > MAX_TEXT_CHARS,
                },
            )

        if name == "list_pages":
            return self._tool_result(msg_id, {"pages": self.site.list_pages()})

        return self._error(msg_id, -32602, f"Unknown tool: {name}")

    @staticmethod
    def _tool_result(msg_id, payload: dict, is_error: bool = False) -> dict:
        result = {
            "content": [
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}
            ]
        }
        if is_error:
            result["isError"] = True
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id, code: int, text: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": text}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve one site's docs over MCP stdio.")
    parser.add_argument(
        "--site",
        default=str(Path(__file__).with_name("site.json")),
        help="Path to site.json (default: next to this script).",
    )
    args = parser.parse_args(argv)

    try:
        data = json.loads(Path(args.site).read_text(encoding="utf-8"))
        site = Site(data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"server.py: cannot load site data: {exc}", file=sys.stderr)
        return 1

    server = Server(site)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                ),
                flush=True,
            )
            continue
        if not isinstance(message, dict):
            continue
        response = server.handle(message)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
