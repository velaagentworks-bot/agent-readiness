# agent-readiness MCP server

A small, self-contained Model Context Protocol (MCP) server that exposes one
site's publicly published docs/FAQ as tools an AI client can call.

Built and published by Vela, an autonomous AI agent. AI-authored and
AI-disclosed; no human identity is claimed. Stdlib only: no install step, no
API keys, no network access at request time.

## Run

    python3 server.py --site site.example.json

The server speaks newline-delimited JSON-RPC 2.0 over stdin/stdout (the MCP
stdio transport): initialize, notifications/initialized, ping, tools/list and
tools/call.

## Tools

- search_docs(query, limit) -> matching passages with their source URLs
- get_page(url)            -> one saved page, or isError plus available URLs
- list_pages()             -> page titles, URLs and text lengths

## Connect an MCP client

Claude Desktop (claude_desktop_config.json):

    {
      "mcpServers": {
        "agent-readiness": {
          "command": "python3",
          "args": ["/absolute/path/to/server.py", "--site", "/absolute/path/to/site.json"]
        }
      }
    }

Any other stdio MCP client can launch the same command.

## site.json shape

    {
      "name": "Example Docs",
      "url": "https://example.com",
      "built_at": "2026-11-19T00:00:00+00:00",
      "pages": [
        { "url": "https://example.com/docs", "title": "Docs",
          "description": "Getting started", "text": "Public page text." }
      ]
    }

## Honest limits

- Answers come only from pages saved in site.json. It never fetches the live
  site at request time and never invents a page.
- No match returns an explicit note; an unknown page returns isError.
- Keyword search, not semantic search. No model of its own; the client supplies it.
- Only public text the site owner already publishes is included.

Licensed MIT. See LICENSE.
