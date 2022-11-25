# -*- coding: utf-8 -*-
# This program is to bid on UrawaMisono Contract which to provide the Market next day every 30 minutes.

import csv
import json
import logging
import logging.config
import os.path
import sys
import time
import traceback

import toml
from eth_account import Account
from eth_utils import event_abi_to_log_topic
from web3 import Web3
from web3._utils.abi import filter_by_type
from web3._utils.events import get_event_data
# 並列処理用
from multiprocessing import Pool
import multiprocessing as multi

# 設定ファイル読み込み
CONFIG = toml.load(open('config.toml',encoding="utf-8"))

# ログ設定
logging.config.fileConfig(CONFIG['log']['config'])
logger = logging.getLogger()
logger.setLevel(10)

# 接続方式確立
if CONFIG['web3']['mode'] == 'HTTP':
    W3 = Web3(Web3.HTTPProvider(CONFIG['web3']['http']['url'], request_kwargs={'timeout': CONFIG['web3']['http']['timeout']}))
elif CONFIG['web3']['mode'] == 'WEBSOCKET':
    W3 = Web3(Web3.WebsocketProvider(CONFIG['web3']['websocket']['url'], websocket_kwargs={'timeout': CONFIG['web3']['websocket']['timeout']}))

def readKeyFile(keyFileName, passwordCode):
    '''
    キーファイルから情報を取得
    '''

    # キーファイルよる情報を取得する
    with open(keyFileName, encoding="utf-8") as f:
        data = json.load(f)
    
    private_key = Web3.toHex(Account.decrypt(data, passwordCode))
    account = Account.privateKeyToAccount(private_key)
    address = account.address
    
    return private_key, address


def createTransaction(private_key, address, reader,timedata):
    """
    トランザクション生成
    """
    # トランザクション生成開始
    logging.log(20, "Start CreateTransaction.")
    timedata['startCretaeTx'] = time.time()

    # nonce値の取得
    nonce = W3.eth.getTransactionCount(W3.toChecksumAddress(address))

    # トランザクション格納用配列
    rawTransaction = []
    
    for Data in reader:
        # テストデータと設定ファイルからトランザクション作成
        transaction = {
                'chainId': CONFIG['tx']['chain_id'],
                'data' : Data[0],
                'nonce': nonce,
                'gas' : CONFIG['tx']['gas'],
                'gasPrice': CONFIG['tx']['gas_price'],
                'value': int(Data[1]),
                'to' : Data[2]
            }

        nonce += 1
        signed = Account.signTransaction(transaction, private_key)    # 署名
        rawTransaction.append(signed.rawTransaction) # 組み立てたトランザクションをリストに追加

    logging.log(20, "End CreateTransaction.")
    timedata['endCretaeTx'] = time.time()

    return rawTransaction,timedata


def sendTransactionmulti(transaction):
    return W3.eth.sendRawTransaction(transaction)

def sendTransaction(transactions,timedata):
    """
    トランザクション送信
    """

    results = []
    receipts = []

    # トランザクション送信開始
    logging.log(20, "Start SendTransactions.")
    timedata['startSendTx'] = time.time()

    # send処理を並列実行
    with Pool(multi.cpu_count()) as p:
        results = p.map(sendTransactionmulti, transactions)

    # for transaction in transactions:
    #     result = W3.eth.sendRawTransaction(transaction)
    #     results.append(result)

    logging.log(20, "End SendTransactions.")
    timedata['endSendTx'] = time.time()

    # 最終レシート確認
    logging.log(20, "Start Get Last Receipt.")
    timedata['startGetTx'] = time.time()

    last_result = results[-1]
    last_receipt_info = {}
    last_receipt = W3.eth.waitForTransactionReceipt(W3.toHex(last_result))
    last_receipt_info['hash'] = Web3.toHex(last_receipt.transactionHash)
    last_receipt_info['status'] = last_receipt.status

    # 最終レシートのステータスを表示
    logging.log(20, "last receipt:"+json.dumps(last_receipt_info))

    logging.log(20, "End Get Last Receipt.")
    timedata['endGetTx'] = time.time()

    #result ALLの場合、レシート一覧の情報を保存
    if CONFIG['log']['result'] == "ALL":
        logging.log(20, "Start Get All Receipt.")
        for result in results:
            receipt_info = {}
            receipt = W3.eth.getTransactionReceipt(W3.toHex(result))
            receipt_info['hash'] = Web3.toHex(receipt.transactionHash)
            receipt_info['status'] = receipt.status
            receipts.append(receipt_info)
        logging.log(20, "End Get All Receipt.")
    
    return receipts,timedata

# 1:CSVファイルパス, 2:keyファイルパス
if __name__ == "__main__":
    try:
        args = sys.argv
        # 各実施時間を記録
        timedata = {}
        # テストデータの読み込み
        csvfile = open(args[1], 'r', encoding="utf-8")
        reader = csv.reader(csvfile)
        next(reader) # ヘッダーを読み飛ばす

        # 秘密鍵とアドレスを取得する
        private_key, address = readKeyFile(args[2], CONFIG['key']['pass'])

        #トランザクション生成
        transactions,timedata = createTransaction(private_key, address, reader,timedata)
        csvfile.close()

        # トランザクション送信
        receipts,timedata = sendTransaction(transactions,timedata)

        # トランザクション送信開始時間と最終レシート受け取り時間の差分を計算
        logging.log(20,"EndGetTime - StartSendTime = " + str(timedata['endGetTx'] - timedata['startSendTx']))

        #result ALLの場合、レシート一覧をcsvに出力する。
        if CONFIG['log']['result'] == "ALL":
            with open(CONFIG['log']['file'], "w", encoding="utf-8", newline="") as f:
                receiptWriter = csv.DictWriter(f, fieldnames=['hash', 'status'])
                receiptWriter.writeheader()
                receiptWriter.writerows(receipts)

    except Exception as e:
        logging.log(20, "Exception Error: %s", e.args)
        logging.log(20, "TraceBack: %s", traceback.format_exc())
