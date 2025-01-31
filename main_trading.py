import time 
from datetime import datetime, timedelta
import requests
import logger
import mexc_api
from mexc_api import OrderStatus
import os
# import simulate_mexc_api
# from simulate_mexc_api import OrderStatus
import socket
import json

APP_DATA_FILE_NAME = "appdata.json"
order_status = OrderStatus.SELLED
buy_price = 0 
sell_price = 0
profit_ratio = 0.01
order_id = 0
byued_quantity = 0

# just for test
balance = 3
trading_balance = 3

#for main2
down_ratio = 0.01;
enable_buy = False
open_price = 0
frame_type = "4h"
# frame_duration_sec = 14400
last_candle_start_time = 0
trading_currency = "HNTUSDT"

current_timestamp = 0


def update_orders_status(symbol, order_id):
    global order_status, current_timestamp
    _success, order_status = mexc_api.get_order_status(symbol, order_id, order_status)
    
    if not _success:
        logger.write_msg(current_timestamp,"Failed to get order {} status.".format(order_id))

def update_app_status():
    global order_status, buy_price, sell_price, profit_ratio, order_id, byued_quantity, balance, down_ratio, enable_buy, open_price
    try:
        data = {
            "order_status": order_status.value,  # Default value
            "buy_price": buy_price,
            "sell_price": sell_price,
            "profit_ratio": profit_ratio,
            "order_id": order_id,
            "byued_quantity": byued_quantity,
            "balance": balance,
            "down_ratio": down_ratio,
            "enable_buy": enable_buy,
            "open_price": open_price
        }
        with open(APP_DATA_FILE_NAME, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print("Exceptionn Writing app data ", e)
        logger.write_msg(current_timestamp, f"error while writing appdata. {e}")
        
        # remove the appdata file
        if os.path.exists(APP_DATA_FILE_NAME):
            os.remove(APP_DATA_FILE_NAME)

def load_app_status():
    global order_status, buy_price, sell_price, profit_ratio, order_id, byued_quantity, balance, down_ratio, enable_buy, open_price, current_timestamp
    try:
        if os.path.exists(APP_DATA_FILE_NAME):
            with open(APP_DATA_FILE_NAME, "r") as file:
                loaded_data = json.load(file)
                print(loaded_data)
                # Assign loaded data to variables
                order_status = OrderStatus(loaded_data.get("order_status", order_status))
                buy_price = loaded_data.get("buy_price", buy_price)
                sell_price = loaded_data.get("sell_price", sell_price)
                profit_ratio = loaded_data.get("profit_ratio", profit_ratio)
                order_id = loaded_data.get("order_id", order_id)
                byued_quantity = loaded_data.get("byued_quantity", byued_quantity)
                balance = loaded_data.get("balance", balance)
                down_ratio = loaded_data.get("down_ratio", down_ratio)
                enable_buy = loaded_data.get("enable_buy", enable_buy)
                # open_price = loaded_data.get("open_price", open_price)
                
                
            print("Data loaded successfully!")
        else:
            print("Data file not found. Using default values.")
    except Exception as e:
        logger.write_msg(current_timestamp, "Error, failed to load app data from file. using default data.")
        if os.path.exists(APP_DATA_FILE_NAME):
            os.remove(APP_DATA_FILE_NAME)

# main1: buy at open, then sell when currency goes up by profit_ratio
# def __main__(current_timestamp):
#     global enable_buy, open_price, order_status, balance, byued_quantity, order_id, sell_price, buy_price, trading_balance

#     try:
#         # if new frame started
#         if current_timestamp % frame_duration_sec == 0:
            
#             update_orders_status(trading_currency, order_id)
            
#             # if the previous sell order filled
#             if order_status == OrderStatus.SELLED:
                
#                 # try to get price 10 times
#                 price = mexc_api.get_open_price(trading_currency, frame_type)
#                 for i in range(10):
#                     if price is None:
#                         price = mexc_api.get_open_price(trading_currency, frame_type)
#                 if price is None:
#                     return
                
#                 # set buy order, try 3 times
#                 success, _order_id, _quantity = mexc_api.set_buy_order(trading_currency, price, trading_balance)
#                 for i in range(3):
#                     if not success:
#                         success, _order_id, _quantity = mexc_api.set_buy_order(trading_currency, price, trading_balance)
                    
#                 if success:
#                     order_id = _order_id
#                     order_status = OrderStatus.WAITING_BUY
#                     buy_price = price
#                     byued_quantity = _quantity
#                     logger.write_action(current_timestamp, "buy", trading_balance, price, frame_type, "set")
                
#                 else:
#                     logger.write_msg(current_timestamp, "Warning, buy not setted.")
            
#             elif order_status == OrderStatus.WAITING_SELL:
#                 logger.write_msg(current_timestamp, "error, sell wasn't complete")
        
        
#         # set sell after buy filled
#         if order_status == OrderStatus.BUYED:
#             sell_price = buy_price + buy_price * profit_ratio
            
#             # set sell order
#             success, _order_id = mexc_api.set_sell_order(trading_currency, sell_price, byued_quantity)
#             if success:
#                 order_id = _order_id
#                 order_status = OrderStatus.WAITING_SELL
#                 logger.write_action(current_timestamp, "sell", byued_quantity, price, frame_type, "set")
                
#             else:
#                 logger.write_msg(current_timestamp, "Warning, sell not setted.")


#         # check if buy or sell filled
#         if order_status == OrderStatus.WAITING_BUY or order_status == OrderStatus.WAITING_SELL:
#             update_orders_status(trading_currency, order_id)
            
#             #log status if changed
#             if order_status == OrderStatus.SELLED:
#                 balance = balance + quantity * sell_price - trading_balance # subtract trading_balance which i used to buy the quantity
#                 logger.write_balance(current_timestamp, balance)
#                 logger.write_action(current_timestamp, "sell", byued_quantity, buy_price, frame_type, "done")
#             elif order_status == OrderStatus.BUYED:
#                 logger.write_action(current_timestamp, "buy", trading_balance, buy_price, frame_type, "done")
    
#     except Exception as e:
#         print(e)
#         logger.write_msg(current_timestamp, f"exception, {e}"")

# main2: buy when price goes down open by down_ratio before gets up the open, 
# then sell when curency goes up open by up_ratio (up_ratio + down_ratio = profit_ratio, up_ratio = down_ratio)
def __main__(current_timestamp):
    global enable_buy, open_price, order_status, balance, byued_quantity, order_id, sell_price, buy_price, trading_balance
    
    try:
        # if new candle started
        _candle_start_time = mexc_api.get_last_candlestick_timestamp(trading_currency, frame_type)
        
        if _candle_start_time is not None and _candle_start_time != last_candle_start_time:
            enable_buy = True
            open_price = mexc_api.get_open_price(trading_currency, frame_type)
            logger.write_msg(current_timestamp, "Info, buy enabled")
            
        # try to get open price if it's none
        if open_price is None:
            open_price = mexc_api.get_open_price(trading_currency, frame_type)
            if open_price is None:            
                logger.write_msg(current_timestamp, "Error, can't get open price")
                return
            logger.write_msg(current_timestamp, f"Info, open price gotten, it's {open_price}")
        
        # control buying
        if enable_buy:
            # try to buy whenever a new the new frame started
            target_buy_price = open_price * (1 - down_ratio)
            current_price = mexc_api.get_current_price(trading_currency)
            
            # don't buy from this frame if the price goes up the open before it goes down
            # if current_price is not None and current_price > open_price:
            #     enable_buy = False
            #     logger.write_msg(current_timestamp, f"Info, buy disabled. current_price {current_price} is greater than open_price {open_price}.")
            
            # if the previous sell order filled
            if order_status == OrderStatus.SELLED:
                if current_price is not None and target_buy_price is not None and current_price <= target_buy_price:
                    target_buy_price = round(target_buy_price , 9)
                    current_price = round(current_price, 9)
                
                    logger.write_msg(current_timestamp, f"Info, trying to buy at price {current_price}. Price reached down target price {target_buy_price}.")
                    
                    # set buy order, try 3 times
                    success, _order_id, _quantity = mexc_api.set_buy_order(trading_currency, current_price, trading_balance)
                    for i in range(3):
                        if not success:
                            success, _order_id, _quantity = mexc_api.set_buy_order(trading_currency, current_price, trading_balance)
                    if success:
                        order_id = _order_id
                        order_status = OrderStatus.WAITING_BUY
                        buy_price = current_price
                        byued_quantity = _quantity
                        logger.write_action(current_timestamp, "buy", trading_balance, current_price, frame_type, "set")
                        logger.write_msg(current_timestamp, f"Info, buy order setted at {current_price}.")
                    else:
                        logger.write_msg(current_timestamp, "Warning, failed to set buy order.")
            
            #if previous sell order didn't fill, then skip buy in this candle 
            elif order_status == OrderStatus.WAITING_SELL:
                logger.write_msg(current_timestamp, "error, previous sell order didn't fill. Don't buy at this candle.")
                enable_buy = False

        # set sell after buy filled
        if order_status == OrderStatus.BUYED:
            sell_price = round(buy_price * (1 + profit_ratio), 9)
            logger.write_msg(current_timestamp, f"Info, trying to sell at {sell_price}. Buy done, setting sell order.")
            
            # set sell order
            success, _order_id = mexc_api.set_sell_order(trading_currency, sell_price, byued_quantity)
            if success:
                order_id = _order_id
                order_status = OrderStatus.WAITING_SELL
                logger.write_action(current_timestamp, "sell", byued_quantity, sell_price, frame_type, "set")
                logger.write_msg(current_timestamp, f"Info, sell order setted at {sell_price}.")
                
            else:
                logger.write_msg(current_timestamp, "Warning, failed to set sell order.")

        # check if buy or sell filled
        if order_status == OrderStatus.WAITING_BUY or order_status == OrderStatus.WAITING_SELL:
            update_orders_status(trading_currency, order_id)
            
            #log status if changed
            if order_status == OrderStatus.SELLED:
                balance = balance + byued_quantity * sell_price - trading_balance # subtract trading_balance which i used to buy the quantity
                logger.write_balance(current_timestamp, balance)
                logger.write_action(current_timestamp, "sell", byued_quantity, sell_price, frame_type, "done")
                logger.write_msg(current_timestamp, "Info, sell order filled.")
            elif order_status == OrderStatus.BUYED:
                logger.write_action(current_timestamp, "buy", trading_balance, buy_price, frame_type, "done")
                logger.write_msg(current_timestamp, "Info, buy order filled.")
    
    except Exception as e:
        print(e)
        logger.write_msg(current_timestamp, f"exception, {e}")


# main3: wait for candle start, then, buy at (candle_open - down_ratio), then sell at (candle_open + profit_ratio)
# note: profit_ratio = up_ratio + down_ratio, up_ratio = down_ratio
# def __main__(current_timestamp):
#     global open_price, order_status, balance, byued_quantity, order_id, sell_price, buy_price, trading_balance
    
#     try:
#         # if new frame started
#         if current_timestamp % frame_duration_sec == 0:
#             open_price = mexc_api.get_open_price(trading_currency, frame_type)
#             logger.write_msg(current_timestamp, "Info, buy enabled")
            
#         # try to get open price if it's none
#         if open_price is None:
#             open_price = mexc_api.get_open_price(trading_currency, frame_type)
#             if open_price is None:            
#                 logger.write_msg(current_timestamp, "Error, can't get open price")
#                 return
#             logger.write_msg(current_timestamp, f"Info, open price gotten, it's {open_price}")
        
#         # control buying
#         # if the previous sell order filled
#         if order_status == OrderStatus.SELLED:
#             target_buy_price = open_price * (1 - down_ratio)
#             current_price = mexc_api.get_current_price(trading_currency)
            
#             if current_price is not None and target_buy_price is not None and current_price <= target_buy_price:
#                 target_buy_price = round(target_buy_price, 9)
#                 current_price = round(current_price, 9)
                
#                 logger.write_msg(current_timestamp, f"Info, trying to buy at price {current_price}. Price reached down target price {target_buy_price}.")
                
#                 # set buy order
#                 success, _order_id, _quantity = mexc_api.set_buy_order(trading_currency, current_price, trading_balance)
#                 if success:
#                     order_id = _order_id
#                     order_status = OrderStatus.WAITING_BUY
#                     buy_price = current_price
#                     byued_quantity = _quantity
#                     logger.write_action(current_timestamp, "buy", trading_balance, current_price, frame_type, "set")
#                     logger.write_msg(current_timestamp, f"Info, buy order setted at {current_price}.")
#                 else:
#                     logger.write_msg(current_timestamp, "Warning, failed to set buy order.")


#         # set sell after buy filled
#         if order_status == OrderStatus.BUYED:
#             sell_price = round(buy_price * (1 + profit_ratio), 9)
#             logger.write_msg(current_timestamp, f"Info, trying to sell at {sell_price}. Buy done, setting sell order.")
            
#             # set sell order
#             success, _order_id = mexc_api.set_sell_order(trading_currency, sell_price, byued_quantity)
#             if success:
#                 order_id = _order_id
#                 order_status = OrderStatus.WAITING_SELL
#                 logger.write_action(current_timestamp, "sell", byued_quantity, sell_price, frame_type, "set")
#                 logger.write_msg(current_timestamp, f"Info, sell order setted at {sell_price}.")
                
#             else:
#                 logger.write_msg(current_timestamp, "Warning, failed to set sell order.")

#         # check if buy or sell filled
#         if order_status == OrderStatus.WAITING_BUY or order_status == OrderStatus.WAITING_SELL:
#             update_orders_status(trading_currency, order_id)
            
#             #log status if changed
#             if order_status == OrderStatus.SELLED:
#                 balance = balance + byued_quantity * sell_price - trading_balance # subtract trading_balance which i used to buy the quantity
#                 logger.write_balance(current_timestamp, balance)
#                 logger.write_action(current_timestamp, "sell", byued_quantity, sell_price, frame_type, "done")
#                 logger.write_msg(current_timestamp, "Info, sell order filled.")
            
#             elif order_status == OrderStatus.BUYED:
#                 logger.write_action(current_timestamp, "buy", trading_balance, buy_price, frame_type, "done")
#                 logger.write_msg(current_timestamp, "Info, buy order filled.")
    
#     except Exception as e:
#         print(e)
#         logger.write_msg(current_timestamp, f"exception, {e}")




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

# get open price at startup
open_price = mexc_api.get_open_price(trading_currency, frame_type)

while True:
    # Get the current timestamp, take the integer part (without milliseconds)
    current_timestamp = int(datetime.now().timestamp())
    try:
        _indx = (_indx % 60) + 1
        print(_indx)
        # check internet connection every 3 minutes,
        # but don't check if we are at the start of new frame
        if _indx % 60 == 0 and current_timestamp % frame_duration_sec != 0:
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
        logger.write_msg(current_timestamp, f"{ex}")
        time.sleep(1)
