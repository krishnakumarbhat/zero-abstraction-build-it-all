import json
import os
import subprocess
import sys
import argparse
from pathlib import Path
import urllib.request
import urllib.error


API_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def load_env_file(path: str = ".env"):
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def has_real_key(name: str) -> bool:
    value = (os.environ.get(name) or "").strip()
    if not value:
        return False
    lowered = value.lower()
    if "your_" in lowered or "replace_me" in lowered or "placeholder" in lowered:
        return False
    return True


def tool_read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def tool_search_web(query: str) -> str:
    return f"search_web not implemented in MVP. query={query}"


def tool_run_bash(command: str) -> str:
    proc = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
    )
    return proc.stdout


TOOLS = {
    "read_file": tool_read_file,
    "search_web": tool_search_web,
    "run_bash": tool_run_bash,
}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local text file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for info",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Run a shell command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def call_llm(messages):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required")

    payload = {
        "model": "gpt-4.1-mini",
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "tool_choice": "auto",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_gemini(prompt: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not has_real_key("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is required")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are a helpful coding agent. "
                            "Give concise practical answers.\n\n"
                            f"User prompt: {prompt}"
                        )
                    }
                ]
            }
        ]
    }

    configured = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    candidate_models = [
        configured,
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    last_error = ""
    data = None
    for model in candidate_models:
        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code == 404:
                last_error = f"{model}: not found"
                continue
            raise RuntimeError(f"Gemini HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini connection error: {e}")

    if data is None:
        raise RuntimeError(f"No compatible Gemini model found. Last error: {last_error}")

    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    return "\n".join([t for t in text_chunks if t]).strip()


def run_mock_agent(user_prompt: str):
    low = user_prompt.lower()
    if "summarize" in low and "readme" in low:
        try:
            content = tool_read_file("README.md")
            lines = [line.strip() for line in content.splitlines() if line.strip()][:5]
            print("[mock-agent] Summary:")
            for line in lines:
                print(f"- {line}")
            return
        except Exception:
            pass
    print("[mock-agent] No live key detected. Set GEMINI_API_KEY (or OPENAI_API_KEY) for live mode.")
    print(f"[mock-agent] Prompt received: {user_prompt}")


def run_agent(user_prompt: str, force_mock: bool = False):
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()

    if force_mock:
        run_mock_agent(user_prompt)
        return

    if provider == "mock":
        run_mock_agent(user_prompt)
        return

    if provider == "gemini":
        if not has_real_key("GEMINI_API_KEY"):
            run_mock_agent(user_prompt)
            return
        try:
            output = call_gemini(user_prompt)
            print(output)
        except Exception as e:
            print(f"[agent] Gemini call failed: {e}")
            run_mock_agent(user_prompt)
        return

    if provider != "openai":
        print(f"[agent] Unknown LLM_PROVIDER={provider}; falling back to mock mode")
        run_mock_agent(user_prompt)
        return

    if not has_real_key("OPENAI_API_KEY"):
        run_mock_agent(user_prompt)
        return

    messages = [
        {"role": "system", "content": "You are a helpful coding agent."},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(8):
        response = call_llm(messages)
        msg = response["choices"][0]["message"]

        tool_calls = msg.get("tool_calls", [])
        content = msg.get("content")
        messages.append(msg)

        if not tool_calls:
            print(content or "")
            return

        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"].get("arguments", "{}"))
            fn = TOOLS.get(name)
            if not fn:
                result = f"unknown tool: {name}"
            else:
                try:
                    result = fn(**args)
                except Exception as e:
                    result = f"tool error: {e}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )

    print("agent stopped after max steps")


def main():
    load_env_file(".env")

    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="+", help="Prompt for the agent")
    parser.add_argument("--mock", action="store_true", help="Force local mock mode (no API call)")
    args = parser.parse_args()

    prompt = " ".join(args.prompt)
    run_agent(prompt, force_mock=args.mock)


if __name__ == "__main__":
    main()
