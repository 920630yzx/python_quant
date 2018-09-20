#动能指标
"""
动能指标对价格的计算与物理学中对速度的计算相似,需要知道价格移动的距离、时间、移动的速度与加速度,
这些变化都反映着市场价格在不同维度上的变化.动能指标的类型主要有两种,一种是Momentum 指标,它有中间轴,
可以是0或100,上下没有界限；另一种是Oscillator 振荡器，它的取值在0至100之间。
"""

'''动能指标:
1. Momentum: ROCR100=(Price/prevPrice)*100
2. MACD: MACD=26'day'EMA-12'day'EMA
         MACD'=9'day'EMA(MACD)
         Hist=MACD-MACD'
3. RSI:  RSI=100-100/(1+RS) RS表示n日内平均上涨变化/n日内平均下跌变化
4. Stochastic(随机指标KDJ): FAST'K=(价格-最低价)/(最高价-最低价)
               SLOW'K=MA(Fast'K,3)
               SLOW'D=MA(SLOW'K,3)
'''

#加载
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

#1.计算并作图
#step1 Momentum: ROCR100的计算并作图
def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df
data = change_index(dv.get_ts('close_adj').loc[20170105:])

#！！！注意下这个表达,通过字典生成式读取数据   最后一行是典型的字典读取数据并转换为dataframe格式
symbol= ['000001.SZ','600036.SH','600050.SH','000008.SZ','000009.SZ']
price_dict = {name: data[name] for name in symbol} #name成为字典的key,data[name]成为key对应的元素
data_mom = pd.DataFrame({item: ta.ROCR100(value.values,20) for item,value in price_dict.items()},index=data.index).dropna(axis=0)
#dropna()表示删除为空的行,ta.ROCR100(value.values,20)表示计算动量,原式可为：A=ta.ROCR100(price_dict['000001.SZ'],20) (ta.ROCR100在talib中比较特殊)

fig = plt.figure(figsize=(15, 7)) #图片大小
plt.plot(data_mom)
plt.hlines(100,data_mom.index[0],data_mom.index[-1] , linestyles='dashed', alpha=0.5) 
# ！！！ plt.hlines表示画一条虚线,100为虚线的位置(高度),data_mom.index[0],data_mom.index[-1]表示宽度,linestyles='dashed'表示虚线  
plt.legend(data_mom.columns, loc='upper left') #data_mom.columns为列名,plt.legend表示给线条依次命名
plt.show()

#step2 MACD的计算并作图:
#MACD的计算
macd = ta.abstract.MACD(data, price='600036.SH') #蓝色线代表macd,红色线代表macdsignal(均线),两者相减就是macdhist表示macd的变化速度
# macd ！！！画图
fig, (ax, ax1) = plt.subplots(2, 1, sharex=True, figsize=(15,7)) #plt.subplots(2, 1)表示画两张图,sharex=True表示共用一条x轴
ax.plot(macd.index, data['600036.SH']) # 给第一张图ax画图
ax1.plot(macd.index, macd['macd']) # 给第二张图ax1画图
ax1.plot(macd.index, macd['macdsignal']) # 给第二张图ax1画图
ax1.bar(macd.index, macd['macdhist']) # 给第二张图ax1的坐标轴画图
plt.show()

#step3 RSI的计算并作图
#计算RSI
RSI= ta.abstract.RSI(data,20, price='600036.SH')

fig, (ax, ax1) = plt.subplots(2, 1, sharex=True, figsize=(15,7))
ax.plot(data['600036.SH'])
ax1.plot(RSI,'r', label='RSI') #label='RSI'通过这种方式直接给曲线命名！
ax1.axhline(70,alpha=0.3)
ax1.axhline(30,alpha=0.3)
plt.legend()
plt.show()

#step4  Stochastic(随机指标)的计算并作图
high = change_index(dv.get_ts('high_adj').loc[20170105:])['600036.SH'].values #注意.values的作用
low = change_index(dv.get_ts('low_adj').loc[20170105:])['600036.SH'].values
close = change_index(dv.get_ts('close_adj').loc[20170105:])['600036.SH'].values

#Stochastic  由ta.STOCH计算Stochastic
k,d = ta.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
KDJ = pd.concat([pd.Series(k,index=data.index), pd.Series(d,index=data.index)], axis=1, keys=['slowk','slowd'])

fig, (ax, ax1) = plt.subplots(2, 1, sharex=True, figsize=(15,7))
ax.plot(data['600036.SH'])
ax1.plot(KDJ['slowk'], label='slowK')
ax1.plot(KDJ['slowd'],'y', label='slowd')
ax1.axhline(70,alpha=0.3) #ax1.axhline表示做一条线
ax1.axhline(30,alpha=0.3)
plt.legend(loc='upper left')
plt.show()



#2.动能指标做策略
'''
1. 图表的领先形态（Charting Patterns-Leading ahead）: 
可以通过观察指标对价格做领先的形态或走势判断。
2. 交叉信号（Cross Signals）： 
快线高于慢线金叉，看涨；快线低于慢线死叉，看跌。
3. 柱的斜率（The slope of MACD-Histogram）： 
当前的柱比前一根高，看涨；当前的柱比前一根低，看跌。
4. 超买超卖（Overbought/OverSold）： 
当振荡器高于上方的值如RSI(70)为超买，低于下方的值如RSI(30)为超卖，超卖买入，超买卖出。
5. 背离（Divergence）： 
价格创新高，而指标没有创新高，顶背离，看跌。 
价格创新低，而指标没有创新低，底背离，看涨。
'''

#以RSI判断超买超卖为例:
#底背离买入： RSI<30
#顶背离卖出： RSI>70

# Bollinger Band
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.PERIOD = 20

def handle_bar(context, bar_dict):
    price = history_bars(context.s1, context.PERIOD*2+1, '1d', 'close')
    RSI = talib.RSI(price, 20)

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if RSI[-1]>70:
        order_target_value(context.s1, 0)

    if RSI[-1]<30:
        order_shares(context.s1, shares)
        
'''可以试试这个有没有区别,这块应该比上面更好,为什么。
def handle_bar(context, bar_dict):
    price = history_bars(context.s1, context.PERIOD*2+1, '1d', 'close')
    RSI = talib.RSI(price, 20)

    cur_position = context.portfolio.positions[context.s1].quantity
    shares = context.portfolio.cash/bar_dict[context.s1].close

    if RSI[-1]>70 and cur_position > 0:
        order_target_value(context.s1, 0)

    if RSI[-1]<30 and cur_position == 0:
        order_shares(context.s1, shares)
'''

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-06-30",
    "accounts": {'stock':1000000},
    "benchmark": "000001.XSHE"
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "report_save_path": 'G:\data5',
      "plot": True
    }
  }
}

rqalpha.run_func(init=init, handle_bar=handle_bar, config=config)

















