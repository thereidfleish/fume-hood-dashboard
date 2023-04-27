import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json

app = Dash(__name__)

dash.register_page(__name__)


def layout(building=None, floor=None, lab=None, **other_unknown_query_strings):
    return html.Div(className="cols_wrapper", children=[
        # dcc.Location(id='url', refresh=False),  # URL location component

        dbc.Row([
            dbc.Col([
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=False,
                    checked=[],
                    selected=[],
                    expanded=["?building=biotech"],
                    data={
                        'title': 'Biotech',
                        'key': '?building=biotech',
                        'children': [{
                            'title': 'Floor 1',
                            'key': '?building=biotech&floor=1',
                            'children': [
                                {'title': 'Lab 1',
                                 'key': '?building=biotech&floor=1&lab=1'},
                                {'title': 'Lab 2',
                                 'key': '?building=biotech&floor=1&lab=2'},
                                {'title': 'Lab 3',
                                 'key': '?building=biotech&floor=1&lab=3'},
                            ],
                        }]}
                )
            ], width=3),

            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        html.H1(', '.join(filter(None, (building, floor, lab))))
                    ]),
                    dbc.Col([
                        html.Label('Metric'),
                        dcc.Dropdown(["BTU"],
                                     "BTU", id="metric_selector")
                    ]),
                    dbc.Col([
                        html.Label('Date Range'),
                        dcc.Dropdown(["Last day", "Last week", "Last month"],
                                     "Last week", id="date_selector")
                    ])
                ]),

                dbc.Row([
                    dbc.Col([
                        html.H3("Featured Rankings"),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("3rd Best",
                                                className="card-title"),
                                        html.H6("On Olin Floor 3"),
                                        html.P(
                                            "For least avg. energy when unoccupied (2000 BTU/hr)",
                                            className="card-text",
                                        )
                                    ]
                                ),
                            ], className="mb-2"),

                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("1st Best",
                                                className="card-title"),
                                        html.H6("On Olin Floor 3"),
                                        html.P(
                                            "For Least avg. time open when unoccupied (0 min/hr)",
                                            className="card-text",
                                        )
                                    ]
                                ),
                            ])
                    ]),
                    dbc.Col([
                        html.H3("Graphs"),
                        dcc.Loading(
                            id="is-loading",
                            children=[
                                dcc.Graph(
                                    id="sash_graph",
                                    # figure=fig
                                )],
                            type="circle"
                        ),
                        dcc.Loading(
                            id="is-loading",
                            children=[
                                dcc.Graph(
                                    id="energy_graph",
                                    # figure=fig
                                )],
                            type="circle"
                        )

                    ]),

                    dbc.Row([
                        html.H3("Comparative Metrics"),
                        dbc.Col([
                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="comparative_energyGraph",
                                        # figure=fig
                                    )],
                                type="circle"
                            ),
                            dbc.Row([
                                html.P("Olin 301's energy usage is 50 % higher than the most energy efficient lab on campus(Olin 303). ")
                            ])
                        ]),
                        dbc.Col([
                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="comparative_sashGraph",
                                        # figure=fig
                                    )],
                                type="circle"
                            ),
                            dbc.Row([html.P(
                                "Olin 301's sash position is 60% higher than the least open sash on campus (Olin 302).")
                            ])

                        ])

                    ]),

                ])

            ])

        ]),

        # Need this to do the page click callback for some reason!
        html.Div(id='output-selected')
    ])

# @callback(Output('title', 'children'),
#               [Input('input', 'selected')])
# def update_title(selected):
#     if selected:
#         selected_item = selected[0]  # Assuming single selection
#         return selected_item
#     else:
#         return 'Biotech' # Default value


# @callback(Output('breadcrumb', 'children'),
#               [Input('input', 'selected')])
# def update_breadcrumb(selected):
#     if selected:
#         selected_item = selected[0]  # Assuming single selection

#         if selected_item == 'Biotech':
#             breadcrumb_text = html.A('Biotech', href='/biotech')
#         elif selected_item == 'Floor 1':
#             breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1')
#         else:
#             breadcrumb_text = html.A('Biotech', href='/biotech'), ' / ', html.A('Floor 1', href='/floor1'), ' / ', html.A(selected_item, href='/' + selected_item)

#         return html.P(breadcrumb_text)
#     else:
#         breadcrumb_text = html.A('Biotech', href='/biotech')  # Default value
#         return html.P(breadcrumb_text)


# @app.callback(Output("url", "pathname"), [Input("input", "selected_item")])
# def update_url_path(selected_item):
#     if selected_item is not None:
#         print("/" + selected_item["value"])
#         return "/" + selected_item["value"]
#     return "/"


# @app.callback(Output("page-info", "children"), [Input("url", "pathname")])
# def update_page_content(pathname):
#     if pathname:
#         # extract floor number and lab number from URL path
#         parts = pathname.split("/")
#         floor = parts[1].replace("floor", "")
#         lab = parts[2].replace("lab", "")

#         # logic to fetch and display information based on URL path
#         floor_info = f"Floor Number: {floor}"
#         lab_info = f"Lab Number: {lab}"

#         return html.Div(
#             children=[
#                 html.P(floor_info),
#                 html.P(lab_info),
#             ],
#         )
#     return ""


# @app.callback(Output('output-selected', 'children'),
#               [Input('input', 'selected')])
# def _display_selected(selected):
#     return 'You have checked {}'.format(selected)

clientside_callback(
    """
    function(input) {
        console.log(input[0]);
        window.open(`/pages/dashboard${input[0]}`, "_self");
        return input[0];
    }
    """,
    Output('output-selected', 'children'),
    Input('input', 'selected'), prevent_initial_call=True
)


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


