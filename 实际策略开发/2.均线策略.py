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
dv = DataView()
dataview_folder = 'G:/data/hs300_2'
dv.load_dataview(dataview_folder)

def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df

#读取收盘价
data = change_index(dv.get_ts('close').loc[20170105:])

data['SMA'] = ta.abstract.MA(data, 20, price='600036.SH')
#data['SMA2'] = ta.abstract.SMA(data, 20, price='600036.SH') #与上面完全一样
data['WMA'] = ta.abstract.WMA(data, 20, price='600036.SH')
data['TRIMA'] = ta.abstract.TRIMA(data, 20, price='600036.SH')
data['EMA']  = ta.abstract.EMA(data, 20, price='600036.SH')
data['DEMA'] = ta.abstract.DEMA(data, 20, price='600036.SH')
data['KAMA'] = ta.abstract.KAMA(data, 20, price='600036.SH') 


fig = plt.figure(figsize=(15, 7))
plt.plot(data['600036.SH'])
plt.plot(data['SMA'], alpha=0.5) #普通均线
plt.plot(data['WMA'], alpha=0.5) #权重均线(突出前段)
plt.plot(data['TRIMA'], alpha=0.5) #权重均线(突出中间,用于周期分析)
plt.plot(data['EMA'], alpha=0.5) #指数移动平均线
plt.plot(data['DEMA'], alpha=0.5) #突出EMA(减小了EMA的滞后)
plt.plot(data['KAMA'], alpha=0.5) #KAMA表示自适应均线
plt.legend(loc='lower right')
plt.show()


#两条均线的三种交易方法
#1.当均线金叉（短期大于长期均线）时候买进，死叉（短期小于长期）时卖出。 
#2.当价格上穿两条均线时买入，但价格下穿其中一条均线时卖出。 
#3.当两条均线都处于向上方向时买入，当两条均线都处于下跌方向时卖出。

#MA_Strategy_1 当均线金叉（短期大于长期均线）时候买进,死叉（短期小于长期）时卖出。  
# (由于时间上有些许差异,所以结果也有些小差异,修改时间可能会得到一样的结果)
import rqalpha
from rqalpha.api import *
import talib

def init(context): #只会运行一次,并且先于所有的程序运行;context本身是一个字典,可以理解为一个全局变量
    context.s1 = "000001.XSHE"
    #context.s2="000002.XSHE" 
    #context.s3 = "000300.XSHG" 添加新的股票
    #update_universe(context.s1) 不断跟新context.s1
    #logger.info("RunInfo: {}".format(context.run_info)) 实时打印日志
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 20
    #context.commission=0.08 #手动设置交易佣金为万8(百分之0.08)；而印花税都是千一,固没有接口
    #context.slippage=0.05 #设置滑点,若不设置默认百分之0.246

def handle_bar(context, bar_dict): #每次数据更新时,就会运行一次;bar_dict本身也是一个字典,对应K线的每一根蜡烛图

    price = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close') #context.LONGPERIOD+1表示获取的历史数据数量，必填项

    short_avg = talib.SMA(price, context.SHORTPERIOD)
    long_avg = talib.SMA(price, context.LONGPERIOD)

    #plot("short avg", short_avg[-1]) 画图
    #plot("long avg", long_avg[-1])
    #plot("close",bar_dict[context.s1].close) #画出指定股票的收盘价,前面应该是名称

    # 计算现在portfolio中股票的仓位
    cur_position = context.portfolio.positions[context.s1].quantity
    # 计算现在portfolio中的现金可以购买多少股票,context.portfolio.cash表示已有的现金
    shares = context.portfolio.cash/bar_dict[context.s1].close

    # 如果短均线从上往下跌破长均线，也就是在目前的bar短线平均值低于长线平均值，而上一个bar的短线平均值高于长线平均值
    if short_avg[-1] - long_avg[-1] < 0 and short_avg[-2] - long_avg[-2] > 0 and cur_position > 0:
        # 进行清仓
        order_target_value(context.s1, 0)

    # 如果短均线从下往上突破长均线，为入场信号
    if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0 :
        # 满仓入股
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-31",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      #保存report至当下文件：
      #"report_save_path": 'G:\data4', 
      "enabled": True,
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)


'''
def handle_bar(context,bar_dict):
    volume = bar_dict['000001.XSHE'].volume
    #拿到'000001.XSHE'当前bar的成交量,history_bars是拿到k线蜡烛图
    
'''


#MA_Strategy_2   当价格上穿两条均线时买入,价格下穿其中一条均线时卖出. 
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 20


def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close')

    short_avg = talib.SMA(price, context.SHORTPERIOD)
    long_avg = talib.SMA(price, context.LONGPERIOD)

    # 计算现在portfolio中股票的仓位
    cur_position = context.portfolio.positions[context.s1].quantity
    # 计算现在portfolio中的现金可以购买多少股票
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if price[-1] < short_avg[-1] or price[-1] < long_avg[-1] and cur_position > 0:
        order_target_value(context.s1, 0)

    if price[-1] > short_avg[-1] and price[-1] > long_avg[-1] : #???
        order_shares(context.s1, shares)

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-31",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      #"report_save_path": 'G:\data',
      "enabled": True,
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)

#MA_Strategy_3 当两条均线都处于向上方向时买入,当两条均线都处于下跌方向时卖出.
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 30


def handle_bar(context, bar_dict):

    price = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close')

    short_avg = talib.SMA(price, context.SHORTPERIOD)
    long_avg = talib.SMA(price, context.LONGPERIOD)
    
    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close
    
    if len(long_avg)== context.LONGPERIOD+1:
        
        if  short_avg[-1] < short_avg[-2] and long_avg[-1] < long_avg[-2] and cur_position > 0:
            order_target_value(context.s1, 0)

        if short_avg[-1] > short_avg[-2] and long_avg[-1] > long_avg[-2]:
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


'''
history_bars(stock,20,'1d','close')  会得到：（20天前的收盘价，19天前的收盘价.........昨天的收盘价，今天的收盘价）
history_bars(stock,20,'1d','close')[0]:      20天前的收盘价
history_bars(stock,20,'1d','close')[-1]:     今天的收盘价
'''


