import streamlit as st

from translations.translations import translate as t
from translations.translations import DISPLAY_LANGUAGES
from core.utils import *
from core.utils.dlazy_client import available_models, check_credentials, list_voices

# Candidate models. The manifest filters these down to what the key can run, so
# a model going away upstream degrades the dropdown instead of breaking a run.
LLM_MODELS = ["claude-sonnet-5", "qwen3.8-max", "kimi-k3"]
ASR_MODELS = ["fun-asr", "elevenlabs-stt"]
TTS_MODELS = ["qwen-tts", "doubao-tts", "elevenlabs-tts"]

# dlazy speech-to-text accepts these two source languages only.
RECOG_LANGS = {"🇺🇸 English": "en", "🇨🇳 简体中文": "zh"}


def config_input(label, key, help=None, placeholder=None, type="default"):
    """Generic config input handler"""
    val = st.text_input(label, value=load_key(key), help=help, placeholder=placeholder, type=type)
    if val != load_key(key):
        update_key(key, val)
    return val


def _select(label, key, options, help=None):
    """Selectbox bound to a config key, tolerant of values no longer offered."""
    if not options:
        return None
    current = load_key(key)
    index = options.index(current) if current in options else 0
    choice = st.selectbox(label, options=options, index=index, help=help)
    if choice != current:
        update_key(key, choice)
        st.rerun()
    return choice


def page_setting():
    display_language = st.selectbox(
        "Display Language 🌐",
        options=list(DISPLAY_LANGUAGES.keys()),
        index=list(DISPLAY_LANGUAGES.values()).index(load_key("display_language")),
    )
    if DISPLAY_LANGUAGES[display_language] != load_key("display_language"):
        update_key("display_language", DISPLAY_LANGUAGES[display_language])
        st.rerun()

    with st.expander(t("dlazy Configuration"), expanded=True):
        st.caption(t("One key covers translation, transcription and dubbing."))
        config_input(
            t("dlazy API Key"),
            "dlazy.api_key",
            help=t("Get it at dlazy.com/dashboard/organization/api-key"),
            placeholder=t("Enter your dlazy API key"),
            type="password",
        )

        if st.button("📡 " + t("Check API"), key="api", use_container_width=True):
            with st.spinner(t("Check API") + "..."):
                is_valid = check_credentials()
            st.toast(
                t("API Key is valid") if is_valid else t("API Key is invalid"),
                icon="✅" if is_valid else "❌",
            )

        _select(t("LLM Model"), "dlazy.llm_model", available_models(LLM_MODELS),
                help=t("Used for sentence splitting, summarizing and translation"))
        _select(t("ASR Model"), "dlazy.asr_model", available_models(ASR_MODELS),
                help=t("Speech-to-text engine used for transcription"))

    with st.expander(t("Subtitles Settings"), expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            current_lang = load_key("asr.language")
            values = list(RECOG_LANGS.values())
            lang = st.selectbox(
                t("Recog Lang"),
                options=list(RECOG_LANGS.keys()),
                index=values.index(current_lang) if current_lang in values else 0,
                help=t("dlazy transcription supports English and Chinese"),
            )
            if RECOG_LANGS[lang] != current_lang:
                update_key("asr.language", RECOG_LANGS[lang])
                st.rerun()

        with c2:
            target_language = st.text_input(
                t("Target Lang"),
                value=load_key("target_language"),
                help=t("Input any language in natural language, as long as llm can understand"),
            )
            if target_language != load_key("target_language"):
                update_key("target_language", target_language)
                st.rerun()

        burn_subtitles = st.toggle(
            t("Burn-in Subtitles"),
            value=load_key("burn_subtitles"),
            help=t("Whether to burn subtitles into the video, will increase processing time"),
        )
        if burn_subtitles != load_key("burn_subtitles"):
            update_key("burn_subtitles", burn_subtitles)
            st.rerun()

    with st.expander(t("Dubbing Settings"), expanded=True):
        tts_model = _select(t("TTS Model"), "dlazy.tts_model", available_models(TTS_MODELS))

        if tts_model:
            try:
                voices, default_voice = list_voices(tts_model)
            except Exception:
                voices, default_voice = [], ""
            if voices:
                current_voice = load_key("dlazy.tts_voice") or default_voice
                index = voices.index(current_voice) if current_voice in voices else 0
                voice = st.selectbox(t("Voice"), options=voices, index=index)
                if voice != load_key("dlazy.tts_voice"):
                    update_key("dlazy.tts_voice", voice)
                    st.rerun()
            else:
                config_input(t("Voice"), "dlazy.tts_voice",
                             help=t("Set the dlazy API key first to load the voice list"))

        st.caption(t("Voice cloning is not available; dubbing uses preset voices."))
