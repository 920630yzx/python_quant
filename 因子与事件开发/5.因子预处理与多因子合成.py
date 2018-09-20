#1_初始化
from jaqs_fxdayu.data import DataView 
import warnings

warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'
dv = DataView()
dv.load_dataview(dataview_folder)
dv.add_formula("momentum", "Return(close_adj, 20)", is_quarterly=False, add_data=True) #直接使用内置的函数,添加新因子,可能之前已经添加过了
dv.get_ts("momentum").head()
print(dv.fields) #查看dv中取得的数据

import numpy as np

#定义过滤条件
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

mask = mask_index_member() #true表示不在指数中,false表示在指数中
can_enter,can_exit = limit_up_down() #得到两个dataframe的结果



#2_对pb、pe、ps、float_mv、momentum五个因子进行比较、筛选   multi_factor.get_factors_ic_df()
from jaqs_fxdayu.research.signaldigger import multi_factor

ic = dict()
#！！！注意下表达方式
factors_dict = {signal:dv.get_ts(signal) for signal in ["pb","pe","ps","float_mv","momentum"]} #挑选5个因子,#float_mv表示市值
for period in [5, 15, 30]: #分别在5天、15天、30天
    ic[period]=multi_factor.get_factors_ic_df(factors_dict, #传入由不同因子所构成的字典
                                              price=dv.get_ts("close_adj"), #dataframe格式数据,下面两个一样
                                              high=dv.get_ts("high_adj"), # 可为空
                                              low=dv.get_ts("low_adj"),# 可为空
                                              n_quantiles=5,# quantile分类数
                                              mask=mask,# 过滤条件
                                              can_enter=can_enter, #是否能进场
                                              can_exit=can_exit, #是否能出场
                                              period=period, #持有期 for period in [5, 15, 30]: 
                                              benchmark_price=dv.data_benchmark, #基准价格,计算结果为相对收益;也可不传入,持有期收益（return）计算为绝对收益
                                              commission = 0.0008,
                                              )

#step2：计算IC值以进行分析
import pandas as pd
#！！！注意下表达方式
ic_mean_table = pd.DataFrame(data=np.nan,columns=[5,15,30],index=["pb","pe","ps","float_mv","momentum"]) #创建一个dataframe;其内容全是NAN;列名为5,10,15;索引共有5个
ic_std_table = pd.DataFrame(data=np.nan,columns=[5,15,30],index=["pb","pe","ps","float_mv","momentum"])
ir_table = pd.DataFrame(data=np.nan,columns=[5,15,30],index=["pb","pe","ps","float_mv","momentum"])
for signal in ["pb","pe","ps","float_mv","momentum"]: 
    for period in [5, 15, 30]:
        ic_mean_table.loc[signal,period]=ic[period][signal].mean() #运行下: ic[5]["pb"]
        ic_std_table.loc[signal,period]=ic[period][signal].std()
        ir_table.loc[signal,period]=ic[period][signal].mean()/ic[period][signal].std()

print(ic_mean_table) #打印ic的均值
print(ic_std_table) #打印ic的标准差
print(ir_table) #打印ic的信息比率: ic的均值/ic的标准差  

#可视化比较 (这里是对IC的均值进行比较)
ic_mean_table.plot(kind="barh",xerr=ic_std_table,figsize=(15,5))
# 检验：kind="barh",xerr=ic_std_table是调整图形的表达形式;figsize=(15,5)为调整图形大小
'''
ic_mean_table.plot() #会画出折现图,这里不好做比较
ic_mean_table.plot(kind="barh")
ic_mean_table.plot(kind="barh",xerr=ic_std_table)
'''
#可视化比较 IC_IR:方差标准化后的ic均值
ir_table.plot(kind="barh",figsize=(15,5))



