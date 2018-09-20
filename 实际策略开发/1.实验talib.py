from jaqs.data import DataView
from jaqs.data import RemoteDataService
import os
import numpy as np
import warnings

warnings.filterwarnings("ignore")
dv = DataView()
dataview_folder = 'G:/data/hs300_2'
dv.load_dataview(dataview_folder)

#For Example
import talib as ta
from datetime import datetime
import talib.abstract as abstract

data = dv.get_ts('close_adj') #data2 = dv.get_ts('close')
print (data.tail())
print (data['600036.SH'].values)  #X1=data['600036.SH']
print (type(data['600036.SH'].values)) #X2=data['600036.SH'].values

#读取'numpy.ndarray'
A=ta.MA(data['600036.SH'].values, 2)
#直接读取DataFrame,默认读取cloumns名为close的数据。
B=ta.abstract.MA(data, 2, price='600036.SH').tail()

'''
data['SMA'] = ta.abstract.MA(data, 20, price='600036.SH') #普通均线与ta.abstract.MA一样
#data['SMA2'] = ta.abstract.SMA(data, 20, price='600036.SH') #与上面完全一样,普通均线
data['WMA'] = ta.abstract.WMA(data, 20, price='600036.SH') #权重均线(突出中间,用于周期分析)
data['TRIMA'] = ta.abstract.TRIMA(data, 20, price='600036.SH') #指数移动平均线
data['EMA']  = ta.abstract.EMA(data, 20, price='600036.SH')  #指数移动平均线
data['DEMA'] = ta.abstract.DEMA(data, 20, price='600036.SH')  #突出EMA(减小了EMA的滞后)
data['KAMA'] = ta.abstract.KAMA(data, 20, price='600036.SH')  #KAMA表示自适应均线
data_B= ta.abstract.BBANDS(data, timeperiod=20, price='600036.SH')  #ta.abstract.BBANDS计算布林带通道

upperband = ta.abstract.MAX(stock, 20, price='high') #求20日最高价(针对high列)
lowerband = ta.abstract.MIN(stock, 20, price='low')  #求20日最低价(针对low列)

A=ta.ROCR100(value.values,20) #表示计算动量
macd = ta.abstract.MACD(data, price='600036.SH') #蓝色线代表macd,红色线代表macdsignal(均线),两者相减就是macdhist表示macd的变化速度
RSI= ta.abstract.RSI(data,20, price='600036.SH')
RSI = talib.RSI(price, 20) #一样,好像都可以
k,d = ta.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0) #KDJ的计算
KDJ = pd.concat([pd.Series(k,index=data.index), pd.Series(d,index=data.index)], axis=1, keys=['slowk','slowd']) #KDJ的计算

adv10 = ta.abstract.MA(volume, 10, price='600036.SH') #观察下这种计算方式！求成交量均线
adv20 = ta.abstract.MA(volume, 20, price='600036.SH')

OBV= pd.Series(ta.OBV(Close, Volume), index=close.index)
AD = pd.Series(ta.AD(High, Low, Close, Volume), index=close.index)
VWAP = talib.SUM(denominator,context.PERIOD)/talib.SUM(volume,context.PERIOD) #talib.SUM是加总函数
MOM_MOM = Momentum(MOM_RS) #Momentum是计算变化率的函数

slope = ta.abstract.LINEARREG_SLOPE(data, 60, price='000001.SZ') #线性回归求K值
intercept = ta.abstract.LINEARREG_INTERCEPT(data, 60, price='000001.SZ') #线性回归求b值
prediction = slope*data['000001.SZ']+intercept #(求k*x+b)
band = 2*ta.abstract.STDDEV(data, 60, price='000001.SZ') #ta.abstract.STDDEV求60日滚动标准差,data为dataframe格式,'000001.SZ'为其中一列








