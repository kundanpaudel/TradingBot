## Imports
import tkinter as tk  # Module for GUI
import logging  # Module for logging
from connectors.binance_futures import BinanceFutureClient  # Importing Binance Futures client

# Setting up logging configurations
logger = logging.getLogger()  # Initialize logger
logger.setLevel(logging.INFO)  # Set log level to INFO

# Setting up logging handlers
stream_handler = logging.StreamHandler()  # Stream handler for console output
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')  # Log format
stream_handler.setFormatter(formatter)  # Set formatter for stream handler
stream_handler.setLevel(logging.INFO)  # Set log level for stream handler to INFO

file_handler = logging.FileHandler('info.log')  # File handler for log file
file_handler.setFormatter(formatter)  # Set formatter for file handler
file_handler.setLevel(logging.DEBUG)  # Set log level for file handler to DEBUG

# Add handlers to logger
logger.addHandler(stream_handler)  # Add stream handler to logger
logger.addHandler(file_handler)  # Add file handler to logger

## Following only works if main.py is executed.
if __name__ == '__main__':
    # Initialize Binance Futures client for testnet
    binance = BinanceFutureClient("4bad66b617dd085319d941104cb4f3f0c03a1ab966a364a2e1845ae14cb54669", "e74f9f00255b56601171f4265ef8df3f8ca6a4f145e6f112058c55cfdecab12b",True)
    # Print historical candles for BTCUSDT pair with 1-hour interval
    print(binance.get_historical_candles("BTCUSDT", "1h"))

    ## Main window of application.
    root = tk.Tk()  # Create main application window

    ## Function that keeps the window open indefinitely 
    # until any user input is given.
    root.mainloop()  # Start main event loop for GUI application
