import json
import csv
import os
import sys
import uuid
import random
import toml
import time
import math
from datetime import datetime, timedelta
from eth_account import Account
from web3 import Web3
from web3._utils.events import get_event_data
from web3._utils.abi import (
    filter_by_type
)
from eth_utils import (
    event_abi_to_log_topic,
)

# 設定ファイル読み込み
CONFIG = toml.load(open('./config.toml', encoding="utf-8"))
# 接続方式確立
if CONFIG['web3']['mode'] == 'HTTP':
    W3 = Web3(Web3.HTTPProvider(CONFIG['web3']['http']['url'], request_kwargs={'timeout': CONFIG['web3']['http']['timeout']}))
elif CONFIG['web3']['mode'] == 'WEBSOCKET':
    W3 = Web3(Web3.WebsocketProvider(CONFIG['web3']['websocket']['url'], websocket_kwargs={'timeout': CONFIG['web3']['websocket']['timeout']}))

# ABIの読込
base = os.path.dirname(os.path.abspath(__file__))
abiName = os.path.normpath(os.path.join(base, './SecuritiesTrading.json'))
with open(abiName, encoding="utf-8") as f:
    abi = json.load(f)

# 市場コントラクトのインスタンスを生成
CONTRACT_ADDRESS = W3.toChecksumAddress(CONFIG['trading']['contract'])
CONTRACT = W3.eth.contract(CONTRACT_ADDRESS, abi=abi)

def createCsv(filename, functionName, dataHeader, dataList):
    # 作成したリストをcsvファイルに書き込む
    with open('./csv/'+filename+'.csv', "w") as csvData:
        writerData = csv.writer(csvData, lineterminator='\n') # 改行コード（\n）を指定しておく
        writerData.writerow(['data', 'value', 'to']) # ヘッダー作成

        # 作成したテストデータの変数リストをcsvファイルに書き込む
        with open('./csv/'+filename+'_decode.csv', "w") as csvDecode:
            writerDecode = csv.writer(csvDecode, lineterminator='\n') # 改行コード（\n）を指定しておく
            writerDecode.writerow(dataHeader) # ヘッダー作成

            for data in dataList:
                # data作成
                transaction_data = CONTRACT.encodeABI(fn_name=functionName, args=data)

                writerData.writerow([transaction_data, 0, CONFIG['trading']['contract']])
                writerDecode.writerow(data)
