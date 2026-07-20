#!/usr/bin/env python3
"""Lightweight AI simulator — OpenAI- and Ollama-compatible fake API."""

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

PORT = 11435
MODELS = [{"id": "simulator:latest", "name": "simulator:latest", "size": 0}]


def _echo_text(messages: list[dict[str, Any]]) -> str:
    last = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    snippet = (last[:200] + "…") if len(last) > 200 else last
    return f"[AI Simulator] {snippet}" if snippet else "[AI Simulator] Hello!"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, chunks: list[Any]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _send_ndjson(self, chunks: list[Any]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write((json.dumps(chunk) + "\n").encode())
        self.wfile.flush()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/v1/models", "/v1/models/"):
            self._send_json(
                {
                    "object": "list",
                    "data": [
                        {"id": m["id"], "object": "model", "created": 1700000000, "owned_by": "simulator"}
                        for m in MODELS
                    ],
                }
            )
        elif path == "/api/tags":
            self._send_json(
                {
                    "models": [
                        {"name": m["name"], "model": m["name"], "size": m["size"], "details": {"family": "simulator"}}
                        for m in MODELS
                    ]
                }
            )
        elif path in ("/", "/health", "/healthz"):
            self._send_json({"status": "ok", "simulator": True})
        else:
            self._send_json({"error": {"message": "not found", "type": "not_found"}}, 404)

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        body = self._read_json()
        if path == "/v1/chat/completions":
            self._openai_chat(body)
        elif path == "/v1/completions":
            self._openai_completion(body)
        elif path == "/api/chat":
            self._ollama_chat(body)
        elif path == "/api/generate":
            self._ollama_generate(body)
        else:
            self._send_json({"error": {"message": "not found", "type": "not_found"}}, 404)

    def _openai_chat(self, body: dict[str, Any]) -> None:
        text = _echo_text(body.get("messages", []))
        model = body.get("model", "simulator:latest")
        cid = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        now = int(time.time())
        if body.get("stream"):
            self._send_sse(
                [
                    {
                        "id": cid,
                        "object": "chat.completion.chunk",
                        "created": now,
                        "model": model,
                        "choices": [
                            {"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}
                        ],
                    },
                    {
                        "id": cid,
                        "object": "chat.completion.chunk",
                        "created": now,
                        "model": model,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    },
                ]
            )
        else:
            self._send_json(
                {
                    "id": cid,
                    "object": "chat.completion",
                    "created": now,
                    "model": model,
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": len(text.split()),
                        "total_tokens": 10 + len(text.split()),
                    },
                }
            )

    def _openai_completion(self, body: dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        text = f"[AI Simulator] {(prompt[:200] + '…') if len(prompt) > 200 else prompt}"
        model = body.get("model", "simulator:latest")
        self._send_json(
            {
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{"text": text, "index": 0, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": len(text.split()),
                    "total_tokens": 10 + len(text.split()),
                },
            }
        )

    def _ollama_chat(self, body: dict[str, Any]) -> None:
        text = _echo_text(body.get("messages", []))
        model = body.get("model", "simulator:latest")
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        final = {
            "model": model,
            "created_at": ts,
            "message": {"role": "assistant", "content": text},
            "done": True,
            "done_reason": "stop",
            "total_duration": 1000000,
            "prompt_eval_count": 10,
            "eval_count": len(text.split()),
        }
        if body.get("stream", True):
            self._send_ndjson(
                [
                    {
                        "model": model,
                        "created_at": ts,
                        "message": {"role": "assistant", "content": text},
                        "done": False,
                    },
                    final,
                ]
            )
        else:
            self._send_json(final)

    def _ollama_generate(self, body: dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        text = f"[AI Simulator] {(prompt[:200] + '…') if len(prompt) > 200 else prompt}"
        model = body.get("model", "simulator:latest")
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        final = {
            "model": model,
            "created_at": ts,
            "response": text,
            "done": True,
            "done_reason": "stop",
            "total_duration": 1000000,
            "prompt_eval_count": 10,
            "eval_count": len(text.split()),
        }
        if body.get("stream", True):
            self._send_ndjson(
                [
                    {"model": model, "created_at": ts, "response": text, "done": False},
                    final,
                ]
            )
        else:
            self._send_json(final)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"AI Simulator running on :{PORT}", flush=True)
    server.serve_forever()
