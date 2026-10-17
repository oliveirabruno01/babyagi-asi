"""Optional anonymous Parallel Search MCP tool for BASI's synchronous actions."""

import asyncio

ENDPOINT = "https://search.parallel.ai/mcp"
USER_AGENT = "babyagi-asi/parallel-search"
TIMEOUT_SECONDS = 30


async def _search(query: str, session_id: str) -> str:
    # Keep optional dependencies out of the default agent startup path.
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with asyncio.timeout(TIMEOUT_SECONDS):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        ) as client:
            async with streamable_http_client(ENDPOINT, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "web_search",
                        arguments={
                            "objective": query,
                            "search_queries": [query],
                            "session_id": session_id,
                        },
                    )

    text = "\n\n".join(block.text for block in result.content if block.type == "text")
    if result.isError:
        raise RuntimeError("Parallel search failed: " + text)
    if not text.strip():
        raise RuntimeError("Parallel search returned no text")
    return text


def search(query: str, session_id: str) -> str:
    """Return web excerpts and source links; propagate service and network errors."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a nonempty string")
    try:
        return asyncio.run(_search(query.strip(), session_id))
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional search dependencies: pip install -r requirements-parallel.txt"
        ) from exc
