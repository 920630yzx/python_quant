#1_连接数据源
import jaqs_fxdayu
jaqs_fxdayu.patch_all()
from jaqs_fxdayu.data.dataapi import DataApi
from jaqs_fxdayu.data import DataView

api = DataApi(addr='tcp://data.tushare.org:8910')
api.login("18161280526",   #quantos账号(手机号码)
          'eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MjMwMTkwMTkyMDUiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTgxNjEyODA1MjYifQ.Kqx03_5DsQKOurLlQDY7GPRPoRbMisxABuNMG5zTe3Q')
#quantos账号的API令牌号码



#2_获取需要的数据 index_cons ; daily_index_cons
#step1_指数成分
from jaqs_fxdayu.util import dp 
start=20120104
end=20171222
id_cons = dp.index_cons(api, "000300.SH", start, end) #可以得到各个股票进出沪深300的时间,out_date=999999表示现在仍在
#以下为一个小实验,统计出沪深300成分的数量:
k=id_cons.iloc[:,2]
i=0 #统计沪深300成分的数量
for s in k:
    if s==99999999:
        i=i+1

id_member = dp.daily_index_cons(api, "000300.SH", start, end) #与id_cons类似,这里输出的是更为详细的数据,精确到每一天,每一支股票,true表示这一天在沪深300中
mask = ~id_member #true变为false,false变为true
print(mask.tail())
 
#step2_行业分类信息 daily_sec_industry
symbol_id = dp.index_cons(api, "000300.SH", start, end)["symbol"].dropna() #得到沪深300全部的股票代码
symbols = ",".join(symbol_id) #将Series做成str形式,并用豆号隔开,得到一串股票代码symbols

group = dp.daily_sec_industry(api, symbols, start, end, source='sw', value="industry1_name")
#得到了这些股票的所属行业,source='sw'表示这里输出格式以申万为分类标准
print(group.tail())

group_code = dp.daily_sec_industry(api, symbols, start, end, source='sw', value="industry1_code")
print(group_code.tail()) #value="industry1_code"表示以industry1_name为分类标准,不过返回的code类型

group2 = dp.daily_sec_industry(api, symbols, start, end, source='sw', value="industry2_name")
print(group2.tail()) #value="industry2_name"表示另一种分类方式

group2_code = dp.daily_sec_industry(api, symbols, start, end, source='sw', value="industry2_code")
print(group2_code.tail()) #value="industry1_code"表示以industry2_name为分类标准,不过返回的code类型(类别代号)

group3 = dp.daily_sec_industry(api, symbols, start, end, source='zz', value="industry1_name")
print(group3.tail()) #source='zz'表示以中证为分类标准,只是分类标准不同而已

group3_code = dp.daily_sec_industry(api, symbols, start, end, source='zz', value="industry1_code")
print(group3_code.tail()) #source='zz'表示以中证为分类标准,只是分类标准不同而已,industry1_code返回的是类别代号(code类型)



#3_添加数据保存
dv = DataView()
dataview_folder = 'G:/data/hs300' #档案地址
dv.load_dataview(dataview_folder) #加载档案地址
dv.append_df(group, 'group')  #将group列加入dv中,后面的'group'为列名
dv.save_dataview('G:/data/hs300')  #保存

#获取数据
print(dv.get_ts('group').tail())
A=dv.get_ts('group') #这样看的更清楚点
        






