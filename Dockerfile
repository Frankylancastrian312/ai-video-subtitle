# No GPU layer here on purpose: every model runs on dlazy's side, so the image
# only needs Python, ffmpeg and the CJK-capable fonts used for burning subtitles.
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-noto-cjk \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt setup.py ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# spaCy sentence-splitting models are pulled on first use for the source
# language; pre-install the two the ASR layer can actually produce.
RUN python -m spacy download en_core_web_md && \
    python -m spacy download zh_core_web_md

EXPOSE 8501

CMD ["streamlit", "run", "st.py"]
