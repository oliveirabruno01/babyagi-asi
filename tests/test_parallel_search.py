"""Exercise BASI dispatch through the real MCP SDK with HTTP response fixtures."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import httpx
import mcp  # Load SDK annotations before patching the HTTP client factory.

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
os.environ["TASKS_LIST"] = "[]"
os.environ["OPENAI_API_KEY"] = ""
os.environ["SERP_API_KEY"] = ""
os.environ["PINECONE_API_KEY"] = ""

# BASI resolves its existing prompt and memory paths relative to src.
os.chdir(ROOT / "src")
import babyagi
import prompts
from tools import parallel_search


class ParallelSearchTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.mode = "json"
        self.cancelled = False
        self.started = asyncio.Event()
        self.real_client = httpx.AsyncClient

    async def respond(self, request):
        self.requests.append(request)
        message = json.loads(request.content)
        method = message["method"]
        if "id" not in message:
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
        else:
            self.assertEqual(method, "tools/call")
            self.assertEqual(message["params"]["name"], "web_search")
            if self.mode == "network_error":
                raise httpx.ConnectError("connection failed", request=request)
            if self.mode == "blocked":
                self.started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    self.cancelled = True
            result = {
                "content": [{"type": "text", "text": "Python release notes https://www.python.org/downloads/"}],
                "isError": False,
            }
            if self.mode == "tool_error":
                result.update(content=[{"type": "text", "text": "Service rate limit"}], isError=True)
            elif self.mode == "empty":
                result["content"] = []
        reply = {"jsonrpc": "2.0", "id": message["id"], "result": result}
        if self.mode == "sse":
            return httpx.Response(200, headers={"content-type": "text/event-stream"},
                                  text="event: message\ndata: " + json.dumps(reply) + "\n\n")
        return httpx.Response(200, json=reply)

    def client(self, **kwargs):
        return self.real_client(transport=httpx.MockTransport(self.respond), **kwargs)

    def check_requests(self):
        self.assertTrue(self.requests)
        for request in self.requests:
            self.assertEqual(str(request.url), parallel_search.ENDPOINT)
            self.assertEqual(request.headers["User-Agent"], parallel_search.USER_AGENT)
            self.assertNotIn("authorization", request.headers)
        calls = [json.loads(r.content)["params"]["arguments"] for r in self.requests
                 if json.loads(r.content)["method"] == "tools/call"]
        self.assertTrue(calls)
        for args in calls:
            self.assertEqual(args["objective"], "Python latest release notes")
            self.assertEqual(args["search_queries"], ["Python latest release notes"])
            self.assertTrue(args["session_id"])
        return calls

    def test_agent_prompt_and_action_dispatch_json_and_sse(self):
        self.assertFalse(prompts.tools["get_parallel_search_result"]["enabled"])
        before = prompts.get_available_tools([])
        self.assertNotIn("self.get_parallel_search_result(", before)
        with patch.dict(prompts.tools["get_parallel_search_result"], enabled=True):
            self.assertIn("self.get_parallel_search_result(", prompts.get_available_tools([]))
            agent = babyagi.AutonomousAgent("Research Python releases")
            original_serp = agent.get_serp_query_result
            with patch.object(httpx, "AsyncClient", self.client), patch.object(
                babyagi, "openai_call", side_effect=AssertionError("Unexpected LLM repair")
            ):
                for self.mode in ("json", "sse"):
                    result, _, _ = agent.repl_agent(
                        "Research Python releases",
                        "answer:\ndef action(self):\n    return self.get_parallel_search_result('Python latest release notes')",
                    )
                    self.assertIn("https://www.python.org/downloads/", result)
                    self.assertIs(agent.get_serp_query_result, original_serp)
        calls = self.check_requests()
        self.assertEqual(calls[0]["session_id"], calls[1]["session_id"])

    def test_disabled_tool_cannot_make_a_request(self):
        with patch.object(httpx, "AsyncClient", side_effect=AssertionError("unexpected network")):
            with self.assertRaisesRegex(RuntimeError, "Enable get_parallel_search_result"):
                babyagi.AutonomousAgent("Research").get_parallel_search_result("query")

    def test_errors_and_empty_results_are_not_success(self):
        with patch.object(httpx, "AsyncClient", self.client):
            for self.mode, error in (("tool_error", "Service rate limit"), ("empty", "no text")):
                with self.subTest(mode=self.mode), self.assertRaisesRegex(RuntimeError, error):
                    parallel_search.search("Python latest release notes", "stable-test-conversation")
        self.check_requests()

    def test_network_failure_propagates(self):
        self.mode = "network_error"
        with patch.object(httpx, "AsyncClient", self.client):
            with self.assertRaises(BaseExceptionGroup) as caught:
                parallel_search.search("Python latest release notes", "stable-test-conversation")
        def leaves(exc):
            return [leaf for child in exc.exceptions for leaf in leaves(child)] if isinstance(exc, BaseExceptionGroup) else [exc]
        self.assertTrue(any(isinstance(e, httpx.ConnectError) for e in leaves(caught.exception)))
        self.check_requests()

    def test_deadline_cancels_inflight_request(self):
        self.mode = "blocked"
        with patch.object(httpx, "AsyncClient", self.client), patch.object(parallel_search, "TIMEOUT_SECONDS", 0.05):
            with self.assertRaises(TimeoutError):
                parallel_search.search("Python latest release notes", "stable-test-conversation")
        self.assertTrue(self.cancelled)
        self.check_requests()

    def test_cancellation_closes_inflight_request(self):
        self.mode = "blocked"
        async def cancel():
            task = asyncio.create_task(parallel_search._search("Python latest release notes", "stable-test-conversation"))
            await asyncio.wait_for(self.started.wait(), timeout=2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        with patch.object(httpx, "AsyncClient", self.client):
            asyncio.run(cancel())
        self.assertTrue(self.cancelled)
        self.check_requests()

    def test_invalid_query_fails_before_network(self):
        with patch.object(httpx, "AsyncClient", side_effect=AssertionError("unexpected network")):
            for query in ("", " ", None):
                with self.assertRaises(ValueError):
                    parallel_search.search(query, "stable-test-conversation")

    def test_default_startup_needs_no_optional_dependencies(self):
        script = '''
import importlib.abc
import sys
class NoOptionalDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('mcp', 'httpx'):
            raise ImportError('Optional dependency unavailable')
sys.meta_path.insert(0, NoOptionalDependencies())
import babyagi, prompts
agent = babyagi.AutonomousAgent('Research')
assert 'mcp' not in sys.modules and 'httpx' not in sys.modules
prompts.tools['get_parallel_search_result']['enabled'] = True
try:
    agent.get_parallel_search_result('Python latest release notes')
except RuntimeError as exc:
    assert 'requirements-parallel.txt' in str(exc)
else:
    raise AssertionError('Missing dependency should give setup guidance')
'''
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / "src")]))
        result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
