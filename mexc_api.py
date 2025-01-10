import time
import requests
import hashlib
import hmac
from enum import Enum


API_KEY = 'mx0vglZz4BqiGGWUmp'
API_SECRET = '4b34d4c62da94c4b959c051664c61c96'

class OrderStatus(Enum):
    NOTHING = 0
    WAITING_BUY = 1
    BUYED = 2
    WAITING_SELL = 3
    SELLED = 4

def set_buy_order(symbol, price, usd_amount):
    quantity = round(usd_amount / price, 8)  # Calculate quantity, rounding to 8 decimals
    url = "https://api.mexc.com/api/v3/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": price,
        "timestamp": timestamp,
    }
    query_string = "&".join(f"{key}={value}" for key, value in params.items())
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    headers = {"X-MEXC-APIKEY": API_KEY}
    response = requests.post(f"{url}?{query_string}&signature={signature}", headers=headers)
    
    # Check for successful response
    if response.status_code == 200:
        order_data = response.json()
        order_id = order_data.get("orderId", None)

        # Return success, order ID, and quantity
        return True, order_id, quantity
    else:
        # Return failure, None, and 0 if an error occurred
        return False, None, 0


def set_sell_order(symbol, price, quantity):
    url = "https://api.mexc.com/api/v3/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": price,
        "timestamp": timestamp,
    }
    query_string = "&".join(f"{key}={value}" for key, value in params.items())
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    headers = {"X-MEXC-APIKEY": API_KEY}
    response = requests.post(f"{url}?{query_string}&signature={signature}", headers=headers)
    
    if response.status_code == 200:
            order_data = response.json()
            order_id = order_data.get("orderId", None)  # Extract the order ID
            return True, order_id
    else:
        print(f"Error: HTTP {response.status_code}, {response.text}")
        return False, None

def get_order_status(symbol, order_id, current_status):
    try:
        # Generate the query string
        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
        query_string = f"symbol={symbol}&orderId={order_id}&timestamp={timestamp}"

        # Generate the signature
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

        # Add the signature to the query string
        query_string += f"&signature={signature}"

        # Make the GET request
        url = f"https://api.mexc.com/api/v3/order?{query_string}"
        headers = {
            "X-MEXC-APIKEY": API_KEY
        }

        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            order_data = response.json()
            status = order_data.get("status", "Unknown")
            
            #if order finished
            if status == "FILLED":
                if current_status == OrderStatus.WAITING_BUY:
                    return True, OrderStatus.BUYED
                elif current_status == OrderStatus.WAITING_SELL:
                    return True, OrderStatus.SELLED
            else:
                return True, current_status
        else:
            return False, current_status
    
    except Exception as e:
        return False, current_status

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

def cancel_order(symbol, order_id):
    try:
        # Generate the query string
        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
        query_string = f"symbol={symbol}&orderId={order_id}&timestamp={timestamp}"

        # Generate the signature
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

        # Add the signature to the query string
        query_string += f"&signature={signature}"

        # Make the DELETE request
        url = f"https://api.mexc.com/api/v3/order"
        headers = {
            "X-MEXC-APIKEY": API_KEY
        }

        response = requests.delete(url, headers=headers, params=query_string)

        # Check for successful response
        if response.status_code == 200:
            print(f"Order with ID {order_id} successfully canceled.")
            return True
        else:
            print(f"Error: HTTP {response.status_code}, {response.text}")
            return False
    except Exception as e:
        # Handle exceptions
        print(f"Exception occurred: {str(e)}")
        return False

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