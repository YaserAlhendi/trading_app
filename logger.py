import os
from datetime import datetime

msg_filename = "msgs.txt"
actions_filename = "Actions.csv"
balance_fileName = "Balance.txt"

def init_log():
    global msg_filename, actions_filename, balance_fileName
    with open("log/inc.txt", "r+") as file:
        _indx = int(file.readline().strip())
        msg_filename = f"{_indx}_{msg_filename}"
        actions_filename = f"{_indx}_{actions_filename}"
        balance_fileName = f"{_indx}_{balance_fileName}"
        file.seek(0)
        file.write(str(_indx + 1))
        file.truncate()

def write_msg(time_stamp, msg):
    datetime_obj = datetime.fromtimestamp(time_stamp)
    # Format the datetime as YY:MM:DD:hh:mm:ss
    formatted_datetime = datetime_obj.strftime("%y:%m:%d:%H:%M:%S")
    
    with open("log/" + msg_filename, "a") as file:
        file.write(f"{formatted_datetime}: {msg}\n")

def write_action(time_stamp, action, amount, price, frame_type, status):
    datetime_obj = datetime.fromtimestamp(time_stamp)
    # Format the datetime as YY:MM:DD:hh:mm:ss
    formatted_datetime = datetime_obj.strftime("%y:%m:%d:%H:%M:%S")
    
    # Write an action to the actions log file
    with open("log/" + actions_filename, "a") as file:
        file.write(f"{formatted_datetime},{action},{amount},{price},{frame_type},{status}\n")

def write_balance(time_stamp, balance):
    datetime_obj = datetime.fromtimestamp(time_stamp)
    # Format the datetime as YY:MM:DD:hh:mm:ss
    formatted_datetime = datetime_obj.strftime("%y:%m:%d:%H:%M:%S")
    
    with open("log/" + balance_fileName, "a") as file:
        file.write(f"{formatted_datetime}: {balance}\n")