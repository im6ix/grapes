from grapes.agent import _reply_from


def test_answer():
    message = {"content": "paris"}
    assert _reply_from(message) == {"type": "answer", "content": "paris"}


def test_tool_call():
    message = {
        "content": "",
        "tool_calls": [
            {
                "id": "call_abc",
                "type": "function",
                "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
            }
        ],
    }
    assert _reply_from(message) == {
        "type": "tool",
        "id": "call_abc",
        "name": "add",
        "args": {"a": 2, "b": 3},
    }
