# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
# Before running this sample, please:
# - create a Durable activity function (default name is "Hello")
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import requests
import logging
import json

import azure.functions as func
import azure.durable_functions as df


def fetch_all_trading_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        trading_pairs = []
        symbols = data["symbols"]
        for symbol in symbols:
            if symbol["quoteAsset"] == "USDT":
                trading_pairs.append(symbol["symbol"])

        return trading_pairs
    else:
        logging.error(f'Failed to fetch all trading pairs. Error: {response.status_code}')
        return None    

def orchestrator_function(context: df.DurableOrchestrationContext):
    all_pairs = fetch_all_trading_pairs()[:10]

    batch_size=2
    number_of_batches=int(len(all_pairs)/batch_size)

    parallel_tasks = [ context.call_activity("Activity",  all_pairs[i * batch_size: min((i + 1) * batch_size, len(all_pairs))]) for i in range(number_of_batches) ]

    outputs = yield context.task_all(parallel_tasks)
    trading_pairs = list()
    for sublist in outputs:
        trading_pairs.extend(sublist)

    print(trading_pairs)
   
    return outputs

main = df.Orchestrator.create(orchestrator_function)