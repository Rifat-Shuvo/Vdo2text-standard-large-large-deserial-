import moviepy as mp
import speech_recognition as sr
import os

# Define paths clearly
VIDEO_PATH = r'D:\bpython\abc1.mp4'
AUDIO_PATH = 'temp_audio.wav'
TEXT_PATH = 'standard.doc'

def extract_text(): 
    print('Initializing...')
    
    # Check if video exists first
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: File not found at {VIDEO_PATH}")
        return

    try:
        # 1. Extract Audio
        clip = mp.VideoFileClip(VIDEO_PATH)
        # We specify codec to ensure compatibility with SpeechRecognition
        clip.audio.write_audiofile(AUDIO_PATH, codec='pcm_s16le')
        clip.close() # CRITICAL: Close the clip to release the file lock
        
        print('Audio extracted successfully. Processing Bengali...')
        
        # 2. Recognize Speech
        r = sr.Recognizer()
        with sr.AudioFile(AUDIO_PATH) as source:
            # Helps with background noise common in mobile videos
            r.adjust_for_ambient_noise(source)
            audio_data = r.record(source)
            
            print('Sending audio to google (Bengali-BD)...')
            text = r.recognize_google(audio_data, language='bn-BD')
            
            # 3. Save with UTF-8 (Required for Bengali)
            with open(TEXT_PATH, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print('--- Transcription Successful ---')
            print(f"Result saved to {TEXT_PATH}")

    except sr.UnknownValueError:
        print("Error: Google couldn't understand the Bengali audio.")
    except sr.RequestError as e:
        print(f"Error: Could not reach Google servers; {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # 4. Cleanup
        if os.path.exists(AUDIO_PATH):
            os.remove(AUDIO_PATH)

if __name__ == "__main__":
    extract_text()