#3_因子预处理
#根据之前的分析,可知momentum、ps、pe、pb这4个因子在几个持有期下与股票收益的关系(ic)都是负的,故需进一步分析这4个人因子
#先统一调整成正相关关系,并且需要完成以下几个步骤
#去极值
#标准化 -- z-score/rank; z-score标准化,也称为标准化分数,这种方法根据原始数据的均值和标准差进行标准化(会保留因子原有的基本分布信息),
#经过处理后的数据符合标准正态分布,即均值为0,标准差为1(根据下面的转化函数很容易证明),转化函数为：(X-均值)/标准差.而rank标准化会保留因子的排序信息,但会删除因子的分布信息.
#行业市值中性化(这一步是为了防止所选股票的因子在行业或市值上有过多的暴露,(例如:所选股票全是某一行业或全是小市值的股票))
from jaqs_fxdayu.research.signaldigger import process

factor_dict = dict() #处理后的因子factor_dict
index_member = dv.get_ts("index_member")
for name in ["pb","pe","ps","momentum"]:
    signal = -1*dv.get_ts(name) # 调整符号  这里表示统一调整成正相关关系
    process.winsorize(factor_df=signal,alpha=0.05,index_member=index_member) #factor_df=signal是输入的因子值,alpha=0.05表示去掉因子值左右两端5%的数值,
    #index_member=index_member表示需要传入的是否是指数成分的一个dataframe,传入后仅会处理指数成分股,对非指数成分股则不会进行处理
    signal = process.standardize(signal,index_member) #z-score标准化 保留排序信息和分布信息
#     signal = process.rank_standardize(signal,index_member) #rank标准化 因子在截面排序并归一化到0-1(只保留排序信息)
#     # 行业市值中性化(这步可以做也可以不做,其作用是在横截面上把行业风格与市值风格给剔除掉)
#     signal = process.neutralize(signal,
#                                 group=dv.get_ts("sw1"),# 行业分类标准
#                                 float_mv = dv.get_ts("float_mv"), #流通市值 可为None 则不进行市值中性化
#                                 index_member=index_member,# 是否只处理时只考虑指数成份股
#                                 )
    factor_dict[name] = signal #输出结果,结果为字典



#4_施密特正交化
''' 对筛选后的因子进行组合,一般有以下常规处理：    
1:因子间存在较强同质性时,可以使用施密特正交化方法对因子做正交化处理,用得到的正交化残差作为因子,这样可以剔除同质化部分.
但是这也有一个弊端:由于正交化会破坏因子的经济学逻辑,并剔除一些原有的信息(包括原因子之间的联系,这可能导致不好的影响),造成与原因子差别太大,固也可以不使用或谨慎使用.
2:因子组合加权,常规的方法有：等权重、以某个时间窗口的滚动平均ic为权重(理由是ic越大因子效果越好,因而分配更多的权重)、
以某个时间窗口的滚动ic_ir为权重(与前面同理,同时考虑了预测效益即稳定性)、最大化(使上一期因子效果最大化)上个持有期的ic_ir为目标处理权重、最大化上个持有期的ic为目标处理权重 
注:因为计算IC需要用到下一期股票收益,因此在动态加权方法里,实际上使用的是前一期及更早的IC值(向前推移了holding_period)计算当期的权重.也就是说当前的ic是绝对不能使用的,使用了未来函数。
'''

#因子间存在较强同质性时,使用施密特正交化方法对因子做正交化处理,用得到的正交化残差作为因子  multi_factor.orthogonalize施密特正交化
new_factors = multi_factor.orthogonalize(factors_dict=factor_dict, #正交化不会增加减少NAN,但会改变数值
                           standardize_type="rank",#输入因子标准化方法,有"rank"（排序标准化）,"z_score"(z-score标准化)两种（"rank"/"z_score"）
                           winsorization=False,#是否对输入因子去极值
                           index_member=index_member) #　是否只处理指数成分股

new_factors



#5_这里还是用正交化前的因子,分别进行等权、以某个时间窗口的滚动平均ic为权重、以某个时间窗口的滚动ic_ir为权重、
#最大化上个持有期的ic_ir为目标处理权重、最大化上个持有期的ic为目标处理权重的加权组合方式.共5种方式测试组合因子表现

