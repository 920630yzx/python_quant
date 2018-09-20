#SignalDigger:是一个Python第三方库,专门用于选股因子alpha(α)的绩效分析.它是alphalens的功能集成简化版，
#针对A股市场交易制度（如涨跌停）专门进行了一些细节上的优化，适合初学者迅速掌握和使用

#1_数据准备工作
from jaqs_fxdayu.data import DataView # 可以视为一个轻量级的数据库，数据格式基于pandas，方便数据的调用和处理
from jaqs_fxdayu.data import RemoteDataService # 数据服务，用于下载数据
import os
import warnings


warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'

if not (os.path.isdir(dataview_folder)):
    os.makedirs(dataview_folder)
    
# 数据下载
def save_dataview():
    data_config = {
    "remote.data.address": "tcp://data.tushare.org:8910",
    "remote.data.username": "18161280526",
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MjMwMTkwMTkyMDUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTgxNjEyODA1MjYifQ.Kqx03_5DsQKOurLlQDY7GPRPoRbMisxABuNMG5zTe3Q" #QuantOS API令牌
    }
    ds = RemoteDataService()
    ds.init_from_config(data_config)

    dv = DataView()
    props = {'start_date': 20140101, 'end_date': 20180101, 'universe': '000300.SH',
             'fields': "volume,pb,pe,ps,float_mv,sw1",
             'freq': 1}

    dv.init_from_config(props, ds)
    dv.prepare_data()
    dv.save_dataview(dataview_folder) # 保存数据文件到指定路径,方便下次直接加载

save_dataview()    
    
# 加载数据
dv = DataView()
dv.load_dataview(dataview_folder) #加载数据   
print(dv.fields) #查看dv中取得的数据
print(dv.get_ts("pb").head()) #查看dv中取得的市净率

import numpy as np

#定义信号过滤条件-非指数成分
def mask_index_member():
    df_index_member = dv.get_ts('index_member') #A=dv.get_ts('index_member'),1表示在沪深300中,0表示不在沪深300中
    mask_index_member = df_index_member == 0 #过滤
    return mask_index_member

# 定义可买卖条件——未停牌、未涨跌停
def limit_up_down():
    trade_status = dv.get_ts('trade_status')
    mask_sus = trade_status == u'停牌'
    # 定义涨停 'up_limit'
    dv.add_formula('up_limit', '(close - Delay(close, 1)) / Delay(close, 1) > 0.095', is_quarterly=False, add_data=True)
    # 定义跌停 'down_limit'
    dv.add_formula('down_limit', '(close - Delay(close, 1)) / Delay(close, 1) < -0.095', is_quarterly=False, add_data=True)
    can_enter = np.logical_and(dv.get_ts('up_limit') < 1, ~mask_sus) # 未涨停未停牌
    can_exit = np.logical_and(dv.get_ts('down_limit') < 1, ~mask_sus) # 未跌停未停牌
    return can_enter,can_exit

mask = mask_index_member() #是否需要过滤该支股票：这里false表示不用过滤该股票,true表示需要过滤掉该股票
can_enter,can_exit = limit_up_down() #是否能够买入/卖出：can_enter中true表示可以买入,false表示不能买入;can_exit中true表示可以卖出,false表示不能卖出



#2_SignalDigger处理因子  obj.process_signal_before_analysis():
#step1:
from jaqs_fxdayu.research import SignalDigger
obj = SignalDigger(output_folder='G:\data2', #输出路径
                   output_format='pdf') #output_format='pdf'表示输出格式为pdf

# 处理因子 计算目标股票池每只股票的持有期收益，和对应因子值的quantile分类
obj.process_signal_before_analysis(signal=dv.get_ts("pb"), #传入的因子,这里是dataframe格式,不同于alphalens需要传入的multiIndex格式
                                   price=dv.get_ts("close_adj"),#这里的price,high,low是需要计算的价格
                                   high=dv.get_ts("high_adj"), # 可为空(可以不写这一行)
                                   low=dv.get_ts("low_adj"),# 可为空(可以不写这一行)
                                   group=dv.get_ts("sw1"),# 可为空(可以不写这一行) ,这里选择申万的分类方式
                                   n_quantiles=5,# quantile分类数
                                   mask=mask,# 过滤条件
                                   can_enter=can_enter,# 是否能进场
                                   can_exit=can_exit,# 是否能出场
                                   period=15,# 持有期
                                   benchmark_price=dv.data_benchmark, #基准价格 可不传入,持有期收益（return）计算为绝对收益,这里写了则表示计算收益为相对与指数的收益.也可以以其他指数为标准
                                   #改为benchmark_price=None, #则计算的是绝对收益
                                   commission = 0.0008, #手续费,在alphalens中就不能设置手续费
                                   )

