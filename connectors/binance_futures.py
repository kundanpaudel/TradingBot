import logging
import requests
import time
import typing
import hmac
import hashlib
from urllib.parse import urlencode
import websocket
import threading
import json
from models import *

# Initialize logger for logging events
logger = logging.getLogger()

class BinanceFutureClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        # Set base URL based on testnet flag
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"  # Testnet API endpoint
            self._wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"  # Production API endpoint
            self._wss_url = "wss://fstream.binance.com/ws"

        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}
        
        self.contracts = self.get_contracts()
        self.balances = self.get_balance()

        # Dictionary to store latest bid-ask prices for symbols
        self.prices = dict()
        
        self.logs = []

        self._ws_id = 1
        self.ws = None

        t = threading.Thread(target=self._start_ws)
        t.start()
        
        # Log initialization of Binance Futures client
        logger.info("Binance Futures Client Successfully Initialized")


    def _add_logs(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})
        
    """
    The method below takes the request data as input and generates a cryptographic
    signature using HMAC (Hash-based Message Authentication Code) algorithm
    with SHA-256 hash function. The signature is computed by encoding the
    request data using URL encoding, then hashing it with the secret key
    provided. The resulting signature is returned as a hexadecimal string.

    Args:
        data (dict): A dictionary containing the request parameters to be signed.

    Returns:
        str: A hexadecimal string representing the HMAC signature.
    """
    def _generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, data: typing.Dict):
        # Make HTTP request to Binance Futures API
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection Error While Making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection Error While Making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection Error While Making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError("Unsupported HTTP method")
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()  # Return JSON response
        else:
            # Log error if request fails
            logger.error("Error while making %s request to %s: %s (HTTP status code %s)", 
                            method, endpoint, response.json(), response.status_code)
            return None
        
    def get_contracts(self) -> typing.Dict[str, Contract]:
        # Retrieve information about available contracts on Binance Futures
        exchange_info = self._make_request("GET", "/fapi/v1/exchangeInfo", dict())
        contracts = dict()
        if exchange_info is not None:
            # Extract contract data from API response
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = Contract(contract_data)
        return contracts
    
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        # Retrieve historical candlestick data for a symbol and interval
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000  # Limit the number of returned candles

        raw_candles = self._make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            # Format raw candlestick data into a list of tuples
            for c in raw_candles:
                candles.append(Candle(c))
        return candles
    
    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, float]:
        # Retrieve bid-ask spread for a symbol
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self._make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if contract.symbol not in self.prices:
                # Initialize bid-ask prices if not available
                self.prices[contract.symbol] = {
                    'bid': float(ob_data['bidPrice']),  # Latest bid price
                    'ask': float(ob_data['askPrice'])   # Latest ask price
                }
            else:
                # Update latest bid-ask prices
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]


    # Get current balances from account.
    def get_balance(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data["signature"] = self._generate_signature(data)

        balances = dict()

        account_data = self._make_request("GET", "/fapi/v2/account", data)

        if account_data is not None:
            for a in account_data["assets"]:
                balances[a['asset']] = Balance(a)
        return balances

    # Placing order
    def place_order(self, contract: Contract, side: str, quantity: float, order_type: str, price=None, timeinforce=None) -> OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type
        if price is not None:
            data['price'] = price
        if timeinforce is not None:
            data['timeinforce'] = timeinforce
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("POST", "/fapi/v1/order", data)
        
        if order_status is not None:
            order_status = OrderStatus(order_status)
        
        return order_status


    # Cancelling order
    def cancel_order(self, contract: Contract, order_id: int)-> OrderStatus:
        data = dict()
        data['orderId'] = order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    # Get order status
    def get_order_status(self, contract: Contract, order_id: int)-> OrderStatus:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderID'] = order_id
        data['signature'] = self.g_enerate_signature(data)
        order_status = self._make_request("GET", "/fapi/v1/order", data)
        if order_status is not None:
            order_status = OrderStatus(order_status)
        return order_status

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error, on_message=self._on_message)
        while True:
            try:
                self.ws.run_forever()
            except Exception as e:
                logger.error("Binance Error In run_forever() method: %s",e)
            time.sleep(2)
    
    def _on_open(self, ws):
        logger.info("Binance connection opened")
        contract_list = list(self.contracts.values())
        self.subscribe_channel(contract_list, "bookTicker")
    
    def _on_close(self, ws):
        logger.warning("Binance connection closed")

    def _on_error(self, ws, error_code: int, error_msg: str):
        logger.error("Binance connection error. Error code: %s, Error message: %s", error_code, error_msg)

    
    def _on_message(self, ws, message: str):
        # logger.info("Binance message received: %s", message)
        data = json.loads(message)

        if "e" in data:
           if data['e'] == 'bookTicker':
            symbol = data['s']
            if symbol not in self.prices:
                # Initialize bid-ask prices if not available
                self.prices[symbol] = {
                    'bid': float(data['b']),  # Latest bid price
                    'ask': float(data['a'])   # Latest ask price
                }
            else:
                # Update latest bid-ask prices
                self.prices[symbol]['bid'] = float(data['b'])
                self.prices[symbol]['ask'] = float(data['a'])
            # print(self.prices[symbol])
            if symbol == "BTCUSDT":
                self._add_logs(symbol+ " " + str(self.prices[symbol]["bid"]) + " / " + 
                                                str(self.prices[symbol]["ask"]))

    
    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        if self.ws is None:
            logger.error("WebSocket connection is not initialized.")
            return
        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []
        # for contract in contracts:
        #     data['params'].append(contract.symbol.lower()+"@"+ channel)
        data['params'].append("!bookTicker")
        data['id'] = self._ws_id
        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket Error While Subscribing to %s %s updates: %s", len(contracts), channel, e)
        
        self._ws_id += 1