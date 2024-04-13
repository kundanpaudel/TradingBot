## Imports

## UI import
import tkinter as tk 
## logger import
import logging

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
    ## Main window of application.
    root = tk.Tk() 
    ## Function that keeps the window open indefinitely 
    # until any user input is given.
    root.mainloop()