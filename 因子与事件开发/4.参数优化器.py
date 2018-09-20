#1_初始化
from jaqs_fxdayu.data import DataView 
import warnings

warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

#定义过滤条件
import numpy as np
def mask_index_member():
    df_index_member = dv.get_ts('index_member')
    mask_index_member = ~(df_index_member >0) #定义信号过滤条件-非指数成分
    return mask_index_member

def limit_up_down():
    # 定义可买卖条件——未停牌、未涨跌停
    trade_status = dv.get_ts('trade_status')
    mask_sus = trade_status == u'停牌'
    # 涨停
    dv.add_formula('up_limit', '(close - Delay(close, 1)) / Delay(close, 1) > 0.095', is_quarterly=False, add_data=True)
    # 跌停
    dv.add_formula('down_limit', '(close - Delay(close, 1)) / Delay(close, 1) < -0.095', is_quarterly=False, add_data=True)
    can_enter = np.logical_and(dv.get_ts('up_limit') < 1, ~mask_sus) # 未涨停未停牌
    can_exit = np.logical_and(dv.get_ts('down_limit') < 1, ~mask_sus) # 未跌停未停牌
    return can_enter,can_exit

mask = mask_index_member()
can_enter,can_exit = limit_up_down()



#2_运用参数优化器 from jaqs_fxdayu.research import Optimizer
from jaqs_fxdayu.research import Optimizer
''' 
:param dataview: 包含了计算公式所需要的所有数据的jaqs.data.DataView对象 
:param formula: str 需要优化的公式：如'(open - Delay(close, l1)) / Delay(close, l2)' 
:param params: dict 需要优化的参数范围：如{"LEN1"：range(1,10,1),"LEN2":range(1,10,1)} 
:param name: str (N) 信号的名称 
:param price: dataFrame (N) 价格与ret不能同时存在 
:param ret: dataFrame (N) 收益 
:param high: dataFrame (N) 最高价　用于计算上行收益空间 
:param low: dataFrame (N) 最低价　用于计算下行收益空间 
:param benchmark_price: dataFrame (N) 基准价格　若不为空收益计算模式为相对benchmark的收益 
:param period: int (5) 选股持有期 
:param n_quantiles: int (5) 
:param mask: 过滤条件 dataFrame (N) 
:param can_enter: dataFrame (N) 是否能进场 
:param can_exit: dataFrame (N) 是否能出场 
:param forward: bool(True) 是否forward return 
:param commission:　float(0.0008) 手续费率 
:param is_event: bool(False) 是否是事件(0/1因子) 
:param is_quarterly: bool(False) 是否是季度因子 
'''

#step1:因子参数优化
price = dv.get_ts('close_adj')
high = dv.get_ts('high_adj')
low = dv.get_ts('low_adj')
price_bench = dv.data_benchmark #指数收盘价
optimizer = Optimizer(dataview=dv,
                      formula='- Correlation(vwap_adj, volume, LEN)', #formula:这里是需要优化的因子,
                      #这里的定义是成交量加权的平均价格与成交量的相关关系的负值;LEN是参数,需要优化,表示时间长度,
                      params={"LEN":range(2,15,1)}, #设置时间长度,这里认为这些时间长度都有可能,我们就是要找到哪些参数是优秀的
                      name='divert', #因子的名称
                      price=price,
                      high=high,
                      low=low,
                      benchmark_price=None, #=None求绝对收益 #=price_bench求相对收益
                      period=30,
                      n_quantiles=5,
                      mask=mask,
                      can_enter=can_enter,
                      can_exit=can_exit,
                      commission=0.0008,#手续费 默认0.0008
                      is_event=False, #是否是事件(0/1因子),False表示不是事件因子
                      is_quarterly=False) #是否是季度因子 默认为False,表示不是季度因子

''' 可以参见本章第二节
target_type:
ic类: 
return_ic/upside_ret_ic/downside_ret_ic
持有收益类 
long_ret/short_ret/long_short_ret/top_quantile_ret/bottom_quantile_ret/tmb_ret
收益空间类 
long_space/short_space/long_short_space/top_quantile_space/bottom_quantile_space/tmb_space

target:
ic类 
"IC Mean", "IC Std.", "t-stat(IC)", "p-value(IC)", "IC Skew", "IC Kurtosis", "Ann. IR"
持有收益类 
't-stat', "p-value", "skewness", "kurtosis", "Ann. Ret", "Ann. Vol", "Ann. IR", "occurance"
收益空间类 
'Up_sp Mean','Up_sp Std','Up_sp IR','Up_sp Pct5', 'Up_sp Pct25 ','Up_sp Pct50 ', 'Up_sp Pct75','Up_sp Pct95','Up_sp Occur','Down_sp Mean',
'Down_sp Std', 'Down_sp IR', 'Down_sp Pct5','Down_sp Pct25 ','Down_sp Pct50 ','Down_sp Pct75', 'Down_sp Pct95','Down_sp Occur'
''' 

