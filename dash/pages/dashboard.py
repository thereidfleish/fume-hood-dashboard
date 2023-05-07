import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json

app = Dash(__name__)

dash.register_page(__name__)


def layout(building=None, floor=None, lab=None, **other_unknown_query_strings):
        return html.Div([
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
                    dbc.Row(className="mb-3", children=[
                        dbc.Col([
                            html.H1(
                                ', '.join(filter(None, (building, floor, lab))))
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
                                            html.H4("3rd Best 🥉",
                                                    className="card-title"),
                                            html.H6("On Biotech Floor 1"),
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
                                            html.H4("1st Best 🥇",
                                                    className="card-title"),
                                            html.H6("On Biotech Floor 1"),
                                            html.P(
                                                "For least avg. time open when unoccupied (9 min/hr)",
                                                className="card-text",
                                            )
                                        ]
                                    ),
                                ]),

                            html.H3(className="mt-3",
                                    children="Comparative Metrics"),

                            dbc.Col([
                                    dcc.Loading(
                                        id="is-loading",
                                        children=[
                                            dcc.Graph(
                                                id="comparative_energyGraph",
                                                style={'border-radius': '5px',
                                                       'background-color': '#f3f3f3'}
                                                # figure=fig
                                            )],
                                        type="circle"
                                    ),
                                    dbc.Row([
                                        html.P(
                                            "Biotech 202's energy usage is 35% higher than the most energy efficient lab on campus (Olin 303). ")
                                    ])
                                    ]),
                            dbc.Col([
                                dcc.Loading(
                                    id="is-loading",
                                    children=[
                                        dcc.Graph(
                                            id="comparative_sashGraph",
                                            style={'border-radius': '5px',
                                                   'background-color': '#f3f3f3'}
                                            # figure=fig
                                        )],
                                    type="circle"
                                ),
                                dbc.Row([html.P(
                                    "Biotech 202's sash position is 60% higher than the least open sash on campus (Baker B10).")
                                ])

                            ])
                        ]),
                        dbc.Col([
                            html.H3("Graphs"),
                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="energy_graph",
                                        # eventually change these styles into a classname to put in css file
                                        style={
                                            'border-radius': '5px', 'background-color': '#f3f3f3', "margin-bottom": "10px"}
                                        # figure=fig
                                    )],
                                type="circle"
                            ),

                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="sash_graph",
                                        style={'border-radius': '5px',
                                               'background-color': '#f3f3f3'}

                                        # figure=fig
                                    )],
                                type="circle"
                            )

                        ]),

                        dbc.Row([



                        ]),

                    ])

                ])

            ]),

            # Need this to do the page click callback for some reason!
            html.Div(id='output-selected')
        ])

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


def synthetic_query(target, start, end):
    url = "https://portal.emcs.cornell.edu/api/datasources/proxy/5/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": [
            {
                "target": target
            }
        ],

    }
    request = requests.post(url, json=data)
    print(request)
    # print(request.json())
    master = create_tuple(request)
    list = pd.Series(data=[i[0] for i in master],
                     index=[i[1] for i in master])

    list = list[~list.index.duplicated()]

    return list


@callback(
    Output("sash_graph", "figure"),
    Input("date_selector", "value")
)
def update_sash_graph(date):
    sash_data_occ = synthetic_query(target="Biotech.Floor_4.Lab_433.Hood_1.sashOpenTime.occ",
                                    start=str(datetime(2021, 11, 16)),
                                    end=str(datetime(2021, 11, 20)))

    sash_data_unocc = synthetic_query(target="Biotech.Floor_4.Lab_433.Hood_1.sashOpenTime.unocc",
                                      start=str(datetime(2021, 11, 16)),
                                      end=str(datetime(2021, 11, 20)))

    #print(sash_data_occ)
    #print(sash_data_unocc)

    final_df = pd.DataFrame(
        data={"occ": sash_data_occ, "unocc": sash_data_unocc})
    final_df = final_df.fillna(0)

    final_df.index.name = "time"

    print(final_df)

    final_df_long = pd.melt(final_df, value_vars = ["occ", "unocc"], ignore_index = False)

    print(final_df_long)

    sash_fig_2 = px.bar(final_df_long, x = final_df_long.index, y = "value", color = "variable",
                        color_discrete_map={'occ': 'mediumseagreen', 'unocc': '#d62728'}
    #                    ,hover_data = {"variable": True, "value": False}
                        )

    sash_fig_2.update_traces(hovertemplate=('The fume hood was open for %{value} minutes when %{variable}'))

    sash_fig = px.bar(final_df, y = ['occ', 'unocc'], 
                      labels={
                          "value": "Time (min)",
                          "index": "Date and Time",
                          "variable": ""},
                      title="Time Sash Open",
                      color_discrete_map={'occ': 'mediumseagreen', 'unocc': '#d62728'})
    
    sash_fig.update_traces(hovertemplate=('The fume hood was open for %{y} minutes when %{status}'))

    sash_fig.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    #return sash_fig
    return sash_fig_2


@callback(
    Output("energy_graph", "figure"),
    Input("date_selector", "value")
)
def update_energy_graph(date):
    # TODO

    print(energy_data_occ)
    print(energy_data_unocc)

    final_df = pd.DataFrame(
        data={"occ": energy_data_occ, "unocc": energy_data_unocc})
    final_df = final_df.fillna(0)

    energy_fig = px.bar(final_df,
                        labels={
                            "value": "Energy (BTU)",
                            "index": "Date and Time",
                            "variable": ""},
                        title="Total Fumehood Energy Consumption",
                        color_discrete_map={'occ': 'mediumseagreen', 'unocc': '#d62728'
                                            })

    energy_fig.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)")
    

    return energy_fig


@ callback(
    Output("comparative_energyGraph", "figure"),
    Input("date_selector", "value")
)
def update_comparative_energyGraph(data):
    df = pd.DataFrame({
        "Lab": ["Biotech 202", "Best Lab"],
        "Energy Used": [200, 125],
    })

    comparative_data_energy = px.bar(df,
                                     labels={"Energy": "Energy Used",
                                             "Lab": "Lab"},
                                     x="Energy Used",
                                     y="Lab",
                                     color="Lab",
                                     orientation='h',
                                     title="Average Energy Used (BTU/Hr)",
                                     color_discrete_sequence=[
                                         "#d62728", "mediumseagreen"],
                                     height=275
                                     )

    comparative_data_energy.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    return comparative_data_energy


@ callback(
    Output("comparative_sashGraph", "figure"),
    Input("date_selector", "value")
)
def update_comparative_sashGraph(data):
    df = pd.DataFrame({
        "Lab": ["Biotech 202", "Best Lab"],
        "Sash Position": [10, 5],
    })

    comparative_data_sash = px.bar(df,
                                   labels={"Sash Position": "Sash Position",
                                           "Lab": "Lab"},
                                   x="Sash Position",
                                   y="Lab",
                                   color="Lab",
                                   orientation='h',
                                   title="Average Sash Position (in)",
                                   color_discrete_sequence=[
                                       "#d62728", "mediumseagreen"],
                                   height=275
                                   )

    comparative_data_sash.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    return comparative_data_sash

# if __name__ == '__main__':
#     app.run_server(debug=True)
