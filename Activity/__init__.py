# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
import requests
import datetime

import pandas as pd
import numpy as np

def smma(src, length):
    smma = pd.Series(index=src.index)

    for i in range(len(src)):
        if pd.isna(smma.iloc[i-1]):
            smma.iloc[i] = np.mean(src.iloc[:i+1])
        else:
            smma.iloc[i] = (smma.iloc[i-1] * (length - 1) + src.iloc[i]) / length

    return smma

def get_pair_status(symbol):

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1w"
    data = None

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()


    df = pd.DataFrame(data)
    df.columns = ['open_time', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'close_time', ' quote_asset_volume', 'orders', 'irl1', 'irl2', 'irl3']
  
    df['hl2'] = (df['high_price'].astype(float) + df['low_price'].astype(float)) / 2

    v1 = smma(df['hl2'], 15).iloc[-1]
    m1 = smma(df['hl2'], 19).iloc[-1]
    v2 = smma(df['hl2'], 29).iloc[-1]
    m2 = smma(df['hl2'], 25).iloc[-1]

    p2 = (v1 < m1) != (v1 < v2) or (m2 < v2) != (v1 < v2)
    p3 = not p2 and v1 < v2
    p1 = not p2 and not p3

    c = "green" if p1 else "gray" if p2 else "red"

    return c

def get_trading_pair_details(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1w"
    logging.info(url)

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if len(data)>104:
            return [data[-2][4], data[-2][5], data[-2][6], len(data)]
    
    return None

def main(pairs: list) -> list:

    trading_pairs = list()
    for pair in pairs:

        pair_details = get_trading_pair_details(pair)
        if pair_details is None:
            continue

        timestamp = str(pair_details[2])[:10]
        date =  datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
        
        p = {"Symbol": pair , "Status":  get_pair_status(pair), "Date": date , "Price": pair_details[0].rstrip('0'), "Volume": pair_details[1].split(".")[0] , "ChartAge": pair_details[3] }
  
        trading_pairs.append(p)

    return trading_pairs
