"""Talk to the opencode-go chat API (OpenAI-compatible wire format).

This file is the ONLY place that touches the raw wire dicts. Everything else
(loop.py, the engine) sees the flat replies returned by `_reply_from`.

Request we send:
    {
      "model": "qwen3.8-flash",
      "messages": [{"role": "user"/"assistant"/"tool", "content": ...}, ...],
      "tools": [...]            # optional
    }

Response we get (we only use choices[0]):
    {
      "choices": [
        {
          "message": {
            "content": "text, or \"\" when a tool is called",
            "tool_calls": [                    # optional
              {
                "id": "call_...",            # match this on the tool result
                "type": "function",
                "function": {
                  "name": "add",
                  "arguments": "{\"a\": 2, \"b\": 3}"   # JSON *string*, not a dict
                }
              }
            ]
          }
        }
      ]
    }

Peel one layer at a time, left to right:
    data["choices"]           -> list
    data["choices"][0]        -> dict
    ...["message"]            -> dict
    ...["content"]            -> str
"""

import json
import urllib.request
import uuid
import pathlib

URL = "https://opencode.ai/zen/go/v1/chat/completions"

ADD_TOOL = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two integers",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    },
}


def _api_key() -> str:
    auth = pathlib.Path.home() / ".local/share/opencode/auth.json"
    return json.loads(auth.read_text())["opencode-go"]["key"]


def _chat(
    messages: list[dict],
    model: str = "qwen3.8-flash",
    tools: list[dict] | None = None,
) -> dict:
    key = _api_key()
    body = {"model": model, "messages": messages}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "grapes/0.1",
            "x-opencode-session": str(uuid.uuid4()),
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]


def ask(messages: list[dict], model: str = "qwen3.8-flash") -> str:
    return _chat(messages, model)["content"]


def _reply_from(message: dict) -> dict:
    calls = message.get("tool_calls")
    if not calls:
        return {"type": "answer", "content": message["content"]}

    call = calls[0]
    return {
        "type": "tool",
        "id": call["id"],
        "name": call["function"]["name"],
        "args": json.loads(call["function"]["arguments"]),
    }


def model(messages: list[dict]) -> dict:
    return _reply_from(_chat(messages, tools=[ADD_TOOL]))
