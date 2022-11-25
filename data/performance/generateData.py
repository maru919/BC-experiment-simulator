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

# 共通部分をダウンロード
import generateCsv

# 設定ファイル読み込み
CONFIG = toml.load(open('./config.toml', encoding="utf-8"))

def createToken(tokenNumber, inputPrice):
    # ヘッダー作成
    header = ['tokenId', 'tokenName', 'price', 'tokenTypeId', 'updateTime']
    dataList = []

    # トランザクション作成
    argTag = '0x' + (datetime.now().strftime("%Y%m%d%H%M%S").ljust(64, '0'))
    price = inputPrice * CONFIG['trading']['threshold']
    create_time = int(datetime.now().timestamp())

    for i in range(1, tokenNumber + 1):
        # トークンID
        token_id = argTag[:len(argTag) - len(str(i))] + str(i)
        token_name = 'ST{:0=5}'.format(i)

        dataList.append([token_id, token_name, price, CONFIG['trading']['tokenType'], create_time])

    return header, dataList

def updateToken(csvFileName, inputPrice):
    header = ['tokenId', 'price', 'updateTime']
    dataList = []

    # トークンリストの読み込み
    csvfile = open(csvFileName, 'r', encoding="utf-8")
    reader = csv.reader(csvfile)
    next(reader) # ヘッダーを読み飛ばす

    price = inputPrice * CONFIG['trading']['threshold']
    update_time = int(datetime.now().timestamp())

    for data in reader:
        dataList.append([data[0], price, update_time])

    return header, dataList


def generateToken(csvFileName, addAmount):
    header = ['tokenId', 'addAmount', 'userId']
    dataList = []

    # トークンリストの読み込み
    csvfile = open(csvFileName, 'r', encoding="utf-8")
    reader = csv.reader(csvfile)
    next(reader) # ヘッダーを読み飛ばす

    for data in reader:
        dataList.append([data[0], addAmount, CONFIG['trading']['lender']])

    return header, dataList

# def createTrading(csvFileName):
#     header = ['tradingId', 'lender', 'borrowerTokenIds', 'lenderTokenIds', 'borrowerTokenAmounts', 'lenderTokenAmounts', 'startTime', 'finishTime', 'rate', 'adjustmentToken']
#     dataList = []

#     # トークンリストの読み込み
#     csvfile = open(csvFileName, 'r', encoding="utf-8")
#     reader = csv.reader(csvfile)
#     next(reader) # ヘッダーを読み飛ばす

#     # トランザクション作成
#     # タグ
#     argTag = '0x' + (datetime.now().strftime("%Y%m%d%H%M%S").ljust(64, '0'))
 
#     start_time = int(datetime.now().timestamp())
#     finish_time = int(datetime.now().timestamp() + 3600)

#     rate = 100

#     for i, Data in enumerate(reader):
#         # テスタデータ用パラメータ作成
#         # トークンID
#         trading_id = argTag[:len(argTag) - len(str(i))] + str(i)

#         dataList.append([ trading_id, CONFIG['trading']['lender'] , [CONFIG['trading']['jct']], [Data[0]],[1000], [10],start_time,finish_time,rate, CONFIG['trading']['jct']])

#     return header, dataList

def createTrading(csvFileName, tradingNumber, tokentypeNumber, stMax, sumPrice):
    header = ['tradingId', 'lender', 'borrowerTokenIds', 'lenderTokenIds', 'borrowerTokenAmounts', 'lenderTokenAmounts', 'startTime', 'finishTime', 'rate', 'adjustmentToken']
    dataList = []

    # トークンリストの読み込み
    csvfile = open(csvFileName, 'r', encoding="utf-8")
    reader = csv.reader(csvfile)
    next(reader) # ヘッダーを読み飛ばす

    # トランザクション作成
    argTag = '0x' + (datetime.now().strftime("%Y%m%d%H%M%S").ljust(64, '0'))
 
    start_time = int(datetime.now().timestamp())
    finish_time = int(datetime.now().timestamp() + 3600)

    rate = 100
    fixNumber = 0
    valiableNumber = 1

    data = []
    price = []
    dataUse = []
    #csvファイルのデータをループ
    for row in reader:
        data.append(str(row[0]))
        price.append(int(row[2]))
        dataUse.append(0)

    for i in range(1, tradingNumber + 1):
        # テスタデータ用パラメータ作成
        # トークンID
        trading_id = argTag[:len(argTag) - len(str(i))] + str(i)

        tokenList = []
        amountList = []
        tokenList.append(data[fixNumber])
        amountList.append(int(sumPrice * CONFIG['trading']['threshold'] / tokentypeNumber / price[fixNumber])) 
        dataUse[fixNumber] = dataUse[fixNumber] + 1
        if dataUse[fixNumber] >= stMax:
            fixNumber = fixNumber + 1

        for j in range(tokentypeNumber - 1):
            tokenList.append(data[valiableNumber])
            amountList.append(int(sumPrice * CONFIG['trading']['threshold'] / tokentypeNumber / price[valiableNumber])) 
            dataUse[valiableNumber] = dataUse[valiableNumber] + 1
            valiableNumber = valiableNumber + 1
            if valiableNumber >= len(data):
                valiableNumber = fixNumber + 1
            
        dataList.append([ trading_id, CONFIG['trading']['lender'] , [CONFIG['trading']['jct']], tokenList,[sumPrice], amountList,start_time,finish_time,rate, CONFIG['trading']['jct']])

    return header, dataList

def acceptTrading(csvFileName):
    header = ['tradingId']
    dataList = []

    # トークンリストの読み込み
    csvfile = open(csvFileName, 'r', encoding="utf-8")
    reader = csv.reader(csvfile)
    next(reader) # ヘッダーを読み飛ばす

    for data in reader:
        # テスタデータ用パラメータ作成
        dataList.append([data[0]])

    return header, dataList

# 1:function name 
# 2以降:関数に応じた引数
if __name__ == "__main__":
    args = sys.argv
    functionName = args[1]

    if functionName == 'createToken':
        header,dataList = createToken(int(args[2]), int(args[3]))
    elif functionName == 'updateToken':
        header,dataList = updateToken(args[2], int(args[3]))
    elif functionName == 'generateToken':
        header,dataList = generateToken(args[2], int(args[3]))
    elif functionName == 'createTrading':
        header,dataList = createTrading(args[2], int(args[3]), int(args[4]), int(args[5]), int(args[6]))
    elif functionName == 'acceptTrading':
        header,dataList = acceptTrading(args[2])
    else:
        sys.exit()

    generateCsv.createCsv(functionName,functionName,header,dataList)
