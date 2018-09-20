#Alphalen是什么？ Alphalens是一个Python包,用于对阿尔法因子进行性能分析.Alpha因子表示一些
#给定的信息和未来的回报之间的预测关系.通过将这种关系应用于多个股票，能够产生阿尔法信号，
#然后从中交易。Alphalens是一个Python包，用于对阿尔法因子进行性能分析.Alpha因子表示一些给定的
#信息和未来的回报之间的预测关系.通过将这种关系应用于多个股票，能够产生阿尔法信号，然后从中交易。
#通过Alphalens分析你在研究中的因素,你可以花更少的时间来写和运行回测.因此,这允许更快的思想迭代，
#以及最终的算法，您可以对它有信心.Alphalens建立了一个严格的工作流程,将使你的策略更有活力,更不容易过度拟合。



#1_数据准备工作
from jaqs_fxdayu.data import DataView  #可以视为一个轻量级的数据库，数据格式基于pandas，方便数据的调用和处理
from jaqs_fxdayu.data import RemoteDataService #数据服务，用于下载数据
import os
import warnings

warnings.filterwarnings("ignore")
dataview_folder = 'G:/data/hs300_2'

if not (os.path.isdir(dataview_folder)):
    os.makedirs(dataview_folder)

#2_数据下载
def save_dataview():
    data_config = {
    "remote.data.address": "tcp://data.tushare.org:8910",
    "remote.data.username": "18161280526",
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MjMwMTkwMTkyMDUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTgxNjEyODA1MjYifQ.Kqx03_5DsQKOurLlQDY7GPRPoRbMisxABuNMG5zTe3Q" #QuantOs API令牌
    }
    ds = RemoteDataService()
    ds.init_from_config(data_config)
    
    dv = DataView()
    props = {'start_date': 20140101, 'end_date': 20180101, 'universe': '000300.SH', #'universe': '000300.SH'表示标的股票池取的是沪深300
             'fields': "pb,pe,ps,float_mv,sw1,roe", #'fields'表示取的数据,pb,pe,ps分别表示市净率,市盈率,市销率;float_mv代表流通市值,sw1表示申万1级行业分类的数据
             'freq': 1}  

    dv.init_from_config(props, ds)
    dv.prepare_data()
    dv.save_dataview(dataview_folder) # 保存数据文件到指定路径，方便下次直接加载
    
    
save_dataview()

# 加载数据
dv = DataView()
dv.load_dataview(dataview_folder)

print(dv.fields) #查看dv中取得的数据
print(dv.get_ts("pb").head()) #查看dv中取得的市净率



#3_因子分析 
#step1:因子收集及处理
import pandas as pd
from datetime import datetime

factor=dv.get_ts("pb")
factor.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , factor.index)) 
# 改时间索引: 将整数类型的日期转成datetime的格式的日期datetime.strptime  (注意pd.Index,I要大写)
factor=factor.stack() #修改成Mutiindex格式(Alphalen因子分析必要) 得到一窜Series

#这里先定义一个函数,方便下次的转换
def change_index(df):
    df.index=pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , df.index))
    return df

price=dv.get_ts("close") #close得到的真实价格,即除权的价格
prices=dv.get_ts("close_adj") #获取向后复权价格,由于复权因子与所处时间不同,可能与其他软件的数据有一定的差异
prices=change_index(prices)  #直接调用函数


#step2：因子分析 alphalens.utils.get_clean_factor_and_forward_returns()
import alphalens
factor_data=alphalens.utils.get_clean_factor_and_forward_returns(factor,prices,quantiles=5,periods=(1,5,10))
print(factor_data.head())
#factor即之前的pb因子,prices即后复权的价格(dataframe格式),quantiles=5表示将factor分为5个档次,factor越大quantiles也会获得更大的评级
#periods=(1,5,10)表示当天买入,分别持有1天、5天、10天后卖出的收益
#在输出的结果中,如果因子值(这里是factor)越大,股票涨势越好,说明这个因子对我们选出好的股票有帮助;反之,因子值越大,股票表现无规律,则这个因子就不是个好因子;
#最后,若因子值越大,股票表现越差,则可作为一种反向的指标.
#也就是说好的因子应具有这样的规律:factor_quantile(或者factor)越大则股票表现越好,越小则股票表现越差.若每个组别还呈现出显著的递增式差异,这样是最好的.

