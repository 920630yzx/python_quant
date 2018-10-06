#1_先导入模块
from jaqs_fxdayu.data import DataView
from jaqs_fxdayu.data import RemoteDataService
import os
import numpy as np
import warnings
warnings.filterwarnings("ignore") #将警告给过滤掉

#2_设置Config
data_config = {
    "remote.data.address": "tcp://data.quantos.org:8910",  #地址统一,暂不做修改
    "remote.data.username": "18161280526",  #quantos账号(手机号码)
     # quantos账号的API令牌号码
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MjMwMTkwMTkyMDUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTgxNjEyODA1MjYifQ.Kqx03_5DsQKOurLlQDY7GPRPoRbMisxABuNMG5zTe3Q"
}

#3_初始化数据服务与数据接口,成功登陆
ds = RemoteDataService()         # DataService启动
ds.init_from_config(data_config) # data_config启动
dv = DataView() # DataView初始化

#4_设置Props并用字典保存需要的参数
start=20180104
end=20180611

hs300_props = {'start_date': start, 'end_date': end, 'universe': '000300.SH',
         'fields': 'pe_ttm,ps_ttm,pb,pcf_ocfttm,ebit,roe,roa,price_div_dps,total_mv,float_mv,sw1',
         'freq': 1}
#'start_date': start, 'end_date': end分别代表起始时间与结束时间,'universe'表示需要的板块
#'fields'表示所需的因子,'freq': 1代表以日线为主

gem_props = {'start_date': start, 'end_date': end, 'universe': '399606.SZ',
         'fields':'pe_ttm,ps_ttm,pb,pcf_ocfttm,ebit,roe,roa,price_div_dps,total_mv,float_mv,sw1',
         'freq': 1}



#5_下载数据到本地文件
def save_hs300(props):
    dataview_folder = 'G:/data/hs300_611' #设置保存地址
    if not (os.path.isdir(dataview_folder)):  
        os.makedirs(dataview_folder)      #若没有改地址,则创建一个          
    dv.init_from_config(props, ds)        #先将DataView初始化并输入props和ds
    dv.prepare_data()                     #准备数据
    dv.save_dataview(dataview_folder)     #保存数据

def save_gem(props):
    dataview_folder = 'G:/data/gem'
    if not (os.path.isdir(dataview_folder)):
        os.makedirs(dataview_folder)
    dv.init_from_config(props, ds)
    dv.prepare_data()
    dv.save_dataview(dataview_folder)

save_hs300(hs300_props)
save_gem(gem_props)









#数据获取  
#jaqs_fxdayu.data.dataservice.RemoteDataService.daily(symbol, start_date, end_date, fields="", adjust_mode=None)
df,msg = ds.daily("000001.SH",start_date=20140101,end_date=20180101, adjust_mode="post") #fields=""表示全部symbol,code,date,time,trade_date,freq,open,high,low,close,volume,turnover,vwap,oi
df,msg = ds.daily("000001.SH",start_date=20140101,end_date=20180101, fields="symbol, code, date, time, trade_date",adjust_mode="post") 

#获取分钟级数据
df,msg = ds.bar("000001.SZ,000002.SZ", trade_date =20180328,  freq="1M")
df,msg = ds.bar("000001.SZ,000002.SZ", start_date=20180101, end_date=201804028, trade_date =20180328, freq="1M")






