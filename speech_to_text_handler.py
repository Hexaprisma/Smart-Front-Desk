import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

# Load the Vosk speech recognition model
model = Model(r"resources\vosk_models\vosk-model-en-us-0.22")
recognizer = KaldiRecognizer(model, 16000)
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Audio status: {status}")
    q.put(bytes(indata))

def listen():
    print("Listening in real time. Say something! Press Ctrl+C to stop.")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    print(f"You said: {text}")

if __name__ == "__main__":
    try:
        listen()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
