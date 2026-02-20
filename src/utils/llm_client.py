import json
import os
import urllib.request
import urllib.error
from .config import AUTH_PROFILES_PATH
from .logger import setup_logger

logger = setup_logger("llm_client")

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 4096


def _get_api_key():
    # Check env var first
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key

    # Fallback to OpenClaw auth-profiles
    if AUTH_PROFILES_PATH.exists():
        with open(AUTH_PROFILES_PATH, "r") as f:
            profiles = json.load(f)

        # Try anthropic:manual first (last-good)
        manual = profiles.get("profiles", {}).get("anthropic:manual", {})
        key = manual.get("token") or manual.get("key")
        if key:
            return key

        # Try anthropic:default
        default = profiles.get("profiles", {}).get("anthropic:default", {})
        key = default.get("key") or default.get("token")
        if key:
            return key

    raise RuntimeError(
        "No Anthropic API key found. Set ANTHROPIC_API_KEY env var or "
        "configure OpenClaw auth-profiles.json"
    )


def call_claude(prompt, system=None, model=DEFAULT_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS, temperature=0.3):
    api_key = _get_api_key()

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Anthropic API error %d: %s" % (e.code, error_body)
        )
    except urllib.error.URLError as e:
        raise RuntimeError("Network error calling Anthropic API: %s" % e)

    content_blocks = result.get("content", [])
    text_parts = [
        block["text"]
        for block in content_blocks
        if block.get("type") == "text"
    ]
    return "\n".join(text_parts)
