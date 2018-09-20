#1_初始化
from jaqs_fxdayu.data import DataView 
import warnings

warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

import pandas as pd
import talib as ta



#2_add_formula 基于dataview里已有的字段,通过表达式定义因子：
#step1:
dv.add_formula("momentum", "Return(close_adj, 20)", is_quarterly=False).head() #直接使用内置的函数,所以不需要你先自定义
#动量因子"Return(close_adj, 20)"表示股票20日收益率(close/close(20日前)-1),"momentum"是新因子的名称,is_quarterly=True是季度因子,is_quarterly=False为日度因子
#添加到数据集dv里，则计算结果之后可以反复调用：
print(dv.fields) #查看dv中取得的数据
dv.add_formula("momentum", "Return(close_adj, 20)", is_quarterly=False, add_data=True) #add_data=True: 调用添加到数据集dv里,则计算结果之后可以反复调用
dv.get_ts("momentum").head()
A=dv.get_ts("close_adj")
B=dv.get_ts("momentum")
# dv.save_dataview('G:/data/hs300_1') #这相当于另存为

#step2:
# 函数一览 一共68个：
dv.func_doc.funcs  
# 函数描述 一共68个(一一对应):
dv.func_doc.descriptions
# 根据函数类型查询该类型下所有的函数:
dv.func_doc.search_by_type("数学函数")
dv.func_doc.search_by_type("逻辑运算")
dv.func_doc.search_by_type("三角函数")
dv.func_doc.search_by_type("取整函数")
dv.func_doc.search_by_type("选择函数")
dv.func_doc.search_by_type("时间序列函数")
dv.func_doc.search_by_type("横截面函数")
dv.func_doc.search_by_type("其他")
dv.func_doc.search_by_type("技术指标")
# 根据函数名查询该函数：
dv.func_doc.search_by_func("Tan",precise=True)
# 根据函数名查询该函数 -模糊查询
dv.func_doc.search_by_func("Tan",precise=False)


#step3:更高自由度下的自定义因子:内置的函数终究有限，add_formula可以通过事先定义并注册一些因子计算中需要的函数方法,完成更高自由度的因子计算
# 定义指数平均计算函数:传入一个时间为索引,股票为columns的Dataframe,计算其指数平均序列
# SMAtoday=m/n * Pricetoday + ( n-m )/n * SMAyesterday;  ???
def sma(df, n, m): #传入一个Dataframe,输入n和m
    a = n / m - 1
    r = df.ewm(com=a, axis=0, adjust=False)
    return r.mean()

dv.add_formula("double_SMA","SMA(SMA(close_adj,3,1),3,1)", #"double_SMA"表示新因子名称         
               is_quarterly=False, #is_quarterly=True是季度因子,is_quarterly=False为日度因子
               add_data=True, #add_data=True: 调用添加到数据集dv里,则计算结果之后可以反复调用
               register_funcs={"SMA":sma}).head() #？？？
               #register_funcs={"SMA":sma} 用于你自定义一种函数计算方式,然后可以直接通过你定义的方法名称(这里是“SMA”)在表达式里调用并进行计算(SMA(SMA(close_adj,3,1),3,1))
               #与前面直接使用内置的函数不同,这里需要先自定义
C=dv.get_ts("SMA") #得不到结果
C2=dv.get_ts("double_SMA") #可以得到结果

#3_用append_df自定义因子 构造一个因子表格，直接添加到dataview当中 ??#如何查询ta的函数
close = dv.get_ts("close_adj").dropna(how='all', axis=1) #若一列中全为NAN,则将它删除
slope_df = pd.DataFrame({sec_symbol: -ta.LINEARREG_SLOPE(value.values, 10) for sec_symbol, value in close.iteritems()}, index=close.index)
#每个股票每10天求斜率 -ta.LINEARREG_SLOPE(value.values, 10)
dv.append_df(slope_df,'slope') #用append_df方法将slope_df添加至本地(dataview数据集里),其新名称为'slope'
dv.get_ts('slope').tail()



#4_事件因子 事件是因子的一种特殊形式,一般用1/0/-1表示,股价走势发生金叉记为1，死叉记为-1，其他记位0
#step1:
from jaqs_fxdayu.research.signaldigger import process
Open = dv.get_ts("open_adj")
High = dv.get_ts("high_adj")
Low = dv.get_ts("low_adj")
Close = dv.get_ts("close_adj")
trade_status = dv.get_ts('trade_status') #获得是否停牌的情况
mask_sus = trade_status == u'停牌' #false表示未停牌,true表示停牌
# 将剔除掉停牌期的数据　再计算指标(即将上述得到的4个指标中的0值处理成NAN)：
open_masked = process._mask_df(Open,mask=mask_sus)
high_masked = process._mask_df(High,mask=mask_sus)
low_masked = process._mask_df(Low,mask=mask_sus)
close_masked = process._mask_df(Close,mask=mask_sus)  

