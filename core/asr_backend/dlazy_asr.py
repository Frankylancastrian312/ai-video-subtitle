"""Speech-to-text through dlazy.

Replaces the former local WhisperX / 302.ai / ElevenLabs backends. dlazy answers
with a flat word list, while the rest of this pipeline expects the WhisperX
shape, so we re-wrap it:

    dlazy   {"texts": [...], "data": {"words": [{text, start, end, type}, ...]}}
    here    {"segments": [{start, end, text, words: [{word, start, end}, ...]}]}

`process_transcription` only ever flattens `segments[].words[]` (it reads
`speaker_id` off the segment), so emitting one segment per audio chunk keeps
every word timing intact.
"""

import json
import os
import time

import librosa
import soundfile as sf
from rich import print as rprint

from core.utils import *
from core.utils.dlazy_client import DlazyError, run_tool, upload_file
from core.utils.models import *

OUTPUT_LOG_DIR = "output/log"
TMP_DIR = "output/tmp"
# Both dlazy ASR tools accept zh or en only; anything else is sent as en.
SUPPORTED_LANGS = {"zh", "en"}


def _to_segments(output: dict, offset: float) -> dict:
    data = (output or {}).get("data") or {}
    raw_words = data.get("words") or []

    words = []
    for w in raw_words:
        if w.get("type") not in (None, "word"):
            continue  # skip spacing / audio_event entries
        text = (w.get("text") or "").strip()
        if not text:
            continue
        start = w.get("start")
        end = w.get("end")
        item = {"word": text}
        if start is not None:
            item["start"] = float(start) + offset
        if end is not None:
            item["end"] = float(end) + offset
        words.append(item)

    texts = (output or {}).get("texts") or []
    full_text = texts[0] if texts else " ".join(w["word"] for w in words)

    if not words:
        return {"segments": []}

    return {"segments": [{
        "start": words[0].get("start", offset),
        "end": words[-1].get("end", offset),
        "text": full_text,
        "words": words,
    }]}


def transcribe_audio(raw_audio_path: str, vocal_audio_path: str, start: float = None, end: float = None):
    os.makedirs(OUTPUT_LOG_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    log_file = f"{OUTPUT_LOG_DIR}/dlazy_asr_{start}_{end}.json"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    lang = load_key("asr.language")
    if lang not in SUPPORTED_LANGS:
        rprint(f"[yellow]⚠️ dlazy ASR supports zh/en only, falling back to en for '{lang}'[/yellow]")
        lang = "en"

    y, sr = librosa.load(vocal_audio_path, sr=16000)
    duration = len(y) / sr
    if start is None or end is None:
        start, end = 0, duration

    slice_path = os.path.join(TMP_DIR, f"asr_slice_{int(start)}_{int(end)}.wav")
    sf.write(slice_path, y[int(start * sr):int(end * sr)], sr, format="WAV", subtype="PCM_16")

    model = load_key("dlazy.asr_model")
    rprint(f"[cyan]🎤 Transcribing with dlazy <{model}> language <{lang}> ...[/cyan]")
    t0 = time.time()

    audio_url = upload_file(slice_path)
    output = run_tool(model, {
        "audio_url": audio_url,
        "language_code": lang,
        "diarize": False,
    })
    result = _to_segments(output, offset=start)
    if not result["segments"]:
        raise DlazyError(f"{model} returned no words for {slice_path}")

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    try:
        os.remove(slice_path)
    except OSError:
        pass

    rprint(f"[green]✓ Transcription completed in {time.time() - t0:.2f} seconds[/green]")
    return result


if __name__ == "__main__":
    rprint(transcribe_audio(_RAW_AUDIO_FILE, _RAW_AUDIO_FILE))
