#相对强弱市场
"""
什么是相对强弱:一段时间内某股票和本行业的股票或整个市场的比较,即对该股票市场表现的计量.
怎么计算相对强弱:RS = Stock/Index,MOM_RS = Momentum(RS),MOM_MOM = Momentum(MOM_RS)
Momentum是计算变化率的函数
"""



#1.用图形展示相对强弱
#先加载：
from jaqs.data import DataView
from jaqs.data import RemoteDataService
import os
import numpy as np
import talib as ta
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df

#计算并画图
stock = change_index(dv.get_ts('close_adj').loc[20170105:])
hs300 = change_index(dv.data_benchmark.loc[20170105:]) #dv.data_benchmark默认是沪深300指数？
Rs = stock['600036.SH']/hs300.close #计算RS
Rs = RS.dropna() #删除空行
print (RS.tail())

#Momentum_RS的计算
import talib as ta
MOM_Rs = ta.ROCR100(Rs.values, 20) #ta.ROCR100(Mom_Rs,20)表示计算20日动量(增长率)!!!
MOM_Mom = ta.ROCR100(MOM_Rs, 20) #求增长率的增长率,相当于加速度!!!
data_s = stock['600036.SH']
data1 = pd.Series(MOM_Rs, index=Rs.index) #修改索引
data2 = pd.Series(MOM_Mom, index=Rs.index)
data = pd.concat([data_s, Rs, data1, data2], axis=1)
data.columns = ['close', 'RS', 'MOM_RS', 'MOM_MOM'] #得到最终的结果:分别表示收盘价,占有率,增长率,加速度
print (data.tail())

#画图
import matplotlib.pyplot as plt
plt.figure(figsize=(15,7))
plt.plot(data.MOM_RS.tail(20).values,data.MOM_MOM.tail(20).values) #data.MOM_RS.tail(20).value表示速度,data.MOM_MOM.tail(20).values代表加速度
plt.axhline(100,alpha=0.3) #plt.axhline表示画线
plt.axvline(100,alpha=0.3)
X=data['MOM_RS'].iloc[-1]
Y=data['MOM_MOM'].iloc[-1]
plt.scatter(X,Y,color='r', s=100) #plt.scatter表示画点
plt.show()
#第一象限表示加速度与速度均为正;第二象限表示速度为负,但加速度为正



#2.相对强弱策略
'''
买入时机：第一象限：（MOM_RS>100, MOM_MOM>100）,第四象限：（MOM_RS< 100, MOM_MOM >100）
卖出时机:第二象限：（MOM_RS > 100, MOM_MOM < 100）,第三象限：（MOM_RS< 100, MOM_MOM < 100）
'''

#Relative_Strength
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.index = "000300.XSHG"
    context.PERIOD = 50
    
def handle_bar(context, bar_dict):
    price = history_bars(context.s1, context.PERIOD*3, '1d', 'close')
    index = history_bars(context.index, context.PERIOD*3, '1d', 'close')

    if len(price)==len(index):
        RS = price/index
        MOM = talib.ROCR100(RS, context.PERIOD)
        if len(MOM)>context.PERIOD:
            MOM_MOM = talib.ROCR100(MOM, context.PERIOD)
            cur_position = context.portfolio.positions[context.s1].quantity
            shares = context.portfolio.cash/bar_dict[context.s1].close

            if (MOM_MOM[-1]<100) and (MOM_MOM[-2]>100):
                order_target_value(context.s1, 0)

            if (MOM_MOM[-1]>100) and (MOM_MOM[-2]<100) and (cur_position==0):
                order_shares(context.s1, shares)

'''对比看看区别            
def handle_bar(context, bar_dict):
    price = history_bars(context.s1, context.PERIOD*3, '1d', 'close')
    index = history_bars(context.index, context.PERIOD*3, '1d', 'close')

    if len(price)==len(index):
        RS = price/index
        MOM = talib.ROCR100(RS, context.PERIOD)
        if len(MOM)>context.PERIOD:
            MOM_MOM = talib.ROCR100(MOM, context.PERIOD)
            cur_position = context.portfolio.positions[context.s1].quantity
            shares = context.portfolio.cash/bar_dict[context.s1].close

            if (MOM_MOM[-1]<100) and (cur_position>0):
                order_target_value(context.s1, 0)

            if (MOM_MOM[-1]>100) and (cur_position==0):
                order_shares(context.s1, shares)
'''

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
      "report_save_path": 'G:\data3',
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)



















