#通道突破是技术分析中一个判断趋势的重要方法,其观念在于市场价格穿透了之前的价格压力或支撑,
#继而形成一股新的趋势,而交易策略的目标即是在突破发生时能够确认并建立仓位以获取趋势的利润.
'''
1.均线百分比通道：  Upper=MA*1.03   Lower=MA*0.97
2.布林带通道:  Upper=MA+2σ   Lower=MA-2σ   (σ表示波动率,即标准差)
#3.平均波幅通道:  Upper=MA+ATR   Lower=MA-ATR  (ATR 表示平均波幅的一个幅度)
4.高低价通道: Upper=MAX(High,20)   Lower=Min(LOW,20)
'''

#加载:
from jaqs.data import DataView
from jaqs.data import RemoteDataService
import os
import numpy as np
import talib as ta
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
import talib.abstract as abstract

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

def change_index(df): #调整时间索引
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df
data = change_index(dv.get_ts('close_adj').loc[20170105:]) #A=dv.get_ts('close_adj').loc[20170105:]

#example1:均线百分比通道
middleband = ta.abstract.MA(data, timeperiod=20, price='600036.SH') #求均线
upperband = middleband*1.03
lowerband = middleband*0.97
data_B = pd.concat([middleband, upperband , lowerband], axis=1) #将三条均线合并在一个dataframe中
data_B.columns = ['middleband','upperband','lowerband']

plt.figure(figsize=(15,7))
plt.plot(data['600036.SH'])
plt.plot(data_B['middleband'], 'r', alpha=0.3)
plt.plot(data_B['upperband'], 'g', alpha=0.3)
plt.plot(data_B['lowerband'], 'g', alpha=0.3)
plt.show()

#example2:布林带通道     ta.abstract.BBANDS()布林带通道 ,注意波动率的缩小和扩大对布林线有巨大的影响
data_B= ta.abstract.BBANDS(data, timeperiod=20, price='600036.SH') 
plt.figure(figsize=(15,7))
plt.plot(data['600036.SH'])
plt.plot(data_B['middleband'], 'r', alpha=0.3)
plt.plot(data_B['upperband'], 'g', alpha=0.3)
plt.plot(data_B['lowerband'], 'g', alpha=0.3)
plt.show()

#example3:平均波幅率通道线
high = change_index(dv.get_ts('high_adj').loc[20170105:])['600036.SH']
low = change_index(dv.get_ts('low_adj').loc[20170105:])['600036.SH']
stock = pd.concat([high,low,data['600036.SH']],axis=1)
stock.columns=['high','low','close'] #修改列名
'''
A=dv.get_ts('high_adj').loc[20170105:]
B=change_index(dv.get_ts('high_adj').loc[20170105:])
C=change_index(dv.get_ts('high_adj').loc[20170105:])['600036.SH']
'''

atr = ta.abstract.ATR(stock, 20) #根据最高,最低价求ATR波幅
middleband = ta.abstract.MA(data, 20, price='600036.SH') #求均线
upperband = middleband + atr
lowerband = middleband - atr
data_B = pd.concat([middleband, upperband, lowerband], axis=1)
data_B.columns = ['middleband', 'upperband', 'lowerband']

plt.figure(figsize=(15,7))
plt.plot(data['600036.SH'])
plt.plot(data_B['middleband'], 'r', alpha=0.3)
plt.plot(data_B['upperband'], 'g', alpha=0.3)
plt.plot(data_B['lowerband'], 'g', alpha=0.3)
plt.show()

#example4：高低价通道
upperband = ta.abstract.MAX(stock, 20, price='high') #求20日最高价(针对high列)
lowerband = ta.abstract.MIN(stock, 20, price='low')  #求20日最低价(针对low列)
middleband = (upperband+lowerband)/2
data_B = pd.concat([middleband, upperband, lowerband], axis=1)
data_B.columns = ['middleband', 'upperband', 'lowerband']

plt.figure(figsize=(15,7))
plt.plot(data['600036.SH'])
plt.plot(data_B['middleband'], 'r', alpha=0.3)
plt.plot(data_B['upperband'], 'g', alpha=0.3)
plt.plot(data_B['lowerband'], 'g', alpha=0.3)
plt.show()



#通道策略：
#1. Bollinger Band通道策略
#Buy：价格突破UpperBand 和 Sigma<0.005(波动率较小)
#Sell：Sigma>0.05 (波动率较大)
# Bollinger Band
# Bollinger Band
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 20

def handle_bar(context, bar_dict):

    prices = history_bars(context.s1, context.PERIOD+2, '1d', 'close')
    upperband, middleband, lowerband = talib.BBANDS(prices, context.PERIOD) #BBANDS布林线算法
    sigma = (upperband[-1]-prices[-1])/(2*prices[-1]) #布林线波动率定义

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if sigma>0.05 and cur_position > 0:
        order_target_value(context.s1, 0)

    if prices[-2]<=upperband[-2] and prices[-1]>=upperband[-1] and sigma<0.005:
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)



#2.ATR_Channel_1通道策略    Upper=MA+ATR;Lower=MA-ATR (ATR 表示平均波幅的一个幅度)
# Buy ： 价格突破upperBand
# Sell: 价格跌穿lowerband
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 20


def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.PERIOD+1, '1d', 'close')
    high = history_bars(context.s1, context.PERIOD+1, '1d', 'high')
    low = history_bars(context.s1, context.PERIOD+1, '1d', 'low')


    MA = talib.SMA(price, context.PERIOD)
    atr = talib.ATR(high,low,price,timeperiod=context.PERIOD) #ATR计算方式
    upperband = MA[-1]+atr[-1]
    lowerband = MA[-1]-atr[-1]
#     print upperband

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if price[-1] < lowerband and cur_position > 0:
        order_target_value(context.s1, 0)

    if price[-1] > upperband:
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)















#通道策略：
#1. Bollinger Band通道策略修改
#Buy：价格突破UpperBand 和 Sigma<0.005(波动率较小)
#Sell：Sigma>0.05 (波动率较大)
# Bollinger Band
# Bollinger Band
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 20

def handle_bar(context, bar_dict):

    prices = history_bars(context.s1, context.PERIOD+2, '1d', 'close')
    upperband, middleband, lowerband = talib.BBANDS(prices, context.PERIOD) #BBANDS布林线算法
    sigma = (upperband[-1]-prices[-1])/(2*prices[-1]) #布林线波动率定义

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if sigma>0.05 and cur_position > 0: 
        order_target_value(context.s1, 0)

    if prices[-1]>=upperband[-1] and sigma<0.005 :  #修改地方,原式为if prices[-2]<=upperband[-2] and prices[-1]>=upperband[-1] and sigma<0.005:
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)


