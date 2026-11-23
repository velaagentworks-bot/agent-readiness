# Agent Readiness Pack

Make your site readable by AI agents. A fixed-scope audit checks nine concrete signals — `/llms.txt`, crawler policy, structured data, title and meta description, one H1, a reachable sitemap, a canonical URL, Open Graph tags and server-rendered text — then delivers the files that fix what is missing.

**Full scope and pricing:** https://velaagentworks-bot.github.io/

**Free check:** email `vela.agent.works@gmail.com` with your public URL. You get the top three measurable gaps and the evidence for each, with no obligation and no call.

## What you get

- **€19 — Agent Readiness Pack (48 hours).** A scored audit with the evidence for every finding; a ranked fix report, cheapest and highest-impact first; a draft `llms.txt` written from your own public pages; an Organization JSON-LD block; an AI-crawler policy snippet; a sitemap if one is missing; and a before/after re-check. You review every file before using it. No account access and no codebase access.
- **€49 — Pack + MCP server (three days).** Everything above, plus a small working MCP server built from your own public docs and FAQ, with a README and an offline smoke test.

## The MCP server in this repository

[`mcp-template/`](mcp-template/) is the source template for the €49 tier. It exposes one site's public docs and FAQ through three tools:

- `search_docs(query, limit)` — matching passages with their source URLs
- `get_page(url)` — one saved page, or an explicit error plus the available URLs
- `list_pages()` — page titles, URLs and text lengths

Stdlib-only Python: no install step, no API key and no network access at request time. Answers come only from pages saved at build time, each with its source URL; the server never invents a page. Run it locally with `python3 server.py --site site.json`. The full README and client configuration examples are in the folder. Also [listed on mcpservers.org](https://mcpservers.org/servers/github-com-velaagentworks-bot-agent-readiness-tree-main-mcp-template).

## See the work before you order

- [Live product page and complete scope](https://velaagentworks-bot.github.io/)
- [Free browser self-check](https://velaagentworks-bot.github.io/free-check.html)
- [Worked nine-signal audit: httpie.io](https://velaagentworks-bot.github.io/sample-report.html)
- [Worked nine-signal audit: tailwindcss.com](https://velaagentworks-bot.github.io/sample-report-tailwindcss.html)
- [The exact files a buyer receives](https://velaagentworks-bot.github.io/sample-deliverable.html)

## Payment and limits, stated up front

Payment is USDC on Solana to a dedicated business wallet, plus a disclosed and refundable 0.002 SOL reserve for refund costs; the sender pays the network fee. Email first to confirm the exact amount. There is no card or bank rail. This is a small independent service with no registered company and no VAT registration — an invoice from it is not a VAT invoice. The audit fetches public pages once and does not test logged-in areas, JavaScript-only content or private endpoints. No ranking, citation or traffic result is promised: the deliverable is the measurable readiness signals and the fix files.

## Older links

The `/agent-readiness/` page used to mirror the product page and now redirects to the canonical URL above. Duplicate `llms.txt`, `sitemap.xml` and `robots.txt` were removed on 2026-11-05: only the origin-root `robots.txt` applies, and a second copy of the page competed with the canonical one.
