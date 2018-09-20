#关于成交量指标:
'''
1.ADV平均成交量: MA(volume,20)
2.OBV: OBV属于市场的领先指标,计算方法是如果当天价格高于前一天的价格,
当天成交量就用加法,反之就用减法来计算出OBV指标,这样有助于分析成交量与价格的关系。
3.A/D: A/D 指标在OBV的基础上对价格的波幅进行了计算,真实波幅越大,指标中的成交量占比越大。
即A/D=(close-open)/(high-low)*Volume
4.WVAP:按成交量来衡量价格的权重,成交量越大权重也就越大。
即sum(close*volume,20)/sum(volume,20)
'''


#1.先加载
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

def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df



#2.计算与作图
#step1:ADV平均成交量的计算与作图
close = change_index(dv.get_ts('close_adj').loc[20170105:]) #读取后复权价格
volume = change_index(dv.get_ts('volume').loc[20170105:]) #读取成交量

adv10 = ta.abstract.MA(volume, 10, price='600036.SH') #观察下这种计算方式！
adv20 = ta.abstract.MA(volume, 20, price='600036.SH')

fig, (ax, ax1) = plt.subplots(2, 1, sharex=True, figsize=(15,7))
ax.plot(close['600036.SH'], label='600036')
ax.legend(loc='upper left') #loc='upper left'表示位置,同理也可loc='upper right'
ax1.bar(volume.index, volume['600036.SH'],color='g')
ax1.plot(adv10, label='Volume_MA10')
ax1.plot(adv20, label='Volume_MA20')
plt.legend(loc='upper left')
plt.show()

#step2:OBV & A/D的计算与作图
Close = close['600036.SH'].values #clsoe与volume由前面计算得到
Volume = volume['600036.SH'].values
Low = change_index(dv.get_ts('low_adj').loc[20170105:])['600036.SH'].values
High = change_index(dv.get_ts('high_adj').loc[20170105:])['600036.SH'].values
#ta.OBV,ta.AD分别计算OBV和AD指标
OBV= pd.Series(ta.OBV(Close, Volume), index=close.index)
AD = pd.Series(ta.AD(High, Low, Close, Volume), index=close.index)
#A=ta.OBV(Close, Volume) 
#B=pd.Series(ta.OBV(Close, Volume), index=close.index)
fig, (ax, ax1,ax2) = plt.subplots(3, 1, sharex=True, figsize=(15,9))
ax.plot(close['600036.SH'], label='600036')
ax.legend(loc='upper left') #loc='upper left'是名称的位置,而名字默认是上面的'600036.SH'
ax1.plot(OBV,'g', label='OBV')
ax1.legend(loc='upper left')
ax2.plot(AD, 'y', label='A/D')
ax2.legend(loc='upper left')
plt.show()

#step3:VWAP的计算与画图,由于talib中无直接调用函数,就需要先定义算法
#WVAP:sum(close*volume,20)/sum(volume,20),得到的是一个按照成交量进行加权的收盘价
def ts_sum(ts, window=20):
    return ts.rolling(window).sum()
A=pd.Series(Volume,index=volume.index)
B=ts_sum(pd.Series(Volume,index=volume.index))
Vwap=ts_sum(pd.Series(Volume,index=volume.index)*close['600036.SH'])/ts_sum(pd.Series(Volume,index=volume.index))
plt.figure(figsize=(15,7))
plt.plot(close['600036.SH'])
plt.plot(Vwap)
plt.show()



#3.成交量指标策略
import rqalpha
from rqalpha.api import *
import talib
'''
买入： close>VWAP
卖出： close<VWAP
'''
def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 60


def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.PERIOD+1, '1d', 'close')
    volume = history_bars(context.s1, context.PERIOD+1, '1d', 'volume')
    denominator = price*volume
#！！！talib.SUM是加总函数,这个还从未遇到过；同时注意这里没有用滚动函数,因为该引擎本身就是个循环滚动的
    VWAP = talib.SUM(denominator,context.PERIOD)/talib.SUM(volume,context.PERIOD)

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if price[-1] < VWAP[-1] and cur_position > 0:
        order_target_value(context.s1, 0)

    if price[-1] > VWAP[-1]:
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-01",
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





















