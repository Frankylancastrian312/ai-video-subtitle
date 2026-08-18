# NOTICE

**ai-video-subtitle** is a derivative work of the open-source project
**VideoLingo**.

- Upstream: https://github.com/Huanshere/VideoLingo
- Upstream license: Apache License 2.0 (full text in [LICENSE](LICENSE))
- Upstream author: Huanyu (Huanshere)

The processing pipeline — word-level transcription, NLP + LLM sentence
splitting, terminology extraction, multi-step reflective translation, subtitle
cutting and alignment, burn-in, and the dubbing timeline — was all designed and
built upstream. This fork replaces the model layer with the
[dlazy](https://dlazy.com) API and drops the branding and the assets that are
not ours to redistribute.

As required by Apache-2.0 §4(b), the modifications are listed below.

## Removed

| Content | Reason |
| --- | --- |
| `core/asr_backend/whisperX_local.py`, the local Whisper weights and the whole PyTorch/CUDA install path | Local model — replaced by dlazy speech-to-text |
| `core/asr_backend/demucs_vl.py` (Demucs vocal separation) | Local model with no dlazy equivalent; transcription now runs on the raw track |
| `core/asr_backend/whisperX_302.py`, `elevenlabs_asr.py` | Third-party remote ASR — replaced by dlazy |
| 9 TTS backends (Azure, OpenAI, Fish, SiliconFlow FishTTS, SiliconFlow CosyVoice2, Edge, GPT-SoVITS, 302.ai F5-TTS, custom) | Third-party remote/local TTS — replaced by dlazy |
| `core/_9_refer_audio.py` and the reference-audio cloning path | Depended on Demucs, and dlazy exposes no voice-cloning tool |
| `docs/` (upstream documentation site, logo.png / logo.svg) | Upstream's own branding and marketing site |
| `translations/README.*.md` | Upstream READMEs, tied to their site, badges and support channels |
| `VideoLingo_colab.ipynb` | Existed to rent a free GPU for the local Whisper model |
| In-app links to upstream's free QA agent and SaaS site | Upstream's own services, not ours to route users to |

## Changed

| File | Change |
| --- | --- |
| `core/utils/dlazy_client.py` | **New.** HTTP client for the dlazy tool API — run tool, poll async tasks, upload media, read the tool manifest |
| `core/utils/ask_gpt.py` | Rewritten off the OpenAI SDK. dlazy text tools take a single `prompt` and have no `response_format: json_object`, so JSON replies are recovered with `json_repair`, which the pipeline already used as a fallback |
| `core/asr_backend/dlazy_asr.py` | **New.** Re-wraps dlazy's flat word list into the WhisperX `segments[].words[]` shape the pipeline expects |
| `core/tts_backend/dlazy_tts.py` | **New.** Preset-voice dubbing through `qwen-tts` / `doubao-tts` / `elevenlabs-tts` |
| `core/_2_asr.py`, `core/tts_backend/tts_main.py` | Backend routing collapsed to the single dlazy path; the Demucs branch is gone |
| `config.yaml` | Every third-party key replaced by one `dlazy` block; the `whisper.*` namespace renamed to `asr.*` since Whisper is no longer involved |
| `core/st_utils/sidebar_setting.py` | Settings page now configures a dlazy API key plus LLM / ASR / TTS model pickers. Model and voice lists are read live from the dlazy manifest rather than hardcoded |
| `translations/*.json` | 14 new UI strings across 7 languages; 27 strings belonging to removed backends deleted |
| `Dockerfile` | Rebuilt on `python:3.10-slim`; the `nvidia/cuda` base image, PyTorch install and CUDA env vars are gone |
| `requirements.txt` | 30 → 19 packages after dropping the torch/whisperx/pyannote stack and the removed backends |
| `install.py`, `launch.py` | PyTorch, CUDA detection and whisperx preflight checks removed |
| `core/_12_dub_to_vid.py`, `core/utils/models.py` | The dub track now replaces the original audio outright. Upstream mixed it with the Demucs-separated background stem, which no longer exists here; the two orphaned path constants were dropped and the ffmpeg call now raises on a non-zero exit instead of reporting success |
| `core/_10_gen_audio.py` | Fixed an upstream bug surfaced by numpy>=2: `new_sub_times` stored numpy scalars, whose repr became `np.float64(x)`, which broke the `eval()` that reads the column back in `_11_merge_audio.py`. Values are now coerced to plain floats at the source |
| `README.md`, `README_CN.md`, branding across the app | Renamed to ai-video-subtitle |

## Unchanged

The pipeline stages (`core/_1_*` … `core/_12_*` apart from the two rewired
above), the spaCy sentence-splitting utilities (`core/spacy_utils/`), the
prompt library (`core/prompts.py`), subtitle cutting and alignment, the
duration estimator (`core/tts_backend/estimate_duration.py`), batch mode
(`batch/`) and the Streamlit app structure are upstream work, carried over as-is
apart from the naming changes listed above.

## Functional differences from upstream

These are consequences of routing everything through dlazy, not bugs:

- **Source language is limited to English and Chinese.** dlazy's `fun-asr` and
  `elevenlabs-stt` accept `zh` or `en` only, where upstream's WhisperX handled
  more. Target translation language is still free-form.
- **No vocal separation.** dlazy has no audio-separation tool, so videos with
  loud background music will transcribe less accurately than upstream with
  Demucs enabled.
- **No voice cloning.** Dubbing uses preset voices; upstream's GPT-SoVITS,
  CosyVoice2 and FishTTS reference-audio modes have no dlazy counterpart.

## Trademarks

"dlazy" is a trademark of its owner. This repository does not use the upstream
project's name, logo or brand identity; Apache-2.0 grants no trademark rights,
and none is claimed here.
