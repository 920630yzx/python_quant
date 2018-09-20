#线性回归策略
'''什么是线性回归：在统计学中,线性回归(Linear Regression)是利用称为线性回归方程的
最小平方函数对一个或多个自变量和因变量之间关系进行建模的一种回归分析.例如y=k*x+b(这里k也是slope,而b也是intercept,下用)
Confidence Band如何计算:一般是Y加减两个标准差的值
相关策略(Buy):价格大于预测值;价格大于上方边界;Slope>0(即斜率k>0);残差变化率的均线上涨
'''

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
import talib.abstract as abstract

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df

#相关计算  注意ta.abstract.LINEARREG_SLOPE表示求斜率？？？ta.abstract.LINEARREG_INTERCEPT表示求b值??? (线性回归计算)
data = change_index(dv.get_ts('close_adj').loc[20170105:])
#data=data/100
slope = ta.abstract.LINEARREG_SLOPE(data, 60, price='000001.SZ')
intercept = ta.abstract.LINEARREG_INTERCEPT(data, 60, price='000001.SZ')
prediction = slope*data['000001.SZ']+intercept #(求k*x+b)
band = 2*ta.abstract.STDDEV(data, 60, price='000001.SZ') #ta.abstract.STDDEV求60日滚动标准差,data为dataframe格式,'000001.SZ'为其中一列

#作图
plt.figure(figsize=(15,9))
plt.subplot(2,1,1)
plt.plot(data['000001.SZ'])
plt.plot(prediction) #画出线性回归预测值
plt.plot(prediction+band) #画出上边界
plt.plot(prediction-band) #画出下边界
plt.subplot(2,1,2) #画第二张图
plt.hlines(y=0,xmax=slope.index[-1],xmin=slope.index[0])
plt.plot(slope)
plt.show()

#2.残差的计算: 残差=(真实的价格-预测的价格)/真实的价格
residual = (data['000001.SZ']-prediction)/data['000001.SZ'] #残差=(真实的价格-预测的价格)/真实的价格
Ma_r = pd.Series(ta.MA(residual.values, 30),index=residual.index) #求残差的30日均线; .values可以将其转化为float型格式

f,(a1,a2)=plt.subplots(2,1,sharex=True,figsize=(15,9))
a1.plot(data['000001.SZ'])
a2.plot(residual,color='b') #这里表示画出残差
a2.plot(Ma_r,color='r') #这里表示画出残差的均值(这里与答案不同？)
plt.show()



#3.策略回测1
#价格大于预测值则买入,反之价格小于预测值则卖出
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 10

def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.PERIOD+1, '1d', 'close')

    slope = talib.LINEARREG_SLOPE(price, context.PERIOD)
    intercept = talib.LINEARREG_INTERCEPT(price, context.PERIOD)
    prediction = slope*price+intercept

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if price[-1] < prediction[-1] and cur_position > 0: #时间不对为何还能运行？这是因为引擎重新计算了各个值
        order_target_value(context.s1, 0)

    if price[-1] > prediction[-1] :
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
      "report_save_path": 'G:\data3',
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)



#策略回测2
#残差>残差均线则买入,反之残差<残差均线则卖出

import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 10

def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.PERIOD*3, '1d', 'close') #注意时间context.PERIOD*3略有不同

    slope = talib.LINEARREG_SLOPE(price, context.PERIOD) #计算斜率
    intercept = talib.LINEARREG_INTERCEPT(price, context.PERIOD) #计算b值
    prediction = slope*price+intercept #计算预测值
    residual = (price-prediction)/price #计算残差
    residual_MA = ta.MA(residual, 20) #计算20日残差均值

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if residual[-1] < residual_MA[-1] and cur_position > 0:
        order_target_value(context.s1, 0)

    if residual[-1] > residual_MA[-1]:
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

