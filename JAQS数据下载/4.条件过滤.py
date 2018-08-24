#1_读取本地数据
import jaqs_fxdayu
jaqs_fxdayu.patch_all()
from jaqs_fxdayu.data import DataView
from jaqs_fxdayu.data import RemoteDataService
import os
import numpy as np
import warnings

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300_2' #档案地址
dv = DataView()
dv.load_dataview(dataview_folder) #加载档案地址,结果出现Dataview loaded successfully则成功

print(dv.fields) #查看dv中取得的数据

#2_过滤停牌涨跌停（可买可卖） mask_index_member为要过滤的为True,can_enter与can_exit皆为可交易为True
from jaqs_fxdayu.util import dp
from jaqs.data.dataapi import DataApi

A=dv.get_ts('index_member') #得到一张表,1表示在指数成分里,0表示不在指数成分里
B=dv.get_ts('trade_status') #得到一张表,从中可以得出股票能否交易(或停牌)

def mask_index():
    df_index_member = dv.get_ts('index_member')
    mask_index_member = df_index_member==0 #定义信号过滤条件-非指数成分,若df_index_member==0则mask_index_member=true
    return mask_index_member


def limit_up_down():
    # 定义可买卖条件——未停牌、未涨跌停
    trade_status = dv.get_ts('trade_status')
    mask_sus = trade_status == u'停牌'
    # 涨停:
    dv.remove_field('up_limit')
    dv.add_formula('up_limit', '(close - Delay(close, 1)) / Delay(close, 1) > 0.095', is_quarterly=False, add_data=True)
    # 跌停:
    dv.remove_field('down_limit')
    dv.add_formula('down_limit', '(close - Delay(close, 1)) / Delay(close, 1) < -0.095', is_quarterly=False, add_data=True)
    can_enter = np.logical_and(dv.get_ts('up_limit') < 1, ~mask_sus) # 未涨停dv.get_ts('up_limit') < 1,未停牌(~mask_sus):即可以进场
    can_exit = np.logical_and(dv.get_ts('down_limit') < 1, ~mask_sus) # 未跌停dv.get_ts('down_limit') < 1,未停牌(~mask_sus)：即可以出场
    return can_enter,can_exit

mask_index_member = mask_index()
can_enter,can_exit = limit_up_down()

#3_添加数据
# dv.remove_field('mask_index_member')
# dv.remove_field('can_enter')
# dv.remove_field('can_exit')
dv.append_df(mask_index_member, 'mask_index_member') #后面是给新因子的名称
dv.append_df(can_enter, 'can_enter')
dv.append_df(can_exit, 'can_exit')

#保存:
dv.save_dataview('G:/data/hs300')
print(dv.get_ts('mask_index_member').head())
X1=dv.get_ts('mask_index_member') #true表示不在指数成分里,false表示在指数成分里
X2=dv.get_ts('can_enter') #可以买入
X3=dv.get_ts('can_exit') #可以卖出
 
















