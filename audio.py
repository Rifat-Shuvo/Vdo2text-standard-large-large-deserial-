import wave
import os
import speech_recognition as sr
from concurrent.futures import ThreadPoolExecutor, as_completed

AUDIO_PATH = "input.wav"
CHUNKS_DIR = "chunks"
TEXT_PATH = "bengali_output.txt"

CHUNK_DURATION = 120  # seconds (120000 ms)


def split_wav():
    """Split WAV file into 120 sec chunks"""
    with wave.open(AUDIO_PATH, 'rb') as wf:
        frame_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()

        frames_per_chunk = frame_rate * CHUNK_DURATION

        if not os.path.exists(CHUNKS_DIR):
            os.mkdir(CHUNKS_DIR)

        chunk_files = []
        i = 0

        while True:
            frames = wf.readframes(frames_per_chunk)
            if not frames:
                break

            chunk_filename = os.path.join(CHUNKS_DIR, f"chunk_{i}.wav")

            with wave.open(chunk_filename, 'wb') as chunk:
                chunk.setnchannels(n_channels)
                chunk.setsampwidth(sampwidth)
                chunk.setframerate(frame_rate)
                chunk.writeframes(frames)

            chunk_files.append((chunk_filename, i))
            i += 1

    return chunk_files


def process_chunk(file, idx):
    """Recognize a single chunk"""
    r = sr.Recognizer()

    with sr.AudioFile(file) as source:
        audio_data = r.record(source)

    try:
        text = r.recognize_google(audio_data, language='bn-BD')
        print(f"Chunk {idx} done")
        return idx, text
    except:
        return idx, ""


def main():
    if not os.path.exists(AUDIO_PATH):
        print("Audio file not found!")
        return

    print("Splitting audio...")
    chunks = split_wav()

    print(f"{len(chunks)} chunks created.")
    print("Processing in parallel...")

    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_chunk, f, i) for f, i in chunks]

        for future in as_completed(futures):
            idx, text = future.result()
            results[idx] = text

    print("Combining results...")

    full_text = ""
    for i in sorted(results.keys()):
        full_text += results[i] + " "

    with open(TEXT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print("Done! Saved to", TEXT_PATH)

    # Cleanup
    for file, _ in chunks:
        os.remove(file)
    os.rmdir(CHUNKS_DIR)


if __name__ == "__main__":
    main()