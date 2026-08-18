from core.utils import *
from core.asr_backend.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results
from core.asr_backend.dlazy_asr import transcribe_audio
from core._1_ytdlp import find_video_files
from core.utils.models import *

@check_file_exists(_2_CLEANED_CHUNKS)
def transcribe():
    # 1. video to audio
    video_file = find_video_files()
    convert_video_to_audio(video_file)

    # 2. Extract audio
    # Vocal separation was dropped together with the local Demucs model — dlazy
    # has no audio-separation tool, so the raw track is transcribed directly.
    segments = split_audio(_RAW_AUDIO_FILE)

    # 3. Transcribe audio by clips
    all_results = []
    for start, end in segments:
        result = transcribe_audio(_RAW_AUDIO_FILE, _RAW_AUDIO_FILE, start, end)
        all_results.append(result)

    # 4. Combine results
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])

    # 5. Process df
    df = process_transcription(combined_result)
    save_results(df)

if __name__ == "__main__":
    transcribe()
