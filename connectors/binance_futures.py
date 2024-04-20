import logging
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

# Initialize logger for logging events
logger = logging.getLogger()

class BinanceFutureClient:
    def __init__(self, public_key, secret_key, testnet):
        # Set base URL based on testnet flag
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"  # Testnet API endpoint
        else:
            self.base_url = "https://fapi.binance.com"  # Production API endpoint

        self.public_key = public_key
        self.secret_key = secret_key

        self.headers = {'X-MBX-APIKEY': self.public_key}

        # Dictionary to store latest bid-ask prices for symbols
        self.prices = dict()
        
        # Log initialization of Binance Futures client
        logger.info("Binance Futures Client Successfully Initialized")


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
    def generate_signature(self, data):
        return hmac.new(self.secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()
    
    def make_request(self, method, endpoint, data):
        # Make HTTP request to Binance Futures API
        if method == "GET":
            response = requests.get(self.base_url + endpoint, params=data, headers=self.headers)
        elif method == "POST":
            response = requests.post(self.base_url + endpoint, params=data, headers=self.headers)
        elif method == "DELETE":
            response = requests.delete(self.base_url + endpoint, params=data, headers=self.headers)
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
        
    def get_contracts(self):
        # Retrieve information about available contracts on Binance Futures
        exchange_info = self.make_request("GET", "/fapi/v1/exchangeInfo", None)
        contracts = dict()
        if exchange_info is not None:
            # Extract contract data from API response
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = contract_data
        return contracts
    
    def get_historical_candles(self, symbol, interval):
        # Retrieve historical candlestick data for a symbol and interval
        data = dict()
        data['symbol'] = symbol
        data['interval'] = interval
        data['limit'] = 1000  # Limit the number of returned candles

        raw_candles = self.make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            # Format raw candlestick data into a list of tuples
            for c in raw_candles:
                candles.append((c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])))
        return candles
    
    def get_bid_ask(self, symbol):
        # Retrieve bid-ask spread for a symbol
        data = dict()
        data['symbol'] = symbol
        ob_data = self.make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if symbol not in self.prices:
                # Initialize bid-ask prices if not available
                self.prices[symbol] = {
                    'bid': float(ob_data['bidPrice']),  # Latest bid price
                    'ask': float(ob_data['askPrice'])   # Latest ask price
                }
            else:
                # Update latest bid-ask prices
                self.prices[symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[symbol]['ask'] = float(ob_data['askPrice'])

        return self.prices[symbol]


    # Get current balances from account.
    def get_balance(self):
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data["signature"] = self.generate_signature(data)

        balances = dict()

        account_data = self.make_request("GET", "/fapi/v2/account", data)

        if account_data is not None:
            for a in account_data["assets"]:
                balances[a['asset']] = a
        return balances

    # Placing order
    def place_order(self, symbol, side, quantity, order_type, price=None, timeinforce=None):
        data = dict()
        data['symbol'] = symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type
        if price is not None:
            data['price'] = price
        if timeinforce is not None:
            data['timeinforce'] = timeinforce
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("POST", "/fapi/v1/order", data)
        return order_status


    # Cancelling order
    def cancel_order(self, symbol, order_id):
        data = dict()
        data['orderId'] = order_id
        data['symbol'] = symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("DELETE", "/fapi/v1/order", data)
        return order_status

    # Get order status
    def get_order_status(self, symbol, order_id):
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = symbol
        data['orderID'] = order_id
        data['signature'] = self.generate_signature(data)
        order_status = self.make_request("GET", "/fapi/v1/order", data)
        return order_status