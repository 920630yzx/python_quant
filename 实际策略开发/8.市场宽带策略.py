#市场宽度:对市场内股票数据进行统计,观察样本变化。
'''
市场宽度指标指某一日收盘时,显示某指数组合的股票的上涨数量与下跌数量的比率,有比较准确预测大盘行情的功能。
怎么计算市场宽度:1.(advance-decline)/total (上涨的股票数量-下跌的股票数量)/股票总数
2.(high-low)/total (创出新高的股票数量-创出新低的股票数量)/股票总数 (这里股票总数可能不等于两者之和)
3.(MA50up-MA50down)/total (价格大于50日均线的股票数量-价格小于50日均线的股票数量)/股票总数
'''

#首先还是加载
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

dataview_folder = 'G:/data/hs300_611'
dv = DataView()
dv.load_dataview(dataview_folder)

#定义函数
def change_index(df):
    df.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df

def formula(positive, negative, total): #市场宽度的计算
    return (positive-negative)/total

def sumrows(frame):
    return frame.sum(axis=1) #每一行加总

#2.相关计算  下面有panel的直接构建方法,值得反复学习！！！
mask = dv.get_ts('index_member') #打印哪些在指数中
A=dv.get_ts('close_adj').loc[20150105:][mask==1] #观察变化
B=dv.get_ts('close_adj').loc[20150105:][mask==1].dropna(how='all',axis=1)  #观察变化,这里注意下若'high_adj'=0则表示停牌
PN = pd.Panel({'high' : change_index(dv.get_ts('high_adj').loc[20150105:][mask==1].dropna(how='all',axis=1)),
 'low' : change_index(dv.get_ts('low_adj').loc[20150105:][mask==1].dropna(how='all',axis=1)),
 'close' : change_index(dv.get_ts('close_adj').loc[20150105:][mask==1].dropna(how='all',axis=1)),
 'volume' : change_index(dv.get_ts('volume').loc[20150105:])[mask==1].dropna(how='all',axis=1)})
print(PN) 
PN = PN.transpose(2,1,0) #转换一下PN的格式

#step1:市场宽度计算公式 1.(advance-decline)/total (上涨的股票数量-下跌的股票数量)/股票总数
cpc = PN.minor_xs('close') #得到收盘价，'close'即'close_adj'需注意这里名称已换
cpc = PN.minor_xs('close').pct_change() #cpc=close price相对于前一天的涨跌幅

participation = formula(  
    sumrows(cpc>0),
    sumrows(cpc<0),
    300) #sumrows函数用于统计每行满足条件的个数！

print(participation.tail())

#step2:计算新高新低的量 2.(high-low)/total (创出新高的股票数量-创出新低的股票数量)/股票总数 (这里股票总数可能不等于两者之和)
d1 = PN.minor_xs('high').rolling(5).max().pct_change() #每5天取一个新高,求新高变化率
d2 = PN.minor_xs('low').rolling(5).min().pct_change()

leadership = formula(
    sumrows(d1>0),
    sumrows(d2<0),
    300
)
print(leadership.tail())

#step3:计算均线上下的量 3.(MA50up-MA50down)/total (价格大于50日均线的股票数量-价格小于50日均线的股票数量)/股票总数
#MA50
import talib as ta
close = PN.minor_xs('close')

def cal_ma(s, timeperiod=3): #计算50日均线!!!函数较难理解？
    s = s.dropna() #这句话不写好像完全一样？
    try: #正常操作
        return pd.Series(ta.MA(s.values, timeperiod), s.index) 
    except: #若上面发生异常,执行下面
        return pd.Series()

ma2 = close.apply(cal_ma)
'''
apply(func [, args [, kwargs ]]) 函数用于当函数参数已经存在于一个元组或字典中时,间接地调用函数.
args是一个包含将要提供给函数的按位置传递的参数的元组.如果省略了args,任何参数都不会被传递，kwargs是一个包含关键字参数的字典。
apply()的返回值就是func()的返回值,apply()的元素参数是有序的,元素的顺序必须和func()形式参数的顺序一致
'''
trend = formula(
    sumrows(close>ma2),
    sumrows(close<ma2),
    300
)
print(trend.tail())

#3.平滑数据（smooth）  (定义函数)
def smooth(series, fast=20, slow=50):
    f = ta.MA(series.values, fast)
    s = ta.MA(series.values, slow)
    return pd.DataFrame({"fast": f, "slow": s}, series.index)

def plot_smooth(ax, smoothed, origin):
    ax.set_title(origin.name)
    ax.bar(origin.index, origin.values)
    ax.plot(smoothed.slow, c='r', label = 'slow')
    ax.plot(smoothed.fast, c='g', label = 'fast')
    ax.legend()
    return ax

#step2:图形展示市场宽度
import numpy as np
hs300 = change_index(dv.data_benchmark)
hs300["trend"] = trend
hs300["participation"] = participation
hs300["leadership"] = leadership

import matplotlib.pyplot as plt

f, axs = plt.subplots(4, 1, sharex=True, figsize=(15, 15))

axs[0].set_title("hs300") #画出第一张图
axs[0].plot(hs300['close'].loc['2017-02-04':]) #第一章图画收盘价

to_smooth = ["trend", "participation", "leadership"]

for ax, (name, item) in zip(axs[1:], hs300[to_smooth].iteritems()): #循环画图！！！
    plot_smooth(ax, smooth(item), item)

plt.show()

#C=dv.data_benchmark












