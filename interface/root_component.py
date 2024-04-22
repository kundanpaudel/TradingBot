import tkinter as tk
import time
from interface.logging_component import *
from interface.styling import *

class Root(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ProTactic")
        
        self.configure(bg=BG_COLOR)
        
        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tk.LEFT)
        
        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.RIGHT)
        
        self._logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self._logging_frame.pack(side=tk.TOP)
        
        self._logging_frame.add_log("Test Message!!!!!!")
        time.sleep(2)
        self._logging_frame.add_log("Test Message!!!!!!")