#step1:合成新的因子comb_factors：  multi_factor.combine_factors() 
#rollback_period代表滚动窗口所用到的天数,即用前多少期的数据来计算现阶段的因子权重.通常建议设置时间在半年以上,可以获得相对稳定的预期结果
#多因子组合-动态加权参数配置
props = {
    'price':dv.get_ts("close_adj"),
    'high':dv.get_ts("high_adj"), # 可为空
    'low':dv.get_ts("low_adj"),# 可为空
    'ret_type': 'return',#'return'表示持有期的收益,可选参数还有upside_ret/downside_ret 则组合因子将以优化潜在上行、下行空间为目标？？？
    'benchmark_price': dv.data_benchmark,  # 为空计算的是绝对收益　dv.data_benchmark则表示计算相对收益
    'period': 30, # 30天的持有期,这里还表示在30天下进行的最佳合成
    'mask': mask,
    'can_enter': can_enter,
    'can_exit': can_exit,
    'forward': True,
    'commission': 0.0008,
    "covariance_type": "shrink",  # "shrink"表示的是压缩协方差矩阵估算方法 还可以为"simple"协方差矩阵估算方法
    "rollback_period": 120}  # 滚动窗口天数

#测试:multi_factor.combine_factors();comb_factors是合成因子(将上述4个因子进行合成),这里的合成方法预设有5种(5种方法好好理解下？)
comb_factors = dict()
for method in ["equal_weight","ic_weight","ir_weight","max_IR","max_IC"]: #分别表示进行等权、以某个时间窗口的滚动平均ic为权重、
#以某个时间窗口的滚动ic_ir为权重、最大化上个持有期的ic_ir为目标处理权重、最大化上个持有期的ic为目标处理权重的加权组合方式(上文中提及)
    comb_factors[method] = multi_factor.combine_factors(factor_dict, #因子的字典,其中Key为因子的名称,因子的value为dataframe
                                                        standardize_type="rank", #输入因子标准化方法,有"rank"(排序标准化),"z_score"(z-score标准化)两种（"rank"/"z_score"）
                                                        winsorization=False, #对合成的因子去极值,例如：0.05表示去掉因子值左右两端5%的数值
                                                        weighted_method=method, #可选的加权方法(5种)
                                                        props=props) #props是上面已经配置好的配置信息
    print(method)
    print(comb_factors[method].dropna(how="all").head())



#step2：计算新因子的ic_30(即ic分析)
#比较组合前和组合后的因子在30日持有期下的表现(统一到2014年9月后进行比较.这是由于上面用到了一个时间的滚动窗口"rollback_period": 120)
ic_30=multi_factor.get_factors_ic_df(comb_factors,
                                     price=dv.get_ts("close_adj"),
                                     high=dv.get_ts("high_adj"), # 可为空
                                     low=dv.get_ts("low_adj"),# 可为空
                                     n_quantiles=5,# quantile分类数
                                     mask=mask,# 过滤条件
                                     can_enter=can_enter,# 是否能进场
                                     can_exit=can_exit,# 是否能出场
                                     period=period,# 持有期  对比前者for period in [5, 15, 30]
                                     benchmark_price=dv.data_benchmark, #基准价格,计算结果为相对收益;也可不传入(或者benchmark_price=None),持有期收益（return）计算为绝对收益
                                     commission = 0.0008,
                                          )
ic_30 = pd.concat([ic_30,-1*ic[30].drop("float_mv",axis=1)],axis=1) #将ic中key=30(取负值并剔除float_mv列)与ic_30合并,得到新的ic_30.由于预处理中我们将因子取负,索引这里仍然需要去负值.
ic_30.head()


#ic_30的分析:(统一到2014年9月后进行比较.这是由于上面用到了一个时间的滚动窗口"rollback_period":120),得到的ic_30中前面大量的NAN数据会影响结果
ic_30_mean = dict()
ic_30_std = dict()
ir_30 = dict()
#注意以下表达！！！
for name in ic_30.columns:    #ic_30的每一列 
    ic_30_mean[name]=ic_30[name].loc[20140901:].mean() #计算均值
    ic_30_std[name]=ic_30[name].loc[20140901:].std() #计算标准差
    ir_30[name] = ic_30_mean[name]/ic_30_std[name] #计算均值/标准差,即ic的信息比率: ic的均值/ic的标准差
    
import datetime
trade_date = pd.Series(ic_30.index) #提取索引
trade_date = trade_date.apply(lambda x: datetime.datetime.strptime(str(x), '%Y%m%d')) #调整trade_date表达方式！！！
ic_30.index = trade_date #调整ic_30的索引表达方式

