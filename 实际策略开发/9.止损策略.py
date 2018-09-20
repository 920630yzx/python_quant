# 止损策略
#1.固定价位止损 (固定百分比止损)
import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 30
    context.stoplossmultipler= 0.98 #止损乘数 
    context.takepofitmultipler= 3 #止盈乘数

def handle_bar(context, bar_dict): #handle_bar(context, bar_dict)买入、卖出分开写了,这里需要注意区别！！！
    entry_exit(context, bar_dict)
    stop_loss(context, bar_dict)


def stop_loss(context,bar_dict):
    for stock in context.portfolio.positions:
        if bar_dict[stock].last<context.portfolio.positions[stock].avg_price*context.stoplossmultipler:# 现价低于 原价一定比例
            order_target_percent(stock,0) #全部卖出 context.portfolio.positions[stock].avg_price表示成交均价?
        elif bar_dict[stock].last>context.portfolio.positions[stock].avg_price*context.takepofitmultipler:# 现价高于原价一定比例
            order_target_percent(stock,0) #全部卖出

def entry_exit(context, bar_dict):
    prices = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close')
    short_avg = talib.SMA(prices, context.SHORTPERIOD) #求10日均线！这里使用均线策略进行买卖！
    long_avg = talib.SMA(prices, context.LONGPERIOD) #求30日均线！

    cur_position = context.portfolio.positions[context.s1].quantity # 计算现在portfolio中股票的仓位

    if short_avg[-1] - long_avg[-1] < 0 and short_avg[-2] - long_avg[-2] > 0 and cur_position > 0:
        order_target_value(context.s1, 0) #卖出

    if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0:
        order_target_percent(context.s1, 1) #买入

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock': 1000000},
    "benchmark": "000300.XSHG"  #000001.XSHG (上证指数) 或000300.XSHG(沪深300)
#   "strategy_file_path": os.path.abspath(__file__)
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



#2.追踪止损  (若股票一直上涨,止损价位也随着上涨)
'''用字典存储股票最高价
stoploss_max = 允许最大回撤
if 现价<持股股票最高价*(1-stoploss_max):
卖出止损
else：
继续持有'''

import rqalpha
from rqalpha.api import *
import talib

def init(context):
    context.s1 = "000001.XSHE"
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 30
    context.stoploss_max= 0.4
    context.max = {}

def handle_bar(context, bar_dict):
    entry_exit(context, bar_dict)
    stop_loss(context, bar_dict)


def update_high(context, stock): #这里记录最高价
    high = history_bars(stock, 1, '1d', 'high')[0] #[0]是什么意思？
    try:
        Max = context.max[stock]
    except KeyError: #如果是KeyError的问题
        Max = high
        context.max[stock] = high

    if high > Max:
        context.max[stock] = high
        return high
    else:
        return Max

def stop_loss(context,bar_dict): #卖出
    for stock in context.portfolio.positions.keys():
        high = update_high(context, stock)
        close = history_bars(stock, 1, '1d', 'close')[0] #[0]表示什么,这里理论上用[-1]会更好
        if close < high*(1-context.stoploss_max):
            order_target_percent(stock,0)
            context.max.pop(stock) #删除最高价？

def entry_exit(context, bar_dict):
    prices = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close')
    short_avg = talib.SMA(prices, context.SHORTPERIOD)
    long_avg = talib.SMA(prices, context.LONGPERIOD)

    cur_position = context.portfolio.positions[context.s1].quantity #计算现在portfolio中股票的仓位

    if short_avg[-1] - long_avg[-1] < 0 and short_avg[-2] - long_avg[-2] > 0 and cur_position > 0:
        order_target_value(context.s1, 0) #卖出

    if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0:
        order_target_percent(context.s1, 1) #买入

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock':1000000},
    "benchmark": "000300.XSHG"
#     "strategy_file_path": os.path.abspath(__file__)
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



#3.时间止损 if 持股时间 >holdperiod and 周期内涨幅少于 total_return,则卖出该股票
import rqalpha
from rqalpha.api import *
import talib as ta

def init(context):
    context.to_buy = "000001.XSHE"
    context.SHORTPERIOD = 10
    context.LONGPERIOD = 30
    context.time = []
    context.holdperiod = 60
    context.total_return=0.1

def stop_loss( context,bar_dict):
    for stock in context.portfolio.positions:
        buytime=context.time # 获取买入时间
        currenttime=context.now.replace(tzinfo=None) # 获取当前时间
#         print ('buytime='+str(buytime))
#         print('currenttime='+str(currenttime))
        total_return=context.portfolio.positions[stock].market_value/(context.portfolio.positions[stock].avg_price*context.portfolio.positions[stock].quantity) # 计算回报
        hold_time=(currenttime-buytime).days # 计算持有天数
        if hold_time>context.holdperiod and total_return<1+context.total_return:
            order_target_percent(stock, 0) #如果回报大于60且收益小于0.1,则平仓
        elif total_return>1+2*context.total_return:
            order_target_percent(stock, 0) #收益达到一定条件也平仓
#         else: 
#             print(str(stock)+ '持仓未到' +str(context.holdperiod)+'天,继续持有')

def handle_bar(context, bar_dict):
    entry_exit(context, bar_dict)
    stop_loss(context, bar_dict)

def entry_exit(context, bar_dict):
    prices = history_bars(context.to_buy, context.LONGPERIOD+1, '1d', 'close')
    short_avg = ta.SMA(prices, context.SHORTPERIOD)
    long_avg = ta.SMA(prices, context.LONGPERIOD)

    cur_position = context.portfolio.positions[context.to_buy].quantity
    shares = context.portfolio.cash/bar_dict[context.to_buy].close
    if short_avg[-1] - long_avg[-1] < 0 and short_avg[-2] - long_avg[-2] > 0 and cur_position > 0:
        order_target_value(context.to_buy, 0)

    if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0:
        order_shares(context.to_buy, shares)
        #记录买入时间
        buy_time = context.now.replace(tzinfo=None)
        context.time = buy_time

config = {
  "base": {
    "start_date": "2015-06-01",
    "end_date": "2017-12-30",
    "accounts": {'stock': 100000},
    "benchmark": "000001.XSHE"
#     "strategy_file_path": os.path.abspath(__file__)
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























