#1_读取本地数据
import jaqs_fxdayu
jaqs_fxdayu.patch_all()
from jaqs_fxdayu.data import DataView
from jaqs_fxdayu.data import RemoteDataService
import os
import numpy as np
import warnings

warnings.filterwarnings("ignore")

dv = DataView()
dataview_folder = 'G:/data/hs300'
dv.load_dataview(dataview_folder)



#2_因子绩效 例子以roe_pb为因子
factor = dv.get_ts('roe_pb')  #之前自定义做的roe/pb的因子(需要先运行前面第二节roe_pb)
print(factor.tail())

#读取数据：
mask = dv.get_ts('mask_index_member')  #是否在指数成分里
can_enter = dv.get_ts('can_enter')  #能否买入
can_exit = dv.get_ts('can_exit')  #能否卖出
price = dv.get_ts('close_adj')  #价格
group = dv.get_ts('group')  #分类信息

print(can_enter.shape)
print(group.shape)

#定义函数：
import matplotlib.pyplot as plt
from jaqs.research import SignalDigger  #jaqs.research自带的挖掘器SignalDigger
import warnings

def cal_obj(signal, name, period, quantile):
    obj = SignalDigger()  #SignalDigger实体化,下面调用它的方法process_signal_before_analysis
    obj.process_signal_before_analysis(signal,   #因子数据
                                   price=price,  #价格数据
                                   n_quantiles=quantile,  #百分位
                                   period=period, #持有周期
                                   can_enter = can_enter,  #能买入
                                   can_exit = can_exit,  #能卖出
                                   group=group,  #行业分类表格
                                   mask=mask  #指数成分的过滤
                                   )
    obj.create_full_report()   #创建一个完整的report
    return obj

def plot_pfm(signal, name, period=5, quantile=5): #quantile=5是最好的区分度
    obj = cal_obj(signal, name, period, quantile)
    plt.show()   #画图

def signal_data(signal, name, period=5, quantile=5): 
    obj = cal_obj(signal, name, period, quantile)
    return obj.signal_data    #得到一个详细的数据



#3_画图展示：
plot_pfm(factor,'roe_pb', period=5, quantile=5)
#ic值  t-value:t检验,p-value:pvalue,IC SKew:偏度,IC Kurtosis:峰度
#Daily Quantile Return:每个Quantile的收益率,Cumulative Return of Each Quantile：每个Quantile的累计收益率
#Signal Weighted Long Only Portfolio Cumulative Return 多头的收益率
#Signal Weighted Short Only Portfolio Cumulative Return 空头的收益率
#Top Minus Bottom Quantile Return 多空收益(多减空的一个收益)
#Top Minus Bottom (long top,short bottom) Portfolip Cumulative Return (做多Quantile高的,做空Quantile低的的收益率)
#Daily IC and Moving Average: IC的均值;Distribution Daily IC: IC的分布;IC Monthly Mean；每个月IC的值



#4_信号表格:
signal_df = signal_data(factor, 'roe_pb') #signal:因子值,return:收益率(未来5天的收益率)(period=5),quantile:百分位
print(signal_df.head(100))

Q5 = signal_df.signal[signal_df['quantile']==5] #先判断'quantile'是否等于5返回一列true或者false,是true的话则记录signal
Q5[Q5>0]=1 #将这些列中的元素转标记成1
dv.append_df(Q5.unstack(),'roe_pb_Q5') #在dv中加入一列Q5.unstack(),'roe_pb_Q5'为列名  可以运行下A=Q5.unstack()以方便查看
dv.get_ts('roe_pb_Q5')  #读取roe_pb_Q5
dv.save_dataview('G:/data/hs300')