#step2:计算因子5日均线,10日均线 jaqs_fxdayu.data import signal_function_mod as sfm()
from jaqs_fxdayu.data import signal_function_mod as sfm
MA5 = sfm.ta(ta_method='MA', #调用talib的函数,这里尽量多的输入参数,虽然不一定需要
             ta_column=0, #取tialib计算结果的列,例如计算MACD,就会有3个结果,这就可以指定取第几列
             Open=open_masked, 
             High=high_masked, 
             Low=low_masked, 
             Close=close_masked,
             Volume=None, #成交量
             timeperiod=5) #timeperiod=5时间周期
MA10 = sfm.ta('MA',Close=close_masked, timeperiod=10)
dv.append_df(MA5,'MA5')
dv.append_df(MA10,'MA10')

# 定义金叉事件 Delay表示前面几天
dv.add_formula("Cross","(MA5>=MA10)&&(Delay(MA5<MA10, 1))",is_quarterly=False, add_data=True) 
#"Cross"新因子名称,add_data=True即直接添加至数据集里
dv.get_ts("Cross").tail()


#step3:定义过滤条件
import numpy as np
#定义信号过滤条件-非指数成分
def mask_index_member():
    df_index_member = dv.get_ts('index_member')
    mask_index_member = df_index_member == 0 #0表示不是成分股票,1表示是成分股票
    return mask_index_member

#定义可买卖条件——未停牌、未涨跌停
def limit_up_down():
    trade_status = dv.get_ts('trade_status')
    mask_sus = trade_status == u'停牌'
    # 涨停 'up_limit'为新名称
    dv.add_formula('up_limit', '(close - Delay(close, 1)) / Delay(close, 1) > 0.095', is_quarterly=False, add_data=True)
    # 跌停 'down_limit'为新名称
    dv.add_formula('down_limit', '(close - Delay(close, 1)) / Delay(close, 1) < -0.095', is_quarterly=False, add_data=True)
    can_enter = np.logical_and(dv.get_ts('up_limit') < 1, ~mask_sus) # 未涨停未停牌
    can_exit = np.logical_and(dv.get_ts('down_limit') < 1, ~mask_sus) # 未跌停未停牌
    return can_enter,can_exit

mask = mask_index_member() #true表示不是成分股票,false表示是成分股票
can_enter,can_exit = limit_up_down() #是否可以买入和卖出,注意返回了两个参数


#step4:SignalDigger因子分析
# 和处理因子的步骤一样 n_quantiles=1
# 不传入benchmark 可以分析绝对收益
from jaqs_fxdayu.research import SignalDigger
obj = SignalDigger(output_folder='G:\data', #输出路径
                   output_format='pdf') #output_format='pdf'表示输出格式为pdf

obj.process_signal_before_analysis(signal=dv.get_ts("Cross"), #传入的因子,这里是dataframe格式,不同于alphalens需要传入的multiIndex格式
                                   price=dv.get_ts("close_adj"),
                                   high=dv.get_ts("high_adj"), # 可为空
                                   low=dv.get_ts("low_adj"),# 可为空
                                   n_quantiles=1,# quantile分类数,这里显然不用分组
                                   mask=mask,# 过滤条件
                                   can_enter=can_enter,# 是否能进场
                                   can_exit=can_exit,# 是否能出场
                                   period=15,# 持有期
                                   # benchmark_price=dv.data_benchmark, # 基准价格可不传入,则计算为绝对收益
                                   # 或者改为benchmark_price=None, #则计算的是绝对收益
                                   commission = 0.0008,
                                   )
signal_data = obj.signal_data #signal表示因子值,return表示持有期的收益率(买入并持有15天后的收益),upside_ret/ downside_ret代表在对应持有期下的最大上涨空间以及最大下跌空间(这里都是计算的绝对收益率)
signal_data.head()

#收益分析
from jaqs_fxdayu.research.signaldigger.analysis import analysis
result = analysis(signal_data, is_event=True, period=15) #is_event=True表示是事件类因子

print("——选股收益分析——")
print(result["ret"]) 
#long_ret这里无做空,但计算结果却有所不同,是因为考虑年化收益是把所有事件发生的股票都拿出来作为样本 计算年化收益。
#long_short_ret因为有多空 在计算年化收益的时候是把每天的选股收益取平均做年化,因而两者有一定的差别

print("——最大潜在盈利/亏损分析——")
print(result["space"])

# 可视化
import matplotlib.pyplot as plt
obj.create_full_report()
plt.show()
#Daily Quantile Return每日的收益曲线,Cumulative Return of Each Quantile累计收益曲线(持有所有的股票)
#Signal Weighted Long Only Portfolio Cumulative Return 只做多因子值为正的股票的收益情况(若不如前者,说明策略就是没跑过基准收益,是无效的策略)
#Signal Weight Short Only Portfolio Cumulative Return 只做空因子值为负的股票的收益情况(这里无负数的因子,固无股票入选) 
#top,Minus Bottom Quantile Return:top_quantile_ret/bottom_quantile_ret:做多因子值(按quantile分类)最大的组合收益/做多因子值最小(按quantile分类)的组合收益  

# 小实验：
a=0
for i in range(len(signal_data.signal)):
    if signal_data.signal.iloc[i]==1:
        a=a+1








