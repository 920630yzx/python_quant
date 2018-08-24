#1_读取本地数据
import jaqs_fxdayu
jaqs_fxdayu.patch_all() #新加
from jaqs.data import DataView
from jaqs.data import RemoteDataService
import os
import numpy as np
import warnings
warnings.filterwarnings("ignore")

dv = DataView()
dataview_folder = 'G:/data/hs300' #文件地址
dv.load_dataview(dataview_folder) #读取dataview_folder

#2_读取索引为股票代号的数据 get_snapshot
print(dv.get_snapshot(20170504, symbol='600036.SH,600050.SH', fields=''))
print(dv.get_snapshot(20170504, symbol='600036.SH,600050.SH', fields='close_adj'))
#20170504表示时间,symbol='600036.SH,600050.SH'表示股票(可以添加),fields=''表示因子,若不输则会返回全部的因子

#3_读取时间序列数据 get_ts
data1=dv.get_ts('pb') #返回的是一个DataFrame格式的数据(包含沪深300全部),pb表示平均市净率
print(dv.get_ts('pb').head()) 

#4_添加自定义算法数据 add_formul
roe_pb = dv.add_formula('roe_pb', 'roe/pb', is_quarterly=False, add_data=True)
#'roe_pb'表示算法的新名称,'roe/pb'为公式,is_quarterly=False代表是否为季度数据
print(dv.get_ts('roe_pb').head()) #这里用get_ts的方法输入新的名称即可

#5_从数据服务添加新数据至本地
#先设置Config
data_config = {
    "remote.data.address": "tcp://data.tushare.org:8910",  #地址统一,暂不做修改
    "remote.data.username": "18161280526",  #quantos账号(手机号码)
    #quantos账号的API令牌号码
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MjMwMTkwMTkyMDUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTgxNjEyODA1MjYifQ.Kqx03_5DsQKOurLlQDY7GPRPoRbMisxABuNMG5zTe3Q"
}
ds = RemoteDataService() #DataService启动
ds.init_from_config(data_config) #data_config启动

dv.add_field('eps_basic', ds) #添加新数据(eps_basic)至本地(ds)
print(dv.get_ts('eps_basic').head())
A=dv.get_ts('eps_basic').head() #get_ts为数据获取

dv.remove_field('eps_basic') #删除数据(eps_basic)
dv.add_field('volume', ds) #添加新数据至本地(ds)
A=dv.get_ts('volume').head()

dv.save_dataview('G:/data/hs300') #保存
dv.save_dataview('G:/data/hs300_1') #这相当于另存为

print(dv.fields) #查看dv中取得的数据

dv.add_field('roe', ds) #添加新数据至本地(ds)



