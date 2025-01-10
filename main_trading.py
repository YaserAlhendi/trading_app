import time 
from datetime import datetime, timedelta
import requests
import logger
import mexc_api
from mexc_api import OrderStatus
import simulate_mexc_api
# from simulate_mexc_api import OrderStatus
import socket

APP_DATA_FILE_NAME = "appdata.json"
order_status = OrderStatus.SELLED
buy_price = 0 
sell_price = 0
profit_ratio = 0.01
order_id = 0
byued_quantity = 0

# just for test
balance = 50

#for main2
down_ratio = 0.005;
enable_buy = False
open_price = 0


def update_orders_status(symbol, order_id):
    global order_status
    _success, order_status = mexc_api.get_order_status(symbol, order_id, order_status)
    
    if not success:
        logger.write_msg("Failed to get order {} status.".format(order_id))

def update_app_status():
    global order_status, buy_price, sell_price, profit_ratio, order_id, byued_quantity, balance
    data = {
        "order_status": order_status,  # Default value
        "buy_price": buy_price,
        "sell_price": sell_price,
        "profit_ratio": profit_ratio,
        "order_id": order_id,
        "bought_quantity": byued_quantity,
        "balance": balance
    }
    with open(APP_DATA_FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

def load_app_status():
    global order_status, buy_price, sell_price, profit_ratio, order_id, byued_quantity, balance
    
    if os.path.exists(APP_DATA_FILE_NAME):
        with open(APP_DATA_FILE_NAME, "r") as file:
            loaded_data = json.load(file)
            # Assign loaded data to variables
            order_status = loaded_data.get("order_status", order_status)
            buy_price = loaded_data.get("buy_price", buy_price)
            sell_price = loaded_data.get("sell_price", sell_price)
            profit_ratio = loaded_data.get("profit_ratio", profit_ratio)
            order_id = loaded_data.get("order_id", order_id)
            byued_quantity = loaded_data.get("bought_quantity", bought_quantity)
            balance = loaded_data.get("balance", balance)
            
        print("Data loaded successfully!")
    else:
        print("Data file not found. Using default values.")

# main1: buy at open, then sell when currency goes up by profit_ratio
def __main__(current_timestamp):
    global enable_buy, open_price, order_status, balance, byued_quantity, order_id, sell_price

    try:
        # if 4h frame started
        if current_timestamp % 14400 == 0:
            
            update_orders_status("PEPEUSDT", order_id)
            
            # if the previous sell order filled
            if order_status == OrderStatus.SELLED:
                
                # try to get price 10 times
                price = mexc_api.get_open_price("PEPEUSDT", "4h")
                for i in range(10):
                    if price is None:
                        price = mexc_api.get_open_price("PEPEUSDT", "4h")
                if price is None:
                    return
                
                # set buy order, try 3 times
                success, _order_id, _quantity = mexc_api.set_buy_order("PEPEUSDT", price, 50)
                for i in range(3):
                    if not success:
                        success, _order_id, _quantity = mexc_api.set_buy_order("PEPEUSDT", price, 50)
                    
                if success:
                    order_id = _order_id
                    order_status = OrderStatus.WAITING_BUY
                    buy_price = price
                    byued_quantity = _quantity
                    logger.write_action(current_timestamp, "buy", 50, price, "4h", "set")
                
                else:
                    logger.write_msg(current_timestamp, "Warning, buy not setted.")
            
            elif order_status == OrderStatus.WAITING_SELL:
                logger.write_msg(current_timestamp, "error, sell wasn't complete")
        
        
        # set sell after buy filled
        if order_status == OrderStatus.BUYED:
            sell_price = buy_price + buy_price * profit_ratio
            
            # set sell order
            success, _order_id = mexc_api.set_sell_order("PEPEUSDT", sell_price, byued_quantity)
            if success:
                order_id = _order_id
                order_status = OrderStatus.WAITING_SELL
                logger.write_action(current_timestamp, "sell", byued_quantity, price, "4h", "set")
                
            else:
                logger.write_msg(current_timestamp, "Warning, sell not setted.")


        # check if buy or sell filled
        if order_status == OrderStatus.WAITING_BUY or order_status == OrderStatus.WAITING_SELL:
            update_orders_status("PEPEUSDT", order_id)
            
            #log status if changed
            if order_status == OrderStatus.SELLED:
                balance = balance + quantity * sell_price - 50 # subtract 50 which i used to buy the quantity
                logger.write_balance(current_timestamp, balance)
                logger.write_action(current_timestamp, "sell", byued_quantity, buy_price, "4h", "done")
            elif order_status == OrderStatus.BUYED:
                logger.write_action(current_timestamp, "buy", 50, buy_price, "4h", "done")
    
    except Exception as e:
        print(e)
        logger.write_msg(current_timestamp, "exception, ",e)

# main2: buy when price goes down open by down_ratio before gets up the open, 
# then sell when curency goes up open by up_ratio (up_ratio + down_ratio = profit_ratio)
def __main__(current_timestamp):
    global enable_buy, open_price, order_status, balance, byued_quantity, order_id, sell_price
    
    try:
        # if 4h frame started
        if current_timestamp % 14400 == 0:
            enable_buy = True
            open_price = mexc_api.get_open_price("PEPEUSDT", "4h")
        
        # try to get open price if it's none
        if open_price is None:
            open_price = mexc_api.get_open_price("PEPEUSDT", "4h")
            if open_price is None:
                return
        
        # control buying
        if enable_buy:
            # try to buy whenever a new the 4h frame started
            target_buy_price = open_price * (1 - down_ratio)
            current_price = mexc_api.get_current_price("PEPEUSDT")
            
            # don't buy from this frame if the price goes up the open before it goes down
            if current_price > open_price:
                enable_buy = False
            
            # if the previous sell order filled
            if order_status == OrderStatus.SELLED:
                if current_price <= target_buy_price:
                    # set buy order, try 3 times
                    success, _order_id, _quantity = mexc_api.set_buy_order("PEPEUSDT", current_price, 50)
                    for i in range(3):
                        if not success:
                            success, _order_id, _quantity = mexc_api.set_buy_order("PEPEUSDT", current_price, 50)
                    if success:
                        order_id = _order_id
                        order_status = OrderStatus.WAITING_BUY
                        buy_price = current_price
                        byued_quantity = _quantity
                        logger.write_action(current_timestamp, "buy", 50, current_price, "4h", "set")
                    else:
                        logger.write_msg(current_timestamp, "Warning, buy not setted.")
            
            elif order_status == OrderStatus.WAITING_SELL:
                logger.write_msg(current_timestamp, "error, sell wasn't complete")

        # set sell after buy filled
        if order_status == OrderStatus.BUYED:
            sell_price = buy_price + buy_price * profit_ratio
            
            # set sell order
            success, _order_id = mexc_api.set_sell_order("PEPEUSDT", sell_price, byued_quantity)
            if success:
                order_id = _order_id
                order_status = OrderStatus.WAITING_SELL
                logger.write_action(current_timestamp, "sell", byued_quantity, price, "4h", "set")
                
            else:
                logger.write_msg(current_timestamp, "Warning, sell not setted.")

        # check if buy or sell filled
        if order_status == OrderStatus.WAITING_BUY or order_status == OrderStatus.WAITING_SELL:
            update_orders_status("PEPEUSDT", order_id)
            
            #log status if changed
            if order_status == OrderStatus.SELLED:
                balance = balance + quantity * sell_price - 50 # subtract 50 which i used to buy the quantity
                logger.write_balance(current_timestamp, balance)
                logger.write_action(current_timestamp, "sell", byued_quantity, buy_price, "4h", "done")
            elif order_status == OrderStatus.BUYED:
                logger.write_action(current_timestamp, "buy", 50, buy_price, "4h", "done")
    
    except Exception as e:
        print(e)
        logger.write_msg(current_timestamp, "exception, ",e)


#internet connection checks
def check_internet_connection():
    try:
        # Create a socket and try to connect
        socket.setdefaulttimeout(3)
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False
    

_indx = 0

#initialize the logger
logger.init_log()

# get app required data
load_app_status()

while True:
    
    # Get the current timestamp
    current_timestamp = datetime.now().timestamp()
    try:
        _indx = (_indx + 1) % 61
        print(_indx)
        # check internet connection every 3 minutes,
        # but don't check if we are at the start of 4h frame
        if _indx % 60 == 0 and current_timestamp % 14400 != 0:
            _connected = check_internet_connection()
            if _connected:
                logger.write_msg(current_timestamp, "good, internet connected.")
            else:
                logger.write_msg(current_timestamp, "bad, internet disconnected.")
        
        __main__(current_timestamp)
        update_app_status()
        
        time.sleep(1)
    except Exception as ex:
        print(ex)
        logger.write_msg(current_timestamp, ex)
        time.sleep(1)
