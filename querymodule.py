import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json
import matplotlib.pyplot as plt
import math
import scipy.stats as st

from dateutil import parser
import matplotlib.dates as mdates

def create_tuple(response):
    response_data = response.json()
    response_datum = response_data[0]
    response_target = response_datum['target']
    response_datapoints = response_datum['datapoints']
    tuple_array = [tuple(x) for x in response_datapoints]
    npa = np.array(tuple_array, dtype=[
        ('value', np.double), ('ts', 'datetime64[ms]')])
    return npa

def fume_query(target,server, start,end):
    url = "https://ypsu0n34jc.execute-api.us-east-1.amazonaws.com/dev/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": [
            {
                "payload": {
                    "schema": server,
                },
                "target": target
            }
        ],

    }
    request = requests.post(url, json=data)
    #print(request)
    # print(request.json())
    return create_tuple(request)

def query_to_list(point, server, start, end):
    master = fume_query(point, server, start, end)

    list = pd.Series(data=[i[0] for i in master], index=[i[1] for i in master])
    #print("\n", point, "\n", list)

    list = list[~list.index.duplicated()]
    #print("\n", point, " new\n", list)

    return list

def total_time_sash_open(sash_point, occ_point, server, start, end, is_occupied):
    sash_list = query_to_list(sash_point, server, start, end)
    occ_list = query_to_list(occ_point, server, start, end)

    df = pd.concat([sash_list, occ_list], axis=1)
    df.columns = ["sash", "occ"]
    display(df)

    time_interval = df.index[1].minute - df.index[0].minute
    print("Time interval", time_interval)

    # Figure out closed sash position
    # display(df["sash"].value_counts())

    # from running the above on a large time difference, 1.2 inches is the most common smallest value
    df["time_open_mins"] = np.where((df["sash"] > 1.2), time_interval, 0)

    df = df.dropna()
    df.index = df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))
    display(df)

    df = df[df['occ']==int(is_occupied)]

    display(df)

    df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

    return df["time_open_mins"]

def coldorhot(cfm, external, internal, time_interval):
    if external<=internal:
        #sensible heating equation
        return 1.08 * cfm * (internal - external) / (60 / time_interval)
    if external>internal:
        #enthalpy of air
        return 0.24 * cfm /13.333 * 60 * (external - internal) / (60 / time_interval)

def total_energy(cfm_point, sash_point, occ_point, internal_temp_point, external_temp_point, server, start, end, is_occupied):
    #external_temp_master = outside_temp(start,end)
    cfm_list = query_to_list(cfm_point, server, start, end)
    sash_list = query_to_list(sash_point, server, start, end)
    occ_list = query_to_list(occ_point, server, start, end)
    internal_temp_list = query_to_list(internal_temp_point, server, start, end)
    external_temp_list = query_to_list(external_temp_point, server, start, end)

    df = pd.concat([cfm_list, sash_list, occ_list, internal_temp_list, external_temp_list], axis=1)
    df.columns = ["cfm", "sash", "occ", "internal_temp", "external_temp"]
    display(df)

    df["external_temp"] = df["external_temp"].interpolate()
    display(df)

    time_interval = df.index[1].minute - df.index[0].minute

    df['BTU'] = df.apply(lambda df: coldorhot(df['cfm'], df['external_temp'], df['internal_temp'], time_interval=time_interval), axis=1)
    df.index = df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))
    display(df)

    df = df[df['occ']==int(is_occupied)]

    print("\nFinal Data Frame: ")
    display(df)

    df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

    return df["BTU"]