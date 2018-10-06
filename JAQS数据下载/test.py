from jaqs.data import DataView
from jaqs.data import RemoteDataService
import os
import numpy as np
import warnings

warnings.filterwarnings("ignore")

data_config = {
    "remote.data.address": "tcp://data.quantos.org:8910",
    "remote.data.username": "13662241013",
    "remote.data.password": "eyJhbGciOiJIUzI1NiJ9.eyJjcmVhdGVfdGltZSI6IjE1MTc2NDQzMzg5MTIiLCJpc3MiOiJhdXRoMCIsImlkIjoiMTM2NjIyNDEwMTMifQ.sVIzI5VLqq8fbZCW6yZZW0ClaCkcZpFqpiK944AHEow"
}

ds = RemoteDataService()
ds.init_from_config(data_config)
dv = DataView()

start=20160104
end=20180104

hs300_props = {'start_date': start, 'end_date': end, 'universe': '000300.SH',
         'fields': 'pe_ttm,ps_ttm,pb,pcf_ocfttm,ebit,roe,roa,price_div_dps,total_mv,float_mv,sw1',
         'freq': 1}

gem_props = {'start_date': start, 'end_date': end, 'universe': '399606.SZ',
         'fields':'pe_ttm,ps_ttm,pb,pcf_ocfttm,ebit,roe,roa,price_div_dps,total_mv,float_mv,sw1',
         'freq': 1}

def save_hs300(props):
    dataview_folder = '../JAQS_Data/hs300'
    if not (os.path.isdir(dataview_folder)):
        os.makedirs(dataview_folder)
    dv.init_from_config(props, ds)
    dv.prepare_data()
    dv.save_dataview(dataview_folder)
    
def save_gem(props):
    dataview_folder = '../JAQS_Data/gem'
    if not (os.path.isdir(dataview_folder)):
        os.makedirs(dataview_folder)
    dv.init_from_config(props, ds)
    dv.prepare_data()
    dv.save_dataview(dataview_folder)

save_hs300(hs300_props)
save_gem(gem_props)
