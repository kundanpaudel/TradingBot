## Imports
## UI import
import tkinter as tk 
import tkmacosx as tkm
from tkinter import Label
# from tkmacosx import Label

## logger import
import logging
from bitmex import get_contracts

logger = logging.getLogger()

logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

## Following only works if main.py is executed.
if __name__ == '__main__':
    bitmex_contracts = get_contracts()

    ## Main window of application.
    root = tk.Tk()

    for contract in bitmex_contracts:
        label_widget = Label(root, text="hello")
        label_widget.pack(side = tk.TOP)

    ## Function that keeps the window open indefinitely 
    # until any user input is given.
    root.mainloop()