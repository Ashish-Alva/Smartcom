import tkinter as tk
from pages.home_page import HomePage
from pages.hand_gesture_page import HandGesturePage
from pages.insert_image_page import InsertImagePage
from pages.speech_sign_page import SpeechSignPage
from pages.speech_braille_page import SpeechBraillePage

class SmartComApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SmartCom")
        self.geometry("1000x600")
        self.configure(bg="white")

        # Allow root to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container for all pages
        container = tk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")

        # Allow container to expand
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (HomePage, HandGesturePage, InsertImagePage, SpeechSignPage, SpeechBraillePage):
            page_name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[page_name] = frame
            # Expand page fully
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        """Raise the selected page to the front."""
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = SmartComApp()
    app.mainloop()
