# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
# Before running this sample, please:
# - create a Durable activity function (default name is "Hello")
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import os
import requests
import logging
import json

import azure.functions as func
import azure.durable_functions as df

from jinja2 import Environment, FileSystemLoader


def fetch_all_trading_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        trading_pairs = []
        symbols = data["symbols"]
        for symbol in symbols:
            if symbol["quoteAsset"] == "USDT" or symbol["quoteAsset"] == "BTC" :
                trading_pairs.append(symbol["symbol"])

        return trading_pairs
    else:
        logging.error(f'Failed to fetch all trading pairs. Error: {response.status_code}')
        return None   

def render_static_website(data):

    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + '/templates'), trim_blocks=True)
    template = env.get_template("index.html")
  
    rendered_html = template.render(data=data)

    return rendered_html 

def orchestrator_function(context: df.DurableOrchestrationContext):
    all_pairs = fetch_all_trading_pairs()

    print(len(all_pairs))

    batch_size=50
    number_of_batches=int(len(all_pairs)/batch_size)

    parallel_tasks = [ context.call_activity("Activity",  all_pairs[i * batch_size: min((i + 1) * batch_size, len(all_pairs))]) for i in range(number_of_batches) ]

    outputs = yield context.task_all(parallel_tasks)
    trading_pairs = list()
    for sublist in outputs:
        trading_pairs.extend(sublist)

    # print(trading_pairs)

    website = render_static_website(trading_pairs)
   
    return website

main = df.Orchestrator.create(orchestrator_function)