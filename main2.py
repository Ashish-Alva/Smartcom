import pyaudio
import json
import sys
from vosk import Model, KaldiRecognizer
import cv2
import numpy as np

# start vosk
# Load model
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Setup audio
mic = pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000,
                  input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening... Press Ctrl+C to stop.")

final_text = ""  # confirmed words

try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            # Finalized segment
            result = json.loads(recognizer.Result())
            spoken = result.get("text", "").strip()
            if spoken:
                final_text += " " + spoken
                sys.stdout.write("\r\033[K" + final_text + " ")
                sys.stdout.flush()

        else:
            # Partial live words
            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get("partial", "").strip()
            sys.stdout.write("\r\033[K" + final_text + " " + partial_text)
            sys.stdout.flush()

except KeyboardInterrupt:
    print("\nFinal transcript:", final_text)


# end of vosk

# Map alphabets to image paths
ASL_MAP = {chr(i+97): f"letters/{chr(i+97)}.jpeg" for i in range(26)}

def show_word_as_asl(word):
    images = []
    for char in word.lower():
        if char in ASL_MAP:
            img = cv2.imread(ASL_MAP[char])
            if img is not None:
                images.append(img)
    if images:
        combined = np.hstack(images)
        cv2.imshow("ASL Word", combined)
        cv2.waitKey(1000)  # Show for 1 second