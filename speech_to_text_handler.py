import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

class SpeechToTextHandler:
    def __init__(self):
        self.model = Model(r"resources\vosk_models\vosk-model-en-us-0.22")
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.q = queue.Queue()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        self.q.put(bytes(indata))

    def listen_to_vosk(self):
        print("Listening in real time. Say something! Press Ctrl+C to stop.")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self.audio_callback):
            while True:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        return text

                    # If no valid text was recognized, continue listening
                    continue