#step2.2：因子分析 alphalens.utils.get_clean_factor_and_forward_returns()
import matplotlib.pyplot as plt
mean_return_by_q, std_err_by_q=alphalens.performance.mean_return_by_quantile(factor_data,by_date=True,demeaned=True)
#by_date=True表示按每天求平均,若不输则求所有的样本期内的平均收益(建议尝试下);demeaned=True表示求相对收益

alphalens.plotting.plot_cumulative_returns_by_quantile(mean_return_by_q, 1) #1天持有期收益
alphalens.plotting.plot_cumulative_returns_by_quantile(mean_return_by_q, 5) #5天持有期收益
alphalens.plotting.plot_cumulative_returns_by_quantile(mean_return_by_q, 10) #10天持有期收益
plt.show()


#step3：计算信息系数IC值 alphalens.performance.factor_information_coefficient() 
#spearman相关系数(IC)： 因子值大小的排序与股票收益大小的排序的一个相关度,IC用于评估因子的好坏,用来反应因子值大小与股票收益的相关程度的指标;IC越高说明正相关性越高,那么因子值越大的股票表现会越好。
#IC系数在[-1,1]之间,越大正相关性就越强,一般|mean(IC)|>0.02即可判定因子有效; spearman(IC)=1-6*(∑ d^2)/n^3-n  其中d表示示秩次差
#秩次差: 若A=[1,3,5,7,9] ;B=[3,2,4,5,1]  d为排序相减则：  d^2=0,1,1,9,16
ic=alphalens.performance.factor_information_coefficient(factor_data)
ic.head()
#ic值若>0表示因子值越大收益越大,ic值若<0表示因子值越小收益越大,但是仅仅观察几天的值是没有意义的,更需要看整体情况

#step3.2: 进一步观察IC值的情况
alphalens.plotting.plot_ic_hist(ic) #画出IC值的分布,从Mean平均值可以看出整体的情况,若Mean(IC)<0就表示因子值与股票是一个负相关
alphalens.plotting.plot_ic_ts(ic) #画出IC的时间序列曲线,若时间序列曲线有时为正有时为负数(围绕0上下波动),就说明这个因子变化较大,不是很可靠,好的指标应稳定在0轴的上方或者下方
plt.show()  

#step3.3：月均IC热度图
mean_monthly_ic=alphalens.performance.mean_information_coefficient(factor_data, by_time='M')
alphalens.plotting.plot_monthly_ic_heatmap(mean_monthly_ic) #因子月度表现
plt.show()  



#4 将结果输出保存成EXCEL：将Quantile1的选股结果保存成excel
import numpy as np
excel_data = factor_data[factor_data['factor_quantile']==1]["factor_quantile"].unstack().replace(np.nan, 0) #保存factor_quantile=1的行,且只取factor_quantile列中的值
#factor_data['factor_quantile']是factor_data中的factor_quantile列
excel_data.to_excel('G:\data\pb_quantile_1.xlsx') #另存为excel！！！



#5_因子在不同板块的选股能力分析: 有些因子对整个股市效果不好,但对某个板块可能具有较好的效果
#step1：alphalens.utils.get_clean_factor_and_forward_returns() 
sectors=dv.get_ts('sw1')  #按照申万的分类标准获得股票的分类结果
sectors=change_index(sectors) #修改index
sectors.head()
factor_data_2=alphalens.utils.get_clean_factor_and_forward_returns(factor,prices,
                                                                   groupby=sectors.stack(), #sectors.stack()表示sectors的MultiIndex格式,groupby=sectors.stack()即分类情况
                                                                   quantiles=5,periods=(1,5,10)) #对比下与factor_data 有哪些不同,多了哪些参数

ic_by_sector=alphalens.performance.mean_information_coefficient(factor_data_2, by_group=True) #得到行业(板块)平均IC值

import matplotlib.pyplot as plt #画图得到行业的IC情况,IC>0表示正相关即：因子值越大股票收益越大
alphalens.plotting.plot_ic_by_group(ic_by_sector)
plt.show()



