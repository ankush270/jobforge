"""JobForge MCP (Model Context Protocol) Server.

Exposes JobForge tools to Claude Desktop, Cursor, and any MCP-compatible AI client.
Enables AI agents to search jobs, clip job postings, tailor resumes with STAR bullets,
lookup salary benchmarks, and generate application answers.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

import httpx

API_BASE = os.environ.get("JOBFORGE_API_URL", "http://localhost:8000/api")
TOKEN = os.environ.get("JOBFORGE_API_TOKEN", "")

HEADERS = {
    "Content-Type": "application/json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}

# ── Tool Definitions ───────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_jobs",
        "description": "Search jobs in JobForge database by title, keyword, location, or platform.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Search keyword or role title"},
                "platform": {"type": "string", "description": "linkedin, indeed, greenhouse, lever, etc."},
                "location": {"type": "string", "description": "City, country or remote"},
                "page": {"type": "integer", "default": 1},
            },
        },
    },
    {
        "name": "clip_job",
        "description": "Clip / save a job from any webpage or LinkedIn/Indeed URL into JobForge.",
        "inputSchema": {
            "type": "object",
            "required": ["title", "company_name", "description"],
            "properties": {
                "title": {"type": "string", "description": "Job title"},
                "company_name": {"type": "string", "description": "Company name"},
                "description": {"type": "string", "description": "Job description text"},
                "source_url": {"type": "string", "description": "Link to the job posting"},
                "location": {"type": "string", "description": "Job location"},
            },
        },
    },
    {
        "name": "tailor_resume",
        "description": "Tailor a resume for a job using STAR framework and anti-hallucination verification.",
        "inputSchema": {
            "type": "object",
            "required": ["resume_id", "job_id"],
            "properties": {
                "resume_id": {"type": "string", "description": "UUID of master resume"},
                "job_id": {"type": "string", "description": "UUID of target job"},
            },
        },
    },
    {
        "name": "get_salary_benchmark",
        "description": "Look up market compensation percentiles (P25, P50, P75, P90) and calculate leverage.",
        "inputSchema": {
            "type": "object",
            "required": ["role"],
            "properties": {
                "role": {"type": "string", "description": "Target job title, e.g. 'Senior Backend Engineer'"},
                "experience_yrs": {"type": "integer", "description": "Years of experience"},
                "currency": {"type": "string", "default": "INR"},
                "location": {"type": "string", "default": "India"},
            },
        },
    },
    {
        "name": "generate_cover_letter",
        "description": "Generate a research-backed 3-paragraph cover letter or 75-word recruiter cold email.",
        "inputSchema": {
            "type": "object",
            "required": ["job_id"],
            "properties": {
                "job_id": {"type": "string", "description": "Target job ID"},
                "mode": {"type": "string", "enum": ["cover_letter", "email"], "default": "cover_letter"},
            },
        },
    },
]


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    """Execute tool against JobForge backend API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        if name == "search_jobs":
            params = {k: v for k, v in arguments.items() if v is not None}
            res = await client.get(f"{API_BASE}/jobs/", params=params, headers=HEADERS)
            return res.json()

        elif name == "clip_job":
            res = await client.post(f"{API_BASE}/jobs/clip", json=arguments, headers=HEADERS)
            return res.json()

        elif name == "tailor_resume":
            res = await client.post(f"{API_BASE}/evaluations/tailor", json=arguments, headers=HEADERS)
            return res.json()

        elif name == "get_salary_benchmark":
            res = await client.get(f"{API_BASE}/salaries/benchmark", params=arguments, headers=HEADERS)
            return res.json()

        elif name == "generate_cover_letter":
            res = await client.post(f"{API_BASE}/cover-letters/generate", json=arguments, headers=HEADERS)
            return res.json()

        else:
            raise ValueError(f"Unknown tool: {name}")


async def main():
    """Stdio JSON-RPC loop for Model Context Protocol (MCP)."""
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "jobforge-mcp", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                },
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            try:
                result_data = await handle_tool_call(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}]
                    },
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)},
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
