import moviepy as mp
import speech_recognition as sr
import os
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed

VIDEO_PATH = r'D:\bpython\abcd2.mp4'
AUDIO_PATH = 'temp_audio.wav'
CHUNKS_DIR = 'audio_chunks'
TEXT_PATH = 'bengali_output.doc'

CHUNK_LENGTH_MS = 40000  # 40 seconds per chunk
MAX_WORKERS = 4          # adjust based on CPU cores

# --------------------------
# Helper: Convert ms to HH:MM:SS
# --------------------------
def ms_to_time(ms):
    seconds = ms // 1000
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

# --------------------------
# Step 1: Extract audio from video
# --------------------------
def extract_audio():
    clip = mp.VideoFileClip(VIDEO_PATH)
    clip.audio.write_audiofile(AUDIO_PATH, codec='pcm_s16le')
    clip.close()

# --------------------------
# Step 2: Split audio into chunks
# --------------------------
def split_audio():
    audio = AudioSegment.from_wav(AUDIO_PATH)

    if not os.path.exists(CHUNKS_DIR):
        os.mkdir(CHUNKS_DIR)

    chunk_files = []

    for i in range(0, len(audio), CHUNK_LENGTH_MS):
        chunk = audio[i:i + CHUNK_LENGTH_MS]
        chunk_name = os.path.join(CHUNKS_DIR, f"chunk_{i}.wav")
        chunk.export(chunk_name, format="wav")
        start_time = i
        end_time = min(i + CHUNK_LENGTH_MS, len(audio))
        chunk_files.append((i, chunk_name, start_time, end_time))  # store timestamps

    return chunk_files

# --------------------------
# Step 3: Process each chunk
# --------------------------
def process_chunk(chunk_info):
    index, chunk_file, start_time, end_time = chunk_info
    r = sr.Recognizer()

    with sr.AudioFile(chunk_file) as source:
        audio_data = r.record(source)

        try:
            text = r.recognize_google(audio_data, language='bn-BD')
        except sr.UnknownValueError:
            text = "[Unrecognized]"
        except sr.RequestError:
            text = "[API Error]"

    return (index, start_time, end_time, text)

# --------------------------
# Main function
# --------------------------
def main():
    print("Step 1: Extracting audio...")
    extract_audio()

    print("Step 2: Splitting audio into chunks...")
    chunks = split_audio()
    print(f"Total chunks: {len(chunks)}")

    print("Step 3: Parallel processing...")
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, c) for c in chunks]

        for future in as_completed(futures):
            results.append(future.result())

    # 🔥 Sort results to maintain serial order
    results.sort(key=lambda x: x[0])

    print("Step 4: Writing output with timestamps...")
    full_text = ""
    for i, (_, start, end, text) in enumerate(results):
        start_str = ms_to_time(start)
        end_str = ms_to_time(end)
        full_text += f"\n[{start_str} - {end_str}]\n{text}\n"

    with open(TEXT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"Done! Saved to {TEXT_PATH}")

    # Cleanup
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)

    for _, file, _, _ in chunks:
        os.remove(file)

    os.rmdir(CHUNKS_DIR)

if __name__ == "__main__":
    main()