# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json


def create_tuple(response):
    response_data = response.json()
    response_datum = response_data[0]
    response_target = response_datum['target']
    response_datapoints = response_datum['datapoints']
    tuple_array = [tuple(x) for x in response_datapoints]
    npa = np.array(tuple_array, dtype=[
                   ('value', np.double), ('ts', 'datetime64[ms]')])
    return npa


def fume_query(target, server, start, end):
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
    print(request)
    # print(request.json())
    return create_tuple(request)

# fume_query(target="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash", server="biotech_main", start="2021-12-25T00:00:00.000", end=current_date())


def outside_temp(start, end):
    # https://ypsu0n34jc.execute-api.us-east-1.amazonaws.com/dev/query doesn't work
    # https://portal.emcs.cornell.edu/api/datasources/proxy/5/query works
    # https://portal-api.emcs.cucloud.net/query works
    url = "https://portal-api.emcs.cucloud.net/query"
    target = "GameFarmRoadWeatherStation.TAVG_H_F"
    data = {
        "range": {
            "from": start,
            "to": end
        },
        "targets": [
            {
                "target": target,
            }
        ]
    }
    request = requests.post(url, json=data)
    print(request)
#   print(request.json())
    return create_tuple(request)


def query(target_list, server, start, end):
    cfm_master = fume_query(target_list[0], server, start, end)
    sash_master = fume_query(target_list[3], server, start, end)
    occ_master = fume_query(target_list[2], server, start, end)
    internal_temp_master = fume_query(target_list[1], server, start, end)
    external_temp_master = outside_temp(start, end)

    cfm_list = pd.Series(data=[i[0] for i in cfm_master], index=[
                         i[1] for i in cfm_master])
    print("CFM List: ", cfm_list)
    cfm_list = cfm_list[~cfm_list.index.duplicated()]
    print("CFM List new: ", cfm_list)

    sash_list = pd.Series(data=[i[0] for i in sash_master], index=[
                          i[1] for i in sash_master])
    print("\nSash List: ", sash_list)
    sash_list = sash_list[~sash_list.index.duplicated()]
    print("\nSash List new: ", sash_list)

    occ_list = pd.Series(data=[i[0] for i in occ_master], index=[
                         i[1] for i in occ_master])
    print("\nOCC List: ", occ_list)
    occ_list = occ_list[~occ_list.index.duplicated()]
    print("\nOCC List new: ", occ_list)

    internal_temp_list = pd.Series(data=[i[0] for i in internal_temp_master], index=[
                                   i[1] for i in internal_temp_master])
    print("\nInternal Temp List: ", internal_temp_list)
    internal_temp_list = internal_temp_list[~internal_temp_list.index.duplicated(
    )]
    print("\nInternal Temp List new: ", internal_temp_list)

    external_temp_list = pd.Series(data=[i[0] for i in external_temp_master], index=[
                                   i[1] for i in external_temp_master])
    print("\nExternal Temp List: ", external_temp_list)
#   external_temp_list = pd.read_csv("C:/Users/Dan/Documents/GitHub/fume-hood-dashboard/game_farm/hist.csv", index_col=0).squeeze()
#   external_temp_list.index = external_temp_list.index.astype('datetime64[ns]')
    print("\nExternal Temp List: ", external_temp_list)

    df = pd.concat([cfm_list, sash_list, occ_list,
                   internal_temp_list, external_temp_list], axis=1)
    df.columns = ["cfm", "sash", "occ", "internal temp", "external temp"]

    df = df.dropna()

    df["BTUh"] = 1.08 * df["cfm"] * (df["internal temp"] - df["external temp"])
    
    return df


app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Fume Hood Dashboard'),

    html.P("A (very basic, preliminary) web dashboard for Cornell Fume Hoods"),

    html.Label('Date Range'),
    dcc.Dropdown(["Last day", "Last week", "Last month"],
                 "Last week", id="date-selector"),

    html.P(id="total-btu"),
    html.P(id="total-btu-occ"),
    html.P(id="total-btu-unocc"),
    html.P(id="percent-occ"),

    dcc.Loading(
      id = "is-loading",
      children=[
        dcc.Graph(
            id="energy-graph",
            # figure=fig
        )],
        type="circle"
    )

])


@app.callback(
    # the "figure" refers to the "figure" parameter of the Graph component
    Output("energy-graph", "figure"),
    Output("total-btu", "children"),
    Output("total-btu-occ", "children"),
    Output("total-btu-unocc", "children"),
    Output("percent-occ", "children"),
    Input("date-selector", "value")
)
def update_graph(date):
    days = 0
    if date == "Last day":
        days = 1
    elif date == "Last week":
        days = 7
    else:
        days = 30

    target_list = ["#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hoodvalve_flow/trend_log",
                   "#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/zone/zone_temp/trend_log",
                   "#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                   "#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash"]
    server = "biotech_main"
    start = str(datetime.now() - timedelta(days=days))
    end = str(datetime.now())

    final_df = query(target_list, server, start, end)

    fig = px.line(final_df)
    total_btu = f'Total energy used (BTUh): {final_df["BTUh"].sum()}'
    total_btu_occ = f'Total BTUh occupied: {final_df["BTUh"][final_df["occ"] == 1.0].sum()}'
    total_btu_unocc = f'Total BTUh unoccupied: {final_df["BTUh"][final_df["occ"] == 0].sum()}'
    percent_occ = f'Percent occupied: {len(final_df[final_df["occ"] == 1.0]) / len(final_df)}'
    return fig, total_btu, total_btu_occ, total_btu_unocc, percent_occ


if __name__ == '__main__':
    app.run_server(debug=True)
