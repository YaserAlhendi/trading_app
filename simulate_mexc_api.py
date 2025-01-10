import time
import requests
import hashlib
import hmac
from enum import Enum

# Set your API key and secret
API_KEY = 'mx0vgll4Zz4b8hMHLt'
API_SECRET = 'ab96f5c2fa774cfea1c658619cee0003'

class OrderStatus(Enum):
    NOTHING = 0
    WAITING_BUY = 1
    BUYED = 2
    WAITING_SELL = 3
    SELLED = 4

order_status = OrderStatus.SELLED
buy_price = 0
sell_price = 0

def set_buy_order(symbol, price, usd_amount):
    global order_status, buy_price 
    order_status = OrderStatus.WAITING_BUY
    buy_price = price
    quantity = round(usd_amount / price, 8)  # Calculate quantity, rounding to 8 decimals
    return True, 1, quantity

    # url = "https://api.mexc.com/api/v3/order"
    # timestamp = int(time.time() * 1000)
    # params = {
    #     "symbol": symbol,
    #     "side": "BUY",
    #     "type": "LIMIT",
    #     "timeInForce": "GTC",
    #     "quantity": quantity,
    #     "price": price,
    #     "timestamp": timestamp,
    # }
    # query_string = "&".join(f"{key}={value}" for key, value in params.items())
    # signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    # headers = {"X-MEXC-APIKEY": API_KEY}
    # response = requests.post(f"{url}?{query_string}&signature={signature}", headers=headers)
    
    # # Check for successful response
    # if response.status_code == 200:
    #     order_data = response.json()
    #     order_id = order_data.get("orderId", None)

    #     # Return success, order ID, and quantity
    #     return True, order_id, quantity
    # else:
    #     # Return failure, None, and 0 if an error occurred
    #     return False, None, 0


def set_sell_order(symbol, price, quantity):
    global order_status, sell_price 
    order_status = OrderStatus.WAITING_SELL
    sell_price = price
    return True, 1

    # url = "https://api.mexc.com/api/v3/order"
    # timestamp = int(time.time() * 1000)
    # params = {
    #     "symbol": symbol,
    #     "side": "SELL",
    #     "type": "LIMIT",
    #     "timeInForce": "GTC",
    #     "quantity": quantity,
    #     "price": price,
    #     "timestamp": timestamp,
    # }
    # query_string = "&".join(f"{key}={value}" for key, value in params.items())
    # signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    # headers = {"X-MEXC-APIKEY": API_KEY}
    # response = requests.post(f"{url}?{query_string}&signature={signature}", headers=headers)
    
    # if response.status_code == 200:
    #         order_data = response.json()
    #         order_id = order_data.get("orderId", None)  # Extract the order ID
    #         return True, order_id
    # else:
    #     print(f"Error: HTTP {response.status_code}, {response.text}")
    #     return False, None

def get_order_status(symbol, order_id, current_status):
    global buy_price, sell_price
    if current_status == OrderStatus.WAITING_BUY:
        if get_current_price(symbol) < buy_price:
            return True, OrderStatus.BUYED
    elif current_status == OrderStatus.WAITING_SELL:
        if get_current_price(symbol) > sell_price:
            return True, OrderStatus.SELLED

    return True, current_status
    

def get_open_price(symbol, frame_type):
    try:
        # MEXC Kline (candlestick) API endpoint
        url = f"https://api.mexc.com/api/v3/klines"

        # Parameters for 30-minute frame
        params = {
            "symbol": symbol,
            "interval": frame_type,
            "limit": 1
        }

        # Make a GET request
        response = requests.get(url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Extract the open price from the first (most recent) candlestick
            open_price = float(data[0][1])  # Index 1 contains the open price
            return open_price
        else:
            return None
    except Exception as e:
        return None

def get_current_price(symbol):
    try:
        # MEXC API endpoint for ticker price
        url = f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}"
        
        # Make a GET request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 0))  # Return the price as a float
        else:
            print(f"Error: HTTP {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None