#选股回测表格
#1.加载
from jaqs.data.dataapi import DataApi
from jaqs.data import DataView
from jaqs.research import SignalDigger
import numpy as np
from datetime import datetime
import pandas as pd
from datetime import timedelta
import warnings

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)
print(dv.fields) #查看dv中取得的数据

#1.数据预处理
def change_columns_index(signal):
    new_names = {}
    for c in signal.columns: #signal的每一列
        if c.endswith('SZ'):
            new_names[c] = c.replace('SZ', 'XSHE') #将'SZ'转换为'XSHE'以满足需要的格式
        elif c.endswith('SH'):
            new_names[c] = c.replace('SH', 'XSHG') #将'SH'转换为'XSHE'
    signal = signal.rename_axis(new_names, axis=1)
    signal.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , signal.index))
    signal.index = pd.Index(map(lambda x: x+timedelta(hours=15), signal.index))
    return signal

mask = dv.get_ts('mask_fundamental') #是否需要过滤该支股票：这里false表示不用过滤该股票,true表示需要过滤掉该股票???
group = change_columns_index(dv.get_ts('group'))
ROE_Data = dv.get_ts('roe')
ROE_Data = change_columns_index(dv.get_ts('roe').shift(1, axis=0)[mask==0]) #shift(1, axis=0)会自动提前1天,避免未来函数
prices = change_columns_index(dv.get_ts('close_adj'))

def get_largest(df, n=20): #这个方法把ROE最大的20只股票赋值为1,每天都取ROE最大的20支股票 !!???
    largest_list = []
    for time_index, value in df.iterrows():
        largest_list.append(dict.fromkeys(value.nlargest(n).index,1))
    largest_df = pd.DataFrame(largest_list, index = df.index)
    return largest_df

stock_df = get_largest(ROE_Data).dropna(how='all', axis=1)

stock_df.to_excel('roe_backtest.xlsx') #保存至当前目录下



#2.等权重下单
import numpy as np
import talib as ta
import pandas as pd
import rqalpha
from rqalpha.api import *

#读取文件位置
def init(context): 
    context.codes = stock_df
    context.stocks = []
    context.SHORTPERIOD = 20
    #scheduler.run_weekly(find_pool, tradingday=1)
    scheduler.run_daily(find_pool)

def find_pool(context, bar_dict): #读取每天需要选中的股票
    try:
        codes = context.codes.loc[context.now]
    except KeyError:
        return
    stocks = codes.index[codes == 1]
    context.stocks = stocks

def handle_bar(context, bar_dict):
    buy(context, bar_dict)


def buy(context, bar_dict): #多支股票回测,也即选股+等权重+择时的策略
    pool = context.stocks
#     print (pool)
    if pool is not None:
        stocks_len = len(pool) #1/长度(stocks_len)得到结果,分别表示每支股票的投入比例
        for stocks in context.portfolio.positions:
            if stocks not in pool:
                order_target_percent(stocks, 0)
        for codes in pool:
            try: #均线策略(但是与前面的均线策略不同)
                price = history_bars(codes, context.SHORTPERIOD+10, '1d', 'close')
                short_avg = ta.SMA(price, context.SHORTPERIOD) #20日均线
                cur_position = context.portfolio.positions[codes].quantity
                if short_avg[-1] < short_avg[-3] and cur_position > 0:
                    order_target_value(codes, 0)
                if short_avg[-1] > short_avg[-3]:
                    order_target_percent(codes, 1.0/stocks_len)
            except Exception:
                pass


config = {
  "base": {
    "start_date": "2015-09-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000300.XSHG"
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



#3.按照特定权重下单 (这里是按照roe比例进行下单) ？？？
def get_largest_weight(df, n=20):
    largest_list = []
    for time_index, value in df.iterrows():
        largest_list.append(value.nlargest(n).to_dict())
    largest_df = pd.DataFrame(largest_list, index = df.index)
    return largest_df

largest_weight = get_largest_weight(ROE_Data)

weight_list = []
for time_index, weight in largest_weight.iterrows():
    weight[weight<0]=0
    weiht_result = (weight/weight.sum())
    weight_list.append(weiht_result.to_dict())
weight_df = pd.DataFrame(weight_list, index=largest_weight.index)

import numpy as np
import talib as ta
import pandas as pd
import rqalpha
from rqalpha.api import *

#读取文件位置
def init(context):
    context.codes = weight_df
    context.hs300 = '000300.XSHG'
    context.SHORTPERIOD = 20
    context.stocks = {}
    scheduler.run_daily(find_pool)
#     scheduler.run_weekly(find_pool,tradingday=3)

def find_pool(context, bar_dict):
    codes = context.codes.loc[context.now].dropna()
    if codes is not None:
        context.stocks = codes
    else:
        context.stocks = {}

def handle_bar(context, bar_dict):
    buy(context, bar_dict)

def buy(context, bar_dict):
    pool = context.stocks
    if pool is not None:
        for stocks in context.portfolio.positions:
            if stocks not in pool:
                order_target_percent(stocks, 0)
        for codes, target in pool.items(): #按权重值进行遍历
            try:
                price = history_bars(codes, context.SHORTPERIOD+10, '1d', 'close')
                short_avg = ta.SMA(price, context.SHORTPERIOD)
                cur_position = context.portfolio.positions[codes].quantity
                if short_avg[-1] < short_avg[-3] and cur_position > 0:
                    order_target_value(codes, 0)
                if short_avg[-1]  > short_avg[-3]:
                    order_target_percent(codes, target) #target是按照权重进行下单
            except Exception:
                pass

config = {
  "base": {
    "start_date": "2015-09-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000300.XSHG"
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



#4.策略优化***？？？
import logging
from rqalpha_mod_optimization.optimizer import SimpleOptimizeApplication
from rqalpha_mod_optimization.parallel import set_parallel_method, ParallelMethod

params = {
    'SHORTPERIOD': range(5,40,5),
}

config = {
    "extra": {
        "log_level": "verbose",
    },
    "base": {
        "start_date": "2015-09-01",
        "end_date": "2017-12-30",
        "accounts": {'stock':1000000},
        "matching_type": "next_bar",
        "benchmark": "000300.XSHG",
        "frequency": "1d",
    }
}

if __name__ == "__main__":
    try:
        set_parallel_method(ParallelMethod.DASK)
        result = SimpleOptimizeApplication(config).open("ROE_MA_Strategy.py").optimize(params)
        print(result.sort_values(by=["sharpe"], ascending=False))
    except Exception as e:
        logging.exception(e)
        print("******POOL TERMINATE*******")










