import moviepy as mp
import speech_recognition as sr
import os
from pydub import AudioSegment
from concurrent.futures import ProcessPoolExecutor, as_completed

VIDEO_PATH = r'D:\bpython\abcd.mp4'
AUDIO_PATH = 'temp_audio.wav'
CHUNKS_DIR = 'audio_chunks'
TEXT_PATH = 'bengali_outputL.doc'

CHUNK_LENGTH_MS = 120000  # 60 sec


def process_chunk(chunk_file, index):
    """Process a single chunk (runs in parallel)"""
    r = sr.Recognizer()

    with sr.AudioFile(chunk_file) as source:
        audio_data = r.record(source)

        try:
            text = r.recognize_google(audio_data, language='bn-BD')
            return index, text
        except sr.UnknownValueError:
            return index, ""
        except sr.RequestError as e:
            print(f"Chunk {index}: API error {e}")
            return index, ""


def extract_text():
    print('Initializing...')

    if not os.path.exists(VIDEO_PATH):
        print(f"File not found: {VIDEO_PATH}")
        return

    try:
        # 1. Extract audio
        clip = mp.VideoFileClip(VIDEO_PATH)
        clip.audio.write_audiofile(AUDIO_PATH, codec='pcm_s16le')
        clip.close()

        print('Audio extracted. Splitting...')

        # 2. Split audio
        audio = AudioSegment.from_wav(AUDIO_PATH)

        if not os.path.exists(CHUNKS_DIR):
            os.mkdir(CHUNKS_DIR)

        chunk_files = []

        for i, start in enumerate(range(0, len(audio), CHUNK_LENGTH_MS)):
            chunk = audio[start:start + CHUNK_LENGTH_MS]
            chunk_name = os.path.join(CHUNKS_DIR, f"chunk_{i}.wav")
            chunk.export(chunk_name, format="wav")
            chunk_files.append((chunk_name, i))

        print(f"{len(chunk_files)} chunks created.")

        # 3. Parallel processing
        print("Processing in parallel...")

        results = {}

        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(process_chunk, file, idx)
                for file, idx in chunk_files
            ]

            for future in as_completed(futures):
                idx, text = future.result()
                results[idx] = text
                print(f"Finished chunk {idx}")

        # 4. Combine results in order
        full_text = ""
        for i in sorted(results.keys()):
            full_text += results[i] + " "

        # 5. Save output
        with open(TEXT_PATH, 'w', encoding='utf-8') as f:
            f.write(full_text)

        print('--- Done ---')
        print(f"Saved to {TEXT_PATH}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cleanup
        if os.path.exists(AUDIO_PATH):
            os.remove(AUDIO_PATH)

        if os.path.exists(CHUNKS_DIR):
            for file in os.listdir(CHUNKS_DIR):
                os.remove(os.path.join(CHUNKS_DIR, file))
            os.rmdir(CHUNKS_DIR)


if __name__ == "__main__":
    extract_text()