#得到因子值：
signal_data = obj.signal_data  #signal表示因子值,return表示持有期的收益率(买入并持有15天后的相对收益),upside_ret/ downside_ret代表在对应持有期下的最大上涨空间以及最大下跌空间(这里都是计算的绝对收益率)
signal_data.head()
    
    
#step2: 因子分析    
from jaqs_fxdayu.research.signaldigger.analysis import analysis
result = analysis(signal_data, is_event=False, period=15) # is_event=False表示不是事件类因子,period=15研究周期
#这里会得到一个字典(含三个索引)  
#return_ic/upside_ret_ic/downside_ret_ic： 表示持有期收益的ic/持有期(股票暴涨)最大向上空间的ic/持有期(股票暴跌)最大向下空间的ic

#long_ret/short_ret/long_short_ret/top_quantile_ret/bottom_quantile_ret/tmb_ret/all_sample_ret 表示：
#多头组合收益(做多因子值为正的股票)/空头组合收益(做空因子值为负的股票)/多空组合收益(做多因子值为正的股票,做空因子值为负的股票)/
#/做多因子值(按quantile分类)最大的组合收益/做多因子值最小(按quantile分类,后同)的组合收益/因子值最大组（构建多头）+因子值最小组（构建空头）收益/全样本(例如这里研究的沪深300的股票)-基准组合收益

#long_space/short_space/long_short_space/top_quantile_space/bottom_quantile_space/tmb_space/all_sample_space 表示：
#(与上面一行一一对应)多头组合空间/空头组合空间/多空组合空间/因子值最大组合空间/因子值最小组合空间/因子值最大组（构建多头）+因子值最小组（构建空头）空间/全样本（无论信号大小和方向）-基准组合空间

#而关于索引项（ic或收益的具体指标）:
#"IC Mean", "IC Std.", "t-stat(IC)", "p-value(IC)", "IC Skew", "IC Kurtosis", "Ann. IR" 表示：
#IC均值,IC标准差,IC的t统计量,对IC做0均值假设检验的p-value,IC偏度,IC峰度,iC的年化信息比率-mean(IC)/std(IC)  (一般|IC的均值|>0.02,|iC的年化信息比率|>0.6就可认为因子效果会比较好)

#'t-stat',"p-value","skewness","kurtosis","Ann. Ret","Ann. Vol","Ann. IR","occurance" 表示：
#持有期收益的t统计量,对持有期收益做0均值假设检验的p-value,偏度,峰度,Ann. Ret:持有期收益年化值,年化波动率,年化信息比率:年化收益/年化波动率,occurance样本数量.

#'Up_sp Mean','Up_sp Std','Up_sp IR','Up_sp Pct5', 'Up_sp Pct25 ','Up_sp Pct50 ', 'Up_sp Pct75','Up_sp Pct95','Up_sp Occur',
#上行空间均值，上行空间标准差，上行空间信息比率-均值/标准差，上行空间5%分位数,..25%分位数，..中位数，..75%分位数,..95%分位数，上行空间样本数;   
#'Down_sp Mean','Down_sp Std','Down_sp IR','Down_sp Pct5','Down_sp Pct25','Down_sp Pct50','Down_sp Pct75','Down_sp Pct95','Down_sp Occur'表示：   
#上行空间均值，上行空间标准差，上行空间信息比率-均值/标准差，上行空间5%分位数,..25%分位数，..中位数，..75%分位数,..95%分位数，上行空间样本数;    

#打印result这个字典：
print("——ic分析——")
print(result["ic"])
print("——选股收益分析——")
print(result["ret"])
print("——最大潜在盈利/亏损分析——")
print(result["space"]) 
    
    
    
#3_因子分析可视化  obj.create_full_report()
#累计收益计算方法：将资金按持有天数等分,每天取一份买入所选股票-可以用该方式复制投资组合
#相对收益计算方法：减去benchmark对应持有期的收益 
import matplotlib.pyplot as plt
obj.create_full_report()
plt.show()   
#Daily Quantile Return每日的收益曲线,Cumulative Return of Each Quantile累计收益曲线(持有Quantile下所有的股票)(按照Quantile分类下买入所有股票,若Quantile只有1则表示买入全部股票)
#Signal Weighted Long Only Portfolio Cumulative Return 只做多因子值为正的股票的收益情况(根据因子值的大小进行加权的组合)
#Signal Weight Short Only Portfolio Cumulative Return  只做空因子值为负的股票的收益情况(根据因子值的大小进行加权的组合) (这里PB无负数的因子,固无股票入选) 
#top Minus Bottom Quantile Return,top Minus Bottom (long top,short bottom)Quantile Return:做多因子值(按quantile分类)最大的同时做空因子值最小(按quantile分类,后同)的组合收益  
#区别在于第一个求每日收益曲线(类似概率密度),第二个求累积收益曲线(类似于分布函数)  


#step2:分组分析
from jaqs_fxdayu.research.signaldigger import performance as pfm
ic = pfm.calc_signal_ic(signal_data, by_group=True)
mean_ic_by_group = pfm.mean_information_coefficient(ic, by_group=True)

from jaqs_fxdayu.research.signaldigger import plotting
plotting.plot_ic_by_group(mean_ic_by_group)
plt.show()



#4_保存
excel_data = signal_data[signal_data['quantile']==1]["quantile"].unstack().replace(np.nan, 0)
print (excel_data.head())
excel_data.to_excel('G:\data\pb_quantile_2.xlsx')







    
    