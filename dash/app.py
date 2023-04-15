# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
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
    df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

    return df["time_open_mins"]
    


app = Dash(__name__)


app.layout = html.Div(className="cols_wrapper", children=[
    html.Div(className="col_small", children=[
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=False,
            checked=['0-0-1'],
            selected=[],
            expanded=['0'],
            data={
                'title': 'Biotech',
                'key': 'Biotech',
                'children': [{
                    'title': 'Floor 1',
                    'key': 'Floor 1',
                    'children': [
                        {'title': 'Lab 1', 'key': 'Lab 1'},
                        {'title': 'Lab 2', 'key': 'Lab 2'},
                        {'title': 'Lab 3', 'key': 'Lab 3'},
                    ],
                }]}
        )
    ]),

    html.P("A (very basic, preliminary) web dashboard for Cornell Fume Hoods"),

    html.Label('Date Range'),
    dcc.Dropdown(["Last day", "Last week", "Last month"],
                 "Last week", id="date-selector"),

    html.P(id="total-btu"),
    html.P(id="total-btu-occ"),
    html.P(id="total-btu-unocc"),
    html.P(id="percent-occ"),


        html.P(id='breadcrumb'),

        html.Div(id='output-selected'),

        html.Div(className="cols_wrapper", children=[
            html.Div(className="col", children=[
                html.H3("Featured Rankings"),
                
                # Rankings box
                html.Div(className="box", children=[
                    html.H2("3rd Place"),
                    html.H4("on Olin Floor 3"),
                    html.P("Least avg. energy when unoccupied (2000 BTU/hr)")
                ]),

                html.Div(className="box", children=[
                    html.H2("1st Place"),
                    html.H4("on Olin Floor 3"),
                    html.P("Least avg. time when unoccupied (0 min/hr)")
                ]),
            ]),

            html.Div(className="col", children=[
                html.H3("Graphs"),

                dcc.Loading(
                    id="is-loading",
                    #fig = px.scatter(df, x = "Hour", y = "Minutes"),
                    children=[
                        dcc.Graph(
                            id="occ_graph",    
                            #figure=fig
                        )],
                    type="circle"
                )
            ])
        ])
    ])

@app.callback(Output('title', 'children'),
              [Input('input', 'selected')])
def update_title(selected):
    if selected:
        selected_item = selected[0]  # Assuming single selection
        return selected_item
    else:
        return 'Biotech' # Default value


@app.callback(Output('breadcrumb', 'children'),
              [Input('input', 'selected')])
def update_breadcrumb(selected):
    if selected:
        selected_item = selected[0]  # Assuming single selection
        
        if selected_item == 'Biotech':
            breadcrumb_text = html.A('Biotech', href='/biotech')
        elif selected_item == 'Floor 1':
            breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1')
        else:
            breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1'), ' / ', html.A(selected_item, href='/' + selected_item)
        
        return html.P(breadcrumb_text)
    else:
        breadcrumb_text = html.A('Biotech', href='/biotech')  # Default value
        return html.P(breadcrumb_text)

        
@app.callback(Output('output-selected', 'children'),
              [Input('input', 'selected')])
def _display_selected(selected):
    return 'You have checked {}'.format(selected)


# Variable Paths

def title(lab_id=None, floor_id=None):
    return f"Biotech Lab {lab_id} on Floor {floor_id}."

def description(lab_id=None, floor_id=None):
    return f"These are energy usage metrics for Lab {lab_id} on Floor {floor_id}."


dash.register_page(
    __name__,
    path_template = "/biotech/floor/<floor_id>",
)

"""
dash.register_page(
    __name__, 
    path_template = "/biotech/floor/<floor_id>/lab/<lab_id>",
    title = title,
    description = description
    )
"""
    
def layout(lab_id=None, floor_id=None):
    floor = "Floor "+str(floor_id),
    #update_title(floor)
    return html.Div(
        children=[
            html.H1(
        children = f"This is floor: {floor_id}.")
        ]     
    )

# Query Strings

"""
dash.register_page(__name__)

def layout(floor_id = None, lab_id=None):
    return html.Div(
        children=[
            html.H1(
        children = f"This is lab: {lab_id}.\nThis is floor: {floor_id}.")
        ]     
    )
"""

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
    occ_data = total_time_sash_open_unoccupied(sash_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash",
                                               occ_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                                               server="biotech_main",
                                               start=str(
                                                          datetime(2021, 11, 17, 1)),
                                               end=str(datetime(2021, 11, 17, 2)))
    print(occ_data)
    occ_fig = px.line(occ_data,
                      labels={
        "value": "Minutes Open",
        "index": "Date and Time",
        "variable": ""},
        title="Time Open When Unoccupied")
    return occ_fig



if __name__ == '__main__':
    app.run_server(debug=True)