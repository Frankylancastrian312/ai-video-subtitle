# ai-video-subtitle

[English](./README.md) | [简体中文](./README_CN.md)

Turn a video into translated, properly cut subtitles — and optionally a dubbed
track — with **one API key**.

Transcription, sentence splitting, terminology extraction, translation and
dubbing all run through the [dlazy](https://dlazy.com) API. There is no local
model to download, no GPU to provision, and no per-vendor key to juggle.

## What it does

Drop in a video file or a YouTube link, and the pipeline runs:

1. **Word-level transcription** — dlazy speech-to-text, with per-word timings
2. **Sentence segmentation** — spaCy for structure, an LLM for meaning
3. **Summarization and terminology extraction** — builds a glossary first, so
   names and jargon stay consistent across the whole video
4. **Multi-step reflective translation** — translate, critique, revise
5. **Subtitle cutting and alignment** — split long lines against the word
   timings so nothing drifts
6. **Burn-in** (optional) — render the subtitles into the video
7. **Dubbing** (optional) — TTS per line, speed-fitted to the subtitle timeline,
   merged back over the video

## Requirements

- Python 3.10
- ffmpeg **and ffprobe** on your PATH (pydub needs ffprobe to read durations;
  some portable ffmpeg builds ship only `ffmpeg.exe`)
- A dlazy API key — get one at
  [dlazy.com/dashboard/organization/api-key](https://dlazy.com/dashboard/organization/api-key)

## Install

### Option A — uv (no Anaconda needed)

```bash
git clone https://github.com/dlazyai/ai-video-subtitle.git
cd ai-video-subtitle
python setup_env.py
```

Then start it with `OneKeyStart_uv.bat` on Windows, or:

```bash
.venv/bin/streamlit run st.py
```

### Option B — conda

```bash
git clone https://github.com/dlazyai/ai-video-subtitle.git
cd ai-video-subtitle
conda create -n ai-video-subtitle python=3.10 -y
conda activate ai-video-subtitle
python install.py
streamlit run st.py
```

### Option C — Docker

```bash
docker build -t ai-video-subtitle .
docker run -p 8501:8501 ai-video-subtitle
```

The image is built on `python:3.10-slim` — no CUDA base layer, because nothing
runs locally.

## Configure

Open the sidebar and paste your dlazy API key. That is the whole setup. The
model pickers below it are read live from your account, so you only ever see
models your key can actually run:

| Setting | Options |
| --- | --- |
| LLM model | `claude-sonnet-5`, `qwen3.8-max`, `kimi-k3` |
| ASR model | `fun-asr`, `elevenlabs-stt` |
| TTS model | `qwen-tts`, `doubao-tts`, `elevenlabs-tts` |
| Voice | Loaded from the selected TTS model's voice list |

Everything else lives in `config.yaml`, which the settings page writes for you.

## Batch mode

For processing a list of videos unattended, see [batch/README.md](batch/README.md).

## Known limits

Honest about what this fork gives up by moving everything to one provider:

- **Source language is English or Chinese.** dlazy's ASR tools accept `zh` or
  `en`. The *target* translation language is free-form — write it in natural
  language and the LLM follows.
- **No vocal separation.** Videos with loud background music transcribe less
  cleanly than they would with a local Demucs pass.
- **No voice cloning.** Dubbing uses preset voices only.

## Credits

Built on [VideoLingo](https://github.com/Huanshere/VideoLingo) by Huanyu,
licensed under Apache-2.0. The pipeline design is theirs; this fork swaps the
model layer for dlazy. See [NOTICE.md](NOTICE.md) for the full list of changes.

## License

Apache-2.0 — see [LICENSE](LICENSE).
