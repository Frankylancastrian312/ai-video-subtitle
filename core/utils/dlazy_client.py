"""Thin HTTP client for the dlazy tool API.

Every model call in this project goes through here — LLM, ASR and TTS alike.
The endpoints mirror what the official `dlazy` CLI uses:

    POST /api/cli/tool          run a tool, returns {output}
    GET  /api/cli/tool?generateId=...   poll an async task
    POST /api/cli/upload-url    signed URL for uploading local media

Async tools answer the POST with an `output` that carries a `generateId`
instead of the result; we then poll until status is completed or failed.
"""

import mimetypes
import os
import time

import requests
from rich import print as rprint

from core.utils.config_utils import load_key

DEFAULT_BASE_URL = "https://dlazy.com"
POLL_INTERVAL = 3
DEFAULT_TIMEOUT = 1800

# The tool API gates on X-CLI-Version and answers 426 without it. We speak the
# same contract as the official CLI, so we advertise the version we were built
# against; bump it if the server ever raises MIN_SUPPORTED_CLI_VERSION past this.
CLI_VERSION = "1.2.3"


class DlazyError(Exception):
    pass


def _base_url() -> str:
    url = (load_key("dlazy.base_url") or DEFAULT_BASE_URL).strip().rstrip("/")
    return url or DEFAULT_BASE_URL


def _api_key() -> str:
    key = (load_key("dlazy.api_key") or "").strip()
    if not key or key.startswith("your"):
        raise DlazyError(
            "dlazy API key is not set. Open the sidebar settings and paste the key "
            "from https://dlazy.com/dashboard/organization/api-key"
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "X-CLI-Version": CLI_VERSION,
    }


def upload_file(path: str) -> str:
    """Upload a local file to dlazy object storage, return its public URL."""
    if not os.path.exists(path):
        raise DlazyError(f"file not found: {path}")
    filename = os.path.basename(path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    resp = requests.post(
        f"{_base_url()}/api/cli/upload-url",
        headers=_headers(),
        json={"filename": filename, "contentType": content_type},
        timeout=60,
    )
    if not resp.ok:
        raise DlazyError(f"upload-url failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()

    with open(path, "rb") as f:
        put_headers = dict(data.get("requiredHeaders") or {})
        put_headers.setdefault("Content-Type", content_type)
        put = requests.put(data["signedUrl"], data=f, headers=put_headers, timeout=600)
    if not put.ok:
        raise DlazyError(f"upload failed ({put.status_code}): {put.text[:300]}")
    return data["publicUrl"]


def _poll(generate_id: str, timeout: int):
    deadline = time.time() + timeout
    url = f"{_base_url()}/api/cli/tool?generateId={generate_id}"
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        resp = requests.get(url, headers=_headers(), timeout=60)
        if not resp.ok:
            raise DlazyError(f"poll failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        status = data.get("status")
        if status == "completed":
            return data.get("result")
        if status == "failed":
            raise DlazyError(f"task {generate_id} failed: {data.get('error')}")
    raise DlazyError(f"task {generate_id} did not finish within {timeout}s")


def run_tool(model: str, payload: dict, timeout: int = DEFAULT_TIMEOUT):
    """Run one dlazy tool and return its output, waiting out async tasks."""
    resp = requests.post(
        f"{_base_url()}/api/cli/tool",
        headers=_headers(),
        json={"model": model, "input": payload},
        timeout=timeout,
    )
    if not resp.ok:
        detail = resp.text[:500]
        raise DlazyError(f"{model} failed ({resp.status_code}): {detail}")

    output = resp.json().get("output")
    if isinstance(output, dict) and isinstance(output.get("generateId"), str):
        rprint(f"[cyan]⏳ {model} running as async task…[/cyan]")
        return _poll(output["generateId"], timeout)
    return output


def download(url: str, save_as: str) -> str:
    """Fetch a result media URL to a local path."""
    os.makedirs(os.path.dirname(os.path.abspath(save_as)), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=600)
    if not resp.ok:
        raise DlazyError(f"download failed ({resp.status_code}): {url}")
    with open(save_as, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return save_as


def check_credentials() -> bool:
    """Cheap round-trip used by the settings page to validate the key."""
    try:
        resp = requests.get(
            f"{_base_url()}/api/cli/tool/manifest", headers=_headers(), timeout=30
        )
        return resp.ok
    except Exception:
        return False


# ---------------------------------------------------------------------------
# manifest — the server is the source of truth for tool names and voice lists,
# so the settings page reads them live instead of hardcoding a list that goes
# stale as soon as dlazy adds a model or a voice.
# ---------------------------------------------------------------------------

_MANIFEST_CACHE = {}


def get_manifest(force: bool = False) -> dict:
    if not force and "data" in _MANIFEST_CACHE:
        return _MANIFEST_CACHE["data"]
    resp = requests.get(
        f"{_base_url()}/api/cli/tool/manifest", headers=_headers(), timeout=60
    )
    if not resp.ok:
        raise DlazyError(f"manifest failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    _MANIFEST_CACHE["data"] = data
    return data


def _tool(model: str):
    for t in get_manifest().get("tools", []):
        if t.get("cli_name") == model:
            return t
    return None


def list_voices(model: str):
    """Return (voice_ids, default_voice) for a TTS model, straight from the manifest."""
    tool = _tool(model)
    if not tool:
        return [], ""
    props = (tool.get("inputJsonSchema") or {}).get("properties") or {}
    field = props.get("voice") or props.get("voiceId") or {}
    return list(field.get("enum") or []), field.get("default") or ""


def available_models(cli_names) -> list:
    """Filter a candidate model list down to what this account can actually run."""
    try:
        live = {t.get("cli_name") for t in get_manifest().get("tools", [])}
    except Exception:
        return list(cli_names)
    return [n for n in cli_names if n in live] or list(cli_names)
