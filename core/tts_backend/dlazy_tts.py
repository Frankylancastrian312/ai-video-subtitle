"""Text-to-speech through dlazy.

Replaces the former Azure / OpenAI / Fish / SiliconFlow / Edge / GPT-SoVITS /
F5-TTS backends. Each dlazy TTS tool declares every field as required, so the
payload is built in full per model rather than relying on server-side defaults.

Voice cloning is intentionally absent: dlazy exposes no cloning tool, so dubbing
here is preset-voice only and the reference-audio path is not used.
"""

import os

from pydub import AudioSegment
from rich import print as rprint

from core.utils import *
from core.utils.dlazy_client import DlazyError, download, run_tool

TMP_DIR = "output/tmp"

# Fallback voice per model, used when dlazy.tts_voice is left blank.
DEFAULT_VOICES = {
    "qwen-tts": "Cherry",
    "doubao-tts": "zh_female_shuangkuaisisi_uranus_bigtts",
    "elevenlabs-tts": "21m00Tcm4TlvDq8ikWAM",
}


def _build_payload(model: str, text: str) -> dict:
    voice = (load_key("dlazy.tts_voice") or "").strip() or DEFAULT_VOICES.get(model, "")
    lang = load_key("asr.language")

    if model == "qwen-tts":
        return {
            "prompt": text,
            "generation_mode": "system",
            "voice": voice,
            "voice_prompt": "",
            "language_type": "Auto",
            "promptRefs": [],
        }
    if model == "doubao-tts":
        return {
            "prompt": text,
            "voice_language": "zh-cn" if lang == "zh" else "en",
            "voiceId": voice,
            "speed_ratio": "1.0",
            "promptRefs": [],
        }
    if model == "elevenlabs-tts":
        return {
            "prompt": text,
            "use_custom_voice": False,
            "voice_language": "multilingual",
            "voiceId": voice,
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0,
            "promptRefs": [],
        }
    raise DlazyError(f"unsupported dlazy TTS model: {model}")


def dlazy_tts(text: str, save_as: str):
    model = load_key("dlazy.tts_model")
    output = run_tool(model, _build_payload(model, text))

    urls = (output or {}).get("urls") or []
    if not urls:
        raise DlazyError(f"{model} returned no audio url")

    os.makedirs(TMP_DIR, exist_ok=True)
    raw = os.path.join(TMP_DIR, f"tts_{os.path.basename(save_as)}.download")
    download(urls[0], raw)

    # The pipeline downstream (pydub merge, duration probing) assumes wav.
    AudioSegment.from_file(raw).export(save_as, format="wav")
    try:
        os.remove(raw)
    except OSError:
        pass
    return save_as


if __name__ == "__main__":
    dlazy_tts("这是一段配音测试。", "output/tmp/tts_demo.wav")
    rprint("[green]✓ saved output/tmp/tts_demo.wav[/green]")