#step3：可视化比较及分析
#对IC的均值进行比较：
pd.Series(ic_30_mean).plot(kind="barh",xerr=pd.Series(ic_30_std),figsize=(15,5)) 
print(ic_30_mean["equal_weight"])
print(ic_30_mean["ic_weight"])
print(ic_30_mean["pe"])

#ir_30_std是ic的方差,很明显由于只有1个数据,就不需要做题了

#对ir_30进行可视化比较:方差标准化后的ic均值,即ic均值/ic的标准差,即ic的信息比率
pd.Series(ir_30).plot(kind="barh",figsize=(15,5)) #均可以看出采用等权重的方法进行重组因子的确取得了很好的效果,获得了更好的因子

#画出三个因子的时间序列,可以观察到不同时间段的因子表现情况：
ic_30[["equal_weight","ic_weight","pe"]].plot(kind="line",figsize=(15,5),)
#在原有的基础上调整了输出的时间：
ic_30.loc[datetime.date(2017,1,3):,][["equal_weight","ic_weight","pe"]].plot(kind="line",figsize=(15,5),)


#step4:查看等权合成因子的详情报告 process_signal_before_analysis()：与第二章SignalDigger因子分析完全一样,至此可以之前单一因子对比,看合成因子效果如何:
import matplotlib.pyplot as plt
from jaqs_fxdayu.research.signaldigger.analysis import analysis
from jaqs_fxdayu.research import SignalDigger

obj = SignalDigger() #这里与第二章不同,对比下
obj.process_signal_before_analysis(signal=comb_factors["equal_weight"],
                                   price=dv.get_ts("close_adj"),
                                   high=dv.get_ts("high_adj"), # 可为空
                                   low=dv.get_ts("low_adj"),# 可为空
                                   n_quantiles=5,# quantile分类数
                                   mask=mask,# 过滤条件
                                   can_enter=can_enter,# 是否能进场
                                   can_exit=can_exit,# 是否能出场
                                   period=30,# 持有期
                                   benchmark_price=dv.data_benchmark, # 基准价格 可不传入，持有期收益（return）计算为绝对收益
                                   commission = 0.0008,
                                   )
obj.create_full_report()
plt.show()

signal_data = obj.signal_data #得到因子值
result = analysis(signal_data, is_event=False, period=30) #得到分析表格
print(analysis(obj.signal_data,is_event=False,period=30)) #与上面完全一样

'''进一步测试下等权合成因子的绝对收益效果 可以尝试运行下
obj.process_signal_before_analysis(signal=comb_factors["equal_weight"],
                                   price=dv.get_ts("close_adj"),
                                   high=dv.get_ts("high_adj"), # 可为空
                                   low=dv.get_ts("low_adj"),# 可为空
                                   n_quantiles=5,# quantile分类数
                                   mask=mask,# 过滤条件
                                   can_enter=can_enter,# 是否能进场
                                   can_exit=can_exit,# 是否能出场
                                   period=30,# 持有期
                                   #benchmark_price=dv.data_benchmark, #这行注释掉即可
                                   commission = 0.0008,
                                   )
obj.create_full_report()
plt.show()
'''


#step5:将结果保存成excel !!!
excel_data = obj.signal_data[obj.signal_data['quantile']==5]["quantile"].unstack().replace(np.nan, 0).replace(5, 1)
print (excel_data.head())
excel_data.to_excel('G:\data\equal_weight_quantile_5.xlsx')






''' 数据获取,暂时不管,以后再说
A=ds.index_daily(['000300.SH'],20170101,20171228,'close')
ds.index_daily(['000300.SH'],20170101,20171228,'close') 
ds.index_daily(['000300.SH'],20170101,20171230,  'trade_date,close')[0].set_index('trade_date') 
hs300_props = {'start_date': start, 'end_date': end, 'universe': '000300.SH',
         'fields': 'pe_ttm,ps_ttm,pb,pcf_ocfttm,ebit,roe,roa,price_div_dps,total_mv,float_mv,sw1',
         'freq': 1}
'''

df,msg = ds.daily("000001.SH",start_date=20140101,end_date=20150101, adjust_mode="post")



