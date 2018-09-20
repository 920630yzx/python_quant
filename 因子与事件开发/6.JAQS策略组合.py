#1_读取选股结果
import pandas as pd

strategy1 = pd.read_excel('divert_opt_quantile_5.xlsx').set_index("trade_date")
strategy2 = pd.read_excel('equal_weight_quantile_5.xlsx').set_index("trade_date")

strategy1.head()



#2_为不同的选股方案设置不同的偏好(权重),以控制选股结果    
#step1:下面是打分法的案例:
import numpy as np
combined_result=1*strategy1.replace(np.nan,0)+1*strategy2.replace(np.nan,0) 
#这里是等权重,当然也有其他的权重方式,也可按个人喜好;同时,就算strategy1,strategy2维度不同也可对应相加



#step2:取交集 ！！！
Intersection = combined_result[combined_result==2].fillna(0).replace(2,1) #fillna(0)将NAN填充成0,同理replace(2,1)将2置换成1
Intersection.head()


#step3:取并集 ！！！
Union = combined_result[combined_result>0].fillna(0)
Union[Union>0] = 1 #将Union中大于0的全部元素变为1
Union.head()



#3_测试策略组合效果
#step1:数据准备
from jaqs_fxdayu.data import DataView 
import warnings
import numpy as np

warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)

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


#step2: #用append_df的方法将slope_df添加至本地(dataview数据集里)
print(dv.fields) #查看dv中取得的数据
dv.append_df(field_name="Union",df=Union,is_quarterly=False) #用append_df方法将"Union"添加至本地(dataview数据集里),其新名称为df=(Union)
dv.append_df(field_name="Intersection",df=Intersection,is_quarterly=False)
dv.save_dataview('G:/data/hs300_2')  #保存,若不运行,则下次重新运行不会有Union和Intersection

#step3:新因子分析:
from jaqs_fxdayu.research import SignalDigger
import matplotlib.pyplot as plt
from jaqs_fxdayu.research.signaldigger.analysis import analysis

obj = SignalDigger(output_folder='G:/data',
                   output_format='pdf')

def draw_analysis(signal="Union",benchmark_price=None): #同样类似于第二章SignalDigger处理因子的方式,不过这里是定义函数
    obj.process_signal_before_analysis(signal=dv.get_ts(signal),
                                       price=dv.get_ts("close_adj"),
                                       high=dv.get_ts("high_adj"), #可为空
                                       low=dv.get_ts("low_adj"), #可为空
                                       n_quantiles=1,# quantile分类数
                                       mask=mask, #过滤条件
                                       can_enter=can_enter,# 是否能进场
                                       can_exit=can_exit,# 是否能出场
                                       period=30,# 持有期
                                       benchmark_price=benchmark_price, # 基准价格 可不传入,则持有期收益（return）计算为绝对收益
                                       commission = 0.0008,
                                       )
    print(analysis(obj.signal_data,is_event=True,period=30)) # is_event=False表示不是事件类因子,period=15研究周期
    obj.create_full_report() 
    plt.show()


#计算并集绩效 相对收益
draw_analysis('Union',dv.data_benchmark) #dv.data_benchmark表示相对收益
#并集绩效 绝对收益
draw_analysis('Union',None)
#计算交集绩效 相对收益
draw_analysis('Intersection',dv.data_benchmark) #dv.data_benchmark表示相对收益
#交集绩效 绝对收益
draw_analysis('Intersection',None)



#4_保存至excel
Intersection.to_excel('G:/data/Intersection.xlsx')
Union.to_excel('G:/data/Union.xlsx')







