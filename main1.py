# import tkinter as tk
# import threading
# import speech_recognition as sr

# # Initialize recognizer
# recognizer = sr.Recognizer()
# is_listening = False

# def listen_microphone():
#     """Continuously listen and update the text in GUI"""
#     global is_listening
#     with sr.Microphone() as source:
#         recognizer.adjust_for_ambient_noise(source, duration=1)
#         while is_listening:
#             try:
#                 audio = recognizer.listen(source, phrase_time_limit=5)
#                 text = recognizer.recognize_google(audio)
#                 text_display.config(state="normal")
#                 text_display.delete("1.0", tk.END)
#                 text_display.insert(tk.END, text)
#                 text_display.config(state="disabled")
#             except sr.UnknownValueError:
#                 pass
#             except sr.RequestError as e:
#                 text_display.config(state="normal")
#                 text_display.delete("1.0", tk.END)
#                 text_display.insert(tk.END, f"Error: {e}")
#                 text_display.config(state="disabled")
#                 break

# def toggle_listening():
#     """Start/Stop listening"""
#     global is_listening
#     if not is_listening:
#         is_listening = True
#         toggle_btn.config(text="Stop Listening", bg="red")
#         threading.Thread(target=listen_microphone, daemon=True).start()
#     else:
#         is_listening = False
#         toggle_btn.config(text="Start Listening", bg="green")

# # ---------------- GUI ---------------- #
# root = tk.Tk()
# root.title("Real-Time Speech to Text")
# root.geometry("500x300")

# toggle_btn = tk.Button(root, text="Start Listening", bg="green", fg="white",
#                        font=("Arial", 14), command=toggle_listening)
# toggle_btn.pack(pady=10)

# text_display = tk.Text(root, wrap="word", height=10, width=50, font=("Arial", 12))
# text_display.pack(padx=10, pady=10)
# text_display.config(state="disabled")

# root.mainloop()





# ------------------------------------------------------------------------------------------------------



import os
import threading
import queue
import json
import tkinter as tk
import sounddevice as sd
import vosk

# ---------------- Config ----------------
MODEL_PATH = "vosk-model-small-en-us-0.15"  # change to your model folder if needed
SAMPLE_RATE = 16000

# ---------------- Globals ----------------
is_listening = False
audio_q = queue.Queue()   # audio frames -> recognizer thread
ui_q = queue.Queue()      # UI updates -> main thread

# ---------------- Audio callback ----------------
def audio_callback(indata, frames, time, status):
    if status:
        print("SoundDevice status:", status)
    audio_q.put(bytes(indata))

# ---------------- Recognizer thread ----------------
def listen_microphone():
    global is_listening
    try:
        model = vosk.Model(MODEL_PATH)
    except Exception as e:
        ui_q.put(("error", f"Failed to load model: {e}"))
        return

    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                               dtype='int16', channels=1, callback=audio_callback):
            while is_listening:
                data = audio_q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "").strip()
                    if text:
                        ui_q.put(("final", text))
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "").strip()
                    ui_q.put(("partial", partial))
    except Exception as e:
        ui_q.put(("error", f"Audio stream error: {e}"))

# ---------------- GUI update poller ----------------
def poll_ui_queue():
    """Called in main thread via root.after — applies UI updates safely."""
    try:
        while not ui_q.empty():
            typ, text = ui_q.get_nowait()
            if typ == "partial":
                partial_label.config(text=text)
            elif typ == "final":
                # append final text to the transcript area (append-only)
                if text:
                    text_display.config(state="normal")
                    text_display.insert(tk.END, text + " ")
                    text_display.see(tk.END)
                    text_display.config(state="disabled")
                partial_label.config(text="")  # clear partial on final
            elif typ == "error":
                partial_label.config(text=f"ERROR: {text}")
    except queue.Empty:
        pass
    root.after(50, poll_ui_queue)

# ---------------- Start/Stop logic ----------------
def toggle_listening():
    global is_listening
    if not is_listening:
        is_listening = True
        toggle_btn.config(text="Stop Listening", bg="red")
        threading.Thread(target=listen_microphone, daemon=True).start()
    else:
        is_listening = False
        toggle_btn.config(text="Start Listening", bg="green")

def on_closing():
    global is_listening
    is_listening = False
    root.destroy()

# ---------------- Build UI ----------------
root = tk.Tk()
root.title("Real-Time Speech-to-Text (Vosk)")
root.geometry("640x360")


toggle_btn = tk.Button(root, text="Start Listening", bg="black", fg="white", border="2px", 
                       font=("Arial", 14), command=toggle_listening)
toggle_btn.pack(pady=5)

text_display = tk.Text(root, wrap="word", height=20, width=70, font=("Arial", 12))
text_display.pack(padx=10, pady=(0,5))
text_display.config(state="disabled")

# partial live text shown in a smaller label (not appended permanently)
partial_label = tk.Label(root, text="", font=("Arial", 11, "italic"))
partial_label.pack(pady=(0,10))

root.protocol("WM_DELETE_WINDOW", on_closing)

# start the UI polling loop
root.after(50, poll_ui_queue)
root.mainloop()