#step2:开始优化,得到一窜列表,按优化目标降序序排列
ret_best = optimizer.enumerate_optimizer(target_type="top_quantile_ret", #优化目标类型: 这里是做多因子值(按quantile分类)最大的组合收益
                                         target="Ann. IR", #优化目标: 这里是年化信息比率:年化收益/年化波动率  
                                         in_sample_range=[20140101,20160101], #选择优化的时间范围内范围  默认为None,表示在全样本上优化
                                         #这样做的目的是留下一部分样本进行检验,看优化的效果如何
                                         ascending=False) #是否按优化目标升序排列(从小到大),ascending=False表示按降序排列,也就是说得到的结果中第一行就是最优解


print(ret_best[0]["signal_name"]) #返回最优解的结果 'LEN': 12
print(ret_best[0]["ret"])
print(ret_best[0]["ic"])
print(ret_best[0]["space"])


#step3:进行可视化的操作
from jaqs_fxdayu.research import SignalDigger
from jaqs_fxdayu.research.signaldigger.analysis import analysis
import matplotlib.pyplot as plt
obj = SignalDigger()

def draw_analysis(signal_data,period):  
    obj.signal_data = signal_data
    obj.period = period
    obj.create_full_report()
    plt.show()

#全样本可视化操作:
draw_analysis(optimizer.all_signals[ret_best[0]["signal_name"]], period=30)

#当然,这里也可以仿制第二章中的方法,不定义函数,直接运行：
''''
obj.signal_data=optimizer.all_signals[ret_best[0]["signal_name"]]
obj.period = 30
obj.create_full_report()
plt.show()
''''

#样本内可视化:
draw_analysis(optimizer.all_signals[ret_best[0]["signal_name"]].loc[20140101:20160101], period=30)
A=optimizer.all_signals[ret_best[0]["signal_name"]].loc[20140101:20160101] #！！！,选择时间进行操作
#样本外可视化:
draw_analysis(optimizer.all_signals[ret_best[0]["signal_name"]].loc[20160101:], period=30)


#step4:运用参数优化器例2:
# 以持有期mean_ic为最优化目标
ic_best = optimizer.enumerate_optimizer(target_type="return_ic",#优化目标类型
                                        target = "IC Mean",
                                        in_sample_range=[20140101,20160101],#样本内范围 默认为None,在全样本上优化
                                        ascending=False)

print(ic_best[0]["signal_name"])
print(ic_best[0]["ic"])
print(ic_best[0]["ret"])
print(ic_best[0]["space"])


#step5: 把结果保存至excel中 ？？？
'''
A=optimizer.all_signals[ret_best[0]["signal_name"]][optimizer.all_signals[ret_best[0]["signal_name"]]['quantile']==5]["quantile"]
B=optimizer.all_signals[ret_best[0]["signal_name"]][optimizer.all_signals[ret_best[0]["signal_name"]]['quantile']==5]["quantile"].unstack()
C=excel_data = optimizer.all_signals[ret_best[0]["signal_name"]][optimizer.all_signals[ret_best[0]["signal_name"]]['quantile']==5]["quantile"].unstack().replace(np.nan, 0) #replace(np.nan, 0)表示将nan变换成0
'''
excel_data = optimizer.all_signals[ret_best[0]["signal_name"]][optimizer.all_signals[ret_best[0]["signal_name"]]['quantile']==5]["quantile"].unstack().replace(np.nan, 0).replace(5, 1) 
#1表示当日股票因子值划分为第五类的股票; optimizer.all_signals[ret_best[0]["signal_name"]]是因子结果;optimizer.all_signals["divert{'LEN': 12}"]与前者完全一样
print (excel_data.head())
excel_data.to_excel('G:\data\divert_opt_quantile_5.xlsx')



#3_事件参数优化 ？？？未完待续
event_opt = Optimizer(dataview=dv,
                      formula="(Ts_Mean(close_adj, SHORT)>=Ts_Mean(close_adj, LONG))&&(Delay(Ts_Mean(close_adj, SHORT)<Ts_Mean(close_adj, LONG), 1))",
                      params={'SHORT':range(5,11,1),'LONG':range(30,61,5)},
                      name='cross',
                      price=price,
                      high=high,
                      low=low,
                      benchmark_price=None,#=None求绝对收益 #=price_bench求相对收益
                      period=30,
                      n_quantiles=1,
                      mask=mask,
                      can_enter=can_enter,
                      can_exit=can_exit,
                      commission=0.0008,#手续费 默认0.0008
                      is_event=True,#是否是事件(0/1因子)
                      is_quarterly=False)#是否是季度因子 默认为False

event_best = event_opt.enumerate_optimizer(target_type="long_ret",
                                           target="Ann. IR",
                                           in_sample_range=[20140101,20160101],#样本内范围 默认为None,在全样本上优化
                                           ascending=False)

# 事件样本内最优绩效 ps：事件没有ic分析结果
# 可以进一步尝试优化space，辅以更精细的择时捕捉事件收益
print(event_best[0]["signal_name"])
print(event_best[0]["ret"])
print(event_best[0]["space"])

# 全样本
draw_analysis(event_opt.all_signals[event_best[0]["signal_name"]], period=30)
# 样本内
draw_analysis(event_opt.all_signals[event_best[0]["signal_name"]].loc[20140101:20160101], period=30)
# 样本外
draw_analysis(event_opt.all_signals[event_best[0]["signal_name"]].loc[20160101:], period=30)












