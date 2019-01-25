# encoding: UTF-8

"""
本模块中主要包含：
1. 从wind下载历史行情,并且把数据导入到mongodb中
"""

from datetime import datetime, timedelta
from time import time
from multiprocessing.pool import ThreadPool

import pymongo

from vnpy.data.datayes import DatayesApi
from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtConstant import *
from vnpy.trader.vtObject import VtBarData

from WindPy import w
from datetime import *
import MySQLdb
import multiprocessing
from time import sleep

import pandas as pd
pd.set_option('display.height',1000)
pd.set_option('display.max_rows',500)
pd.set_option('display.max_columns',500)
pd.set_option('display.width',1000)

import multiprocessing
from time import sleep
from datetime import datetime, time
from vnpy.trader.vtEngine import MainEngine, LogEngine


#----------------------------------------------------------------------
def getWindData(InstrumentCode):
    """取指数数据"""
    w.start()
    w.start(waitTime=60)

    # IndexData = w.wsd(InstrumentCode, "open,high,low,close", beginDate, endDate, "Period=D")

    # IndexData = w.wsi(InstrumentCode, "open,high,low,close,volume,oi", "2017-11-01 09:00:00", datetime.today(), "")
    IndexData = w.wsi(InstrumentCode, "open,high,low,close,volume,oi", datetime.today() - timedelta(10), datetime.today(), "")


    df_IndexData = pd.DataFrame(IndexData.Data,index=['Open','High','Low','Close','volume','oi'],columns=IndexData.Times)
    df_IndexData = df_IndexData.T
    df_IndexData = df_IndexData.dropna(axis=0,how='any')
    # df_IndexData['InstrumentName'] = InstrumentName
    df_IndexData['Date'] =  df_IndexData.index
    df_IndexData = df_IndexData.reset_index(drop=True)

    print df_IndexData
    bartime = df_IndexData.loc[0,'Date']
    print bartime
    print type(bartime)
    print bartime.strftime('%Y%m%d')
    print bartime.strftime('%H:%M:%S')


    return  df_IndexData

#----------------------------------------------------------------------
def loadWindCsv(db_bar, dbName, symbol):
    """将wind的历史分钟数据插入到Mongo数据库中"""


    start = time()
    print u'开始读取%s的wind数据' %(symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    # 读取数据和插入到数据库
    for i in range(len(db_bar)):
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(db_bar.loc[i,'Open'])
        bar.high = float(db_bar.loc[i,'High'])
        bar.low = float(db_bar.loc[i,'Low'])
        bar.close = float(db_bar.loc[i,'Close'])
        bar.datetime = (db_bar.loc[i,'Date'])
        bar.date = bar.datetime.strftime('%Y%m%d')
        bar.time = bar.datetime.strftime('%H:%M:%S')
        bar.volume = float(db_bar.loc[i,'volume'])
        bar.openInterest = float(db_bar.loc[i,'oi'])

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
        print bar.date, bar.time

    print u'插入完毕'


#----------------------------------------------------------------------
def loadWindCsv_Day(db_bar, dbName, symbol):
    """将wind的历史分钟数据插入到Mongo数据库中"""


    start = time()
    print u'开始读取%s的wind数据' %(symbol)

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    # 读取数据和插入到数据库
    for i in range(len(db_bar)):
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(db_bar.loc[i,'Open'])
        bar.high = float(db_bar.loc[i,'High'])
        bar.low = float(db_bar.loc[i,'Low'])
        bar.close = float(db_bar.loc[i,'Close'])
        bar.datetime = (db_bar.loc[i,'Date'].strftime('%Y-%m-%d'))
        bar.date = bar.datetime
        # bar.time = bar.datetime.strftime('%H:%M:%S')
        # bar.volume = float(db_bar.loc[i,'volume'])
        # bar.openInterest = float(db_bar.loc[i,'oi'])

        print bar.datetime
        print type(bar.datetime)

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
        # collection.update_one({}, {'$set':bar.__dict__}, upsert=True)
        print bar.date, bar.time

    print u'插入完毕'

#----------------------------------------------------------------------
def getIndexData(InstrumentName,InstrumentCode,beginDate,endDate):
    """取指数数据"""
    w.start()
    w.start(waitTime=60)

    IndexData = w.wsd(InstrumentCode, "open,high,low,close", beginDate, endDate, "Period=D")
    df_IndexData = pd.DataFrame(IndexData.Data,index=['Open','High','Low','Close'],columns=IndexData.Times)
    df_IndexData = df_IndexData.T
    df_IndexData['InstrumentName'] = InstrumentName
    df_IndexData['Date'] =  df_IndexData.index
    df_IndexData = df_IndexData.reset_index(drop=True)

    return  df_IndexData

def runChildProcess():
    InstrumentList = [
                        ['rb',	'RBFI.WI',	'S0033227'],
                        ['ru',	'RUFI.WI',	'S5016816'],
                        ['i',	'IFI.WI',	'S5704666'],
                        ['j',	'JFI.WI',	'S0033507'],
                    ]

    for InstrumentInfo in InstrumentList:
        #设置需要读的内容和时间
        InstrumentName = InstrumentInfo[0]
        InstrumentCode = InstrumentInfo[1]
        # beginDate = "2010-01-01"
        # 刷新最近10天的数据到数据库中
        beginDate = datetime.today() - timedelta(days = 365* 6)
        endDate = datetime.today()

        """1. 操作指数数据"""
        #开始读取指数数据
        df_IndexData = getIndexData(InstrumentName,InstrumentCode,beginDate,endDate)
        print df_IndexData
        #并且写入指数数据库
        # loadWindCsv_Day(df_IndexData, 'VnTrader_Day_Db', InstrumentName+'09')


    # ##########################################
    # db_bar = getWindData("rb1805.SHF")
    # loadWindCsv(db_bar, 'VnTrader_1Min_Db', 'rb1805')
    #
    # db_bar = getWindData("ru1805.SHF")
    # loadWindCsv(db_bar, 'VnTrader_1Min_Db', 'ru1805')
    #
    # db_bar = getWindData("i1805.DCE")
    # loadWindCsv(db_bar, 'VnTrader_1Min_Db', 'i1805')
    #
    # db_bar = getWindData("j1805.DCE")
    # loadWindCsv(db_bar, 'VnTrader_1Min_Db', 'j1805')
    # ##########################################



#----------------------------------------------------------------------
def runParentProcess():
    """父进程运行函数"""
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()

    le.info(u'启动更新数据库进程')

    DAY_START = time(8, 10)         # 日盘启动和停止时间
    DAY_END = time(8, 35)

    NIGHT_START = time(20, 10)      # 夜盘启动和停止时间
    NIGHT_END = time(20, 35)

    p = None        # 子进程句柄

    while True:
        currentTime = datetime.now().time()
        recording = False

        # 判断当前处于的时间段
        if ((currentTime >= DAY_START and currentTime <= DAY_END) or
            (currentTime >= NIGHT_START and currentTime <= NIGHT_END)
            ):
            recording = True

        # 记录时间则需要启动子进程
        if recording and p is None:
            le.info(u'启动子进程')
            p = multiprocessing.Process(target=runChildProcess)
            p.start()
            le.info(u'子进程启动成功')

        # 非记录时间则退出子进程
        if not recording and p is not None:
            le.info(u'关闭子进程')
            p.terminate()
            p.join()
            p = None
            le.info(u'子进程关闭成功')

        sleep(10)


if __name__ == '__main__':
    runChildProcess()

    # 尽管同样实现了无人值守，但强烈建议每天启动时人工检查，为自己的PNL负责
    # runParentProcess()









