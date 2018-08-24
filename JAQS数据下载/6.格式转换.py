#1_读取本地数据
from jaqs.data import DataView
import os
import numpy as np
import warnings
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

dataview_folder = 'G:/data/hs300'
dv = DataView()
dv.load_dataview(dataview_folder)



#2_修改索引与列名
from datetime import timedelta

def change_columns_index(signal):
    # 改名称
    new_names = {}
    for c in signal.columns:
        if c.endswith('SZ'):  #若是上证股票
            new_names[c] = c.replace('SZ', 'XSHE')  #则将SZ改为XSHE
        elif c.endswith('SH'):  #若是深证股票
            new_names[c] = c.replace('SH', 'XSHG')  #则将SH改为XSHG
    signal = signal.rename_axis(new_names, axis=1)  
    # 改时间索引: # 改时间索引: 将整数类型的日期转成datetime的格式的日期datetime.strptime ：
    signal.index = pd.Index(map(lambda x: datetime.strptime(str(x),"%Y%m%d") , signal.index))
    # 然后加15个小时:   (x+timedelta(hours=15)) ：
    signal.index = pd.Index(map(lambda x: x+timedelta(hours=15) , signal.index))
    return signal

factor = change_columns_index(dv.get_ts('roe_pb_Q5'))  #对roe_pb_Q5进行修改

print(factor.tail())