def query_to_list(point, server, start, end):
    master = fume_query(point, server, start, end)

    list = pd.Series(data=[i[0] for i in master],
                     index=[i[1] for i in master])
    print("\n", point, "\n", list)

    list = list[~list.index.duplicated()]
    print("\n", point, " new\n", list)

    return list


@ callback(
    Output("sash_graph", "figure"),
    Input("date_selector", "value")
)
def update_sash_graph(date):
    print("sash")

    # Arguments: Sash Point, Occ Point, Server Name, Start Time, End Time
    # Returns: Total time that hood sash was open when room is unoccupied, aggregated by hour
    def total_time_sash_open_unoccupied(sash_point, occ_point, server, start, end):
        sash_list = query_to_list(sash_point, server, start, end)
        occ_list = query_to_list(occ_point, server, start, end)

        df = pd.concat([sash_list, occ_list], axis=1)
        df.columns = ["sash", "occ"]

        time_interval = df.index[1].minute - df.index[0].minute

        # Figure out closed sash position
        # display(df["sash"].value_counts())

        # from running the above on a large time difference, 1.2 inches is the most common smallest value
        df["time_open_mins"] = np.where(
            (df["sash"] > 1.2) & (df["occ"] == 0), time_interval, 0)

        df = df.dropna()

        df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

        return df["time_open_mins"]

    sash_data = total_time_sash_open_unoccupied(sash_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash",
                                                occ_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                                                server="biotech_main",
                                                start=str(
                                                    datetime(2021, 11, 17, 1)),
                                                end=str(datetime(2021, 11, 17, 2)))
    print("sash_data")
    print(sash_data)

    sash_fig = px.bar(sash_data,
                      labels={
                          "value": "Time (min)",
                          "index": "Date and Time",
                          "variable": ""},
                      title="Time Sash Open When Unoccupied")

    return sash_fig


@ callback(
    Output("energy_graph", "figure"),
    Input("date_selector", "value")
)
def update_energy_graph(date):
    print("energy")

    def coldorhot(cfm, external, internal, time_interval):
        if external <= internal:
            # sensible heating equation
            return 1.08 * cfm * (internal - external) / (60 / time_interval)
        if external > internal:
            # enthalpy of air
            return 0.24 * cfm / 13.333 * 60 * (external - internal) / (60 / time_interval)

    def total_energy(cfm_point, sash_point, occ_point, internal_temp_point, external_temp_point, server, start, end):
        # external_temp_master = outside_temp(start,end)
        cfm_list = query_to_list(cfm_point, server, start, end)
        sash_list = query_to_list(sash_point, server, start, end)
        occ_list = query_to_list(occ_point, server, start, end)
        internal_temp_list = query_to_list(
            internal_temp_point, server, start, end)
        external_temp_list = query_to_list(
            external_temp_point, server, start, end)

        df = pd.concat([cfm_list, sash_list, occ_list,
                        internal_temp_list, external_temp_list], axis=1)
        df.columns = ["cfm", "sash", "occ", "internal_temp", "external_temp"]
        df["external_temp"] = df["external_temp"].interpolate()

        time_interval = df.index[1].minute - df.index[0].minute

        df['BTU'] = df.apply(lambda df: coldorhot(
            df['cfm'], df['external_temp'], df['internal_temp'], time_interval=time_interval), axis=1)

        df = df.groupby(pd.Grouper(freq='60Min', label='right')).sum()

        return df["BTU"]

    energy_data = total_energy(cfm_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hoodvalve_flow/trend_log",
                               sash_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/hood_sash",
                               occ_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/occ_trend",
                               internal_temp_point="#biotech/biotech_4th_floor/fourth_floor_fume_hood_lab_spaces/lab_433_control/zone/zone_temp/trend_log",
                               external_temp_point="#biotech/ground_flr_mech/building_hydronic_heating_syatems/reheat_heat_exchanger/oat",
                               server="biotech_main",
                               start=str(datetime(2021, 11, 17, 1)),
                               end=str(datetime(2021, 11, 17, 2)))
    print(energy_data)

    energy_fig = px.bar(energy_data,
                        labels={
                            "value": "Energy (BTU)",
                            "index": "Date and Time",
                            "variable": ""},
                        title="Total Fumehood Energy Consumption")

    return energy_fig


@ callback(
    Output("comparative_energyGraph", "figure"),
    Input("date_selector", "value")
)
def update_comparative_energyGraph(data):
    df = pd.DataFrame({
        "Floors": ["Olin 301", "Best Lab"],
        "Energy Used": [200, 125],
    })

    comparative_data = px.bar(df,
                              labels={"Energy": "Energy Used",
                                      "Floors": "Floor"},
                              x="Energy Used",
                              y="Floors",
                              orientation='h',
                              title="Average Energy Used (BTU/Hr)"
                              )
    return comparative_data


@ callback(
    Output("comparative_sashGraph", "figure"),
    Input("date_selector", "value")
)
def update_comparative_sashGraph(data):
    df = pd.DataFrame({
        "Floors": ["Olin 301", "Best Lab"],
        "Sash Position": [10, 5],
    })

    comparative_data = px.bar(df,
                              labels={"Sash Position": "Sash Position",
                                      "Floors": "Floor"},
                              x="Sash Position",
                              y="Floors",
                              orientation='h',
                              title="Average Sash Position (in)"
                              )
    return comparative_data

# if __name__ == '__main__':
#     app.run_server(debug=True)
