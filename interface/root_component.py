import tkinter as tk
import time

from connectors.binance_futures import BinanceFutureClient
from interface.logging_component import *
from interface.styling import *
from interface.watchlist_component import WatchList

class Root(tk.Tk):
    def __init__(self, binance: BinanceFutureClient):
        super().__init__()
        self.binance = binance
        
        self.title("ProTactic")
        
        self.configure(bg=BG_COLOR)
        
        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tk.LEFT)
        
        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.RIGHT)
        
        self._watchlist_frame = WatchList(self.binance.contracts, self._left_frame, bg=BG_COLOR)
        self._watchlist_frame.pack(side=tk.TOP)
        
        self._logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self._logging_frame.pack(side=tk.TOP)
    
        self._update_ui()
        
        
    def _update_ui(self):
        for log in self.binance.logs:
            if not log["displayed"]:
                self._logging_frame.add_log(log['log'])
                log["displayed"] = True
        
                
        for key, value in self._watchlist_frame.body_widgets['symbol'].items():
            symbol = self._watchlist_frame.body_widgets['symbol'][key].cget("text")
            if symbol not in self.binance.contracts:
                continue
            if symbol not in self.binance.prices:
                self.binance.get_bid_ask(self.binance.contracts[symbol])
                
            prices = self.binance.prices[symbol]
            
            if prices['bid'] is not None:
                self._watchlist_frame.body_widgets['bid_var'][key].set(prices['bid'])
            if prices['ask'] is not None:
                self._watchlist_frame.body_widgets['ask_var'][key].set(prices['ask'])
            
        
        self.after(1000, self._update_ui)