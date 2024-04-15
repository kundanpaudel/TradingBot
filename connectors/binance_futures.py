import logging
import requests

# Initialize logger for logging events
logger = logging.getLogger()

class BinanceFutureClient:
    def __init__(self, testnet):
        # Set base URL based on testnet flag
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"  # Testnet API endpoint
        else:
            self.base_url = "https://fapi.binance.com"  # Production API endpoint
        
        # Dictionary to store latest bid-ask prices for symbols
        self.prices = dict()
        
        # Log initialization of Binance Futures client
        logger.info("Binance Futures Client Successfully Initialized")
    
    def make_request(self, method, endpoint, data):
        # Make HTTP request to Binance Futures API
        if method == "GET":
            response = requests.get(self.base_url + endpoint, params=data)
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