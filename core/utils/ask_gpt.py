import json
import os
from threading import Lock

import json_repair
from rich import print as rprint

from core.utils.config_utils import load_key
from core.utils.decorator import except_handler
from core.utils.dlazy_client import run_tool

# ------------
# cache gpt response
# ------------

LOCK = Lock()
GPT_LOG_FOLDER = 'output/gpt_log'

def _save_cache(model, prompt, resp_content, resp_type, resp, message=None, log_title="default"):
    with LOCK:
        logs = []
        file = os.path.join(GPT_LOG_FOLDER, f"{log_title}.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        logs.append({"model": model, "prompt": prompt, "resp_content": resp_content, "resp_type": resp_type, "resp": resp, "message": message})
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

def _load_cache(prompt, resp_type, log_title):
    with LOCK:
        file = os.path.join(GPT_LOG_FOLDER, f"{log_title}.json")
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                for item in json.load(f):
                    if item["prompt"] == prompt and item["resp_type"] == resp_type:
                        return item["resp"]
        return False

# ------------
# ask gpt once
# ------------

@except_handler("LLM request failed", retry=5)
def ask_gpt(prompt, resp_type=None, valid_def=None, log_title="default"):
    """Run one LLM turn through dlazy.

    dlazy text tools take a single `prompt` string and answer with
    `{"texts": ["..."]}` — there is no messages array and no
    `response_format: json_object`, so JSON replies are recovered with
    json_repair, which this pipeline already relied on as a fallback.
    """
    # check cache
    cached = _load_cache(prompt, resp_type, log_title)
    if cached:
        rprint("use cache response")
        return cached

    model = load_key("dlazy.llm_model")

    if resp_type == "json":
        prompt = f"{prompt}\n\nRespond with valid JSON only. No markdown fences, no commentary."

    output = run_tool(model, {
        "prompt": prompt,
        "images": [],
        "videos": [],
        "promptRefs": [],
    })

    texts = (output or {}).get("texts") or []
    resp_content = texts[0] if texts else ""
    if not resp_content:
        raise ValueError(f"❎ {model} returned an empty response")

    if resp_type == "json":
        resp = json_repair.loads(resp_content)
    else:
        resp = resp_content

    # check if the response format is valid
    if valid_def:
        valid_resp = valid_def(resp)
        if valid_resp['status'] != 'success':
            _save_cache(model, prompt, resp_content, resp_type, resp, log_title="error", message=valid_resp['message'])
            raise ValueError(f"❎ API response error: {valid_resp['message']}")

    _save_cache(model, prompt, resp_content, resp_type, resp, log_title=log_title)
    return resp


if __name__ == '__main__':
    result = ask_gpt("""test respond ```json\n{\"code\": 200, \"message\": \"success\"}\n```""", resp_type="json")
    rprint(f"Test json output result: {result}")
