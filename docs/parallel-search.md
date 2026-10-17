# Optional Parallel web search

BASI can use [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
to research current information and return web excerpts with source links. The
anonymous endpoint uses Fast mode and needs no Parallel account or API key. It is
free for light use, with service rate limits.

The tool is disabled by default. Existing SerpAPI settings and tools are preserved.

1. Use Python 3.11 or newer and install the project and optional dependencies from
   the repository root:

   ```bash
   pip install -r requirements.txt -r requirements-parallel.txt
   ```

2. In `src/tools/config.json`, set `get_parallel_search_result.enabled` to `true`.
   Leave other entries as they are. To use only Parallel for web search, also set
   `get_serp_query.enabled` to `false`.

3. Configure your OpenAI key and tasks in `.env` as usual. Run BASI from `src` so
   its relative tool and memory paths resolve, with the repository on Python's
   import path. On Linux or macOS, from the repository root:

   ```bash
   cd src
   PYTHONPATH=.. python main.py
   ```

   A task can ask BASI to use `self.get_parallel_search_result` to research a topic
   and summarize the sources. Generated actions can call it like this:

   ```python
   def action(self):
       return self.get_parallel_search_result("Python latest release notes")
   ```

   The result is a string of web excerpts with source links. The agent reuses a
   search conversation ID for related calls. OpenAI still powers BASI's reasoning.

For a search-only check without starting the agent or configuring OpenAI, run
this from the repository root after installing the optional dependencies:

```bash
python - <<'PY'
from uuid import uuid4
from src.tools.parallel_search import search

print(search("Python latest release notes", str(uuid4())))
PY
```

Each search has a 30-second deadline. Connection failures, service errors
(including rate limits), and empty responses raise exceptions rather than
returning fabricated results or switching to SerpAPI. Interrupting the action
cancels its request. Disable the config entry and restart BASI to remove the tool
from the agent's available-tool prompt.

The optional dependencies are separate from the default installation. For Docker,
install `requirements-parallel.txt` in your image before enabling the tool.
