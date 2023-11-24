import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs

app = Dash(__name__)

dash.register_page(__name__)

def layout(building=None, floor=None, lab=None, **other_unknown_query_strings):
    
    # if lab == None:
    #     return html.Div([
    #         html.H3("Showing when no lab is selected"),
    #     ])
    # else:
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
                        data=json.loads(treeview(building_list))
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
            html.Div(id='output-selected'),
            dcc.Location(id='url')
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
    request = requests.post(url, json=data, verify=False)
    print(request)
    # print(request.json())
    master = create_tuple(request)
    list = pd.Series(data=[i[0] for i in master],
                     index=[i[1] for i in master])

    list = list[~list.index.duplicated()]

    return list


@callback(
    Output("sash_graph", "figure"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_sash_graph(date, url):
    parsed_url = urlparse(url).query
    target = f"{parse_qs(parsed_url)['building'][0].capitalize()}.Floor_{parse_qs(parsed_url)['floor'][0]}.Lab_{parse_qs(parsed_url)['lab'][0]}.Hood_1"
    sash_data_occ = synthetic_query(target=target + ".sashOpenTime.occ",
                                    start=str(datetime(2023, 1, 1)),
                                    end=str(datetime.now()))

    sash_data_unocc = synthetic_query(target=target + ".sashOpenTime.unocc",
                                      start=str(datetime(2023, 1, 1)),
                                    end=str(datetime.now()))

    print(sash_data_occ)
    print(sash_data_unocc)

    final_df = pd.DataFrame(
        data={"occ": sash_data_occ, "unocc": sash_data_unocc})
    final_df = final_df.fillna(0)
    final_df.index = final_df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))
    final_df_long = pd.melt(final_df, value_vars = ["occ", "unocc"], ignore_index = False)

    print(final_df_long)

    sash_fig = px.bar(final_df_long, x = final_df_long.index, y = "value", color = "variable",
                        labels={
                            "value": "Time (min)",
                            "index": "Date and Time",
                            "variable": ""},
                        title="Time Sash Open",
                        color_discrete_map={'occ': 'mediumseagreen', 'unocc': '#d62728'},
                        hover_data = {"variable": True, "value": False},
                        custom_data = ['variable']
                        )

    sash_fig.update_traces(hovertemplate=('The fume hood was open for %{value} minutes when %{customdata}'))

    sash_fig.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)")

    return sash_fig


@callback(
    Output("energy_graph", "figure"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_energy_graph(date, url):
    parsed_url = urlparse(url).query
    target = f"{parse_qs(parsed_url)['building'][0].capitalize()}.Floor_{parse_qs(parsed_url)['floor'][0]}.Lab_{parse_qs(parsed_url)['lab'][0]}.Hood_1"
    energy_data_occ = synthetic_query(target=target + ".energy.occ",
                                    start=str(datetime(2023, 1, 1)),
                                    end=str(datetime.now()))

    energy_data_unocc = synthetic_query(target=target + ".energy.unocc",
                                      start=str(datetime(2023, 1, 1)),
                                    end=str(datetime.now()))

    print(energy_data_occ)
    print(energy_data_unocc)

    final_df = pd.DataFrame(
        data={"occ": energy_data_occ, "unocc": energy_data_unocc})
    final_df = final_df.fillna(0)
    final_df.index = final_df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))

    final_df = pd.DataFrame(
        data={"occ": energy_data_occ, "unocc": energy_data_unocc})
    final_df = final_df.fillna(0)
    final_df.index = final_df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))
    final_df_long = pd.melt(final_df, value_vars = ["occ", "unocc"], ignore_index = False)

    print(final_df_long)

    energy_fig = px.bar(final_df_long, x = final_df_long.index, y = "value", color = "variable",
                        labels={
                            "value": "Energy (BTU)",
                            "index": "Date and Time",
                            "variable": ""},
                        title="Total Fumehood Energy Consumption",
                        color_discrete_map={'occ': 'mediumseagreen', 'unocc': '#d62728'},
                        hover_data = {"variable": True, "value": False},
                        custom_data = ['variable']
                        )
    
    energy_fig.update_traces(hovertemplate=('The fume hood used %{value} BTUs of energy when %{customdata}'))


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

building_list = ["Biotech.Floor_3.Lab_317.Hood_1", "Biotech.Floor_4.Lab_433.Hood_1", "Biotech.Floor_4.Lab_441.Hood_1",
                 "Olin.Floor_1.Lab_123.Hood_1", "Olin.Floor_1.Lab_127.Hood_1", "Olin.Floor_2.Lab_234.Hood_1",
                 "Baker.Floor_3.Lab_322.Hood_1"]

# deconstructs hood IDs into building, floor and lab. 
# stores all information in a dictionary with building keys and dictionary values.
# the inner dictionary has keys which correspond to floors, floor keys, labs, and lab keys. 
# the values of these keys are lists or nested lists.
def lab_dictionary(id_list):
    
    id_list_split = []
    for i in range(0, (len(id_list))):
        id_list_split.append(id_list[i].split("."))

    building_list = {}
    for i in range (0, len(id_list_split)):
            building = id_list_split[i][0]
            if (building not in building_list.keys()):
                building_key = "?building=" + building.lower()
                building_list[building] = {"building_key": building_key}

    for building in building_list:
        floor_list = []
        floor_key_list = []
        for i in range(0, len(id_list_split)):
            contains = False
            if building == id_list_split[i][0]:
                for j in range(0, len(floor_list)):
                    if floor_list[j] == id_list_split[i][1].replace("_", " "):
                        contains = True
                if contains == False:
                    floor_list.append(id_list_split[i][1].replace("_", " "))
                    floor_key_list.append(building_list[building]["building_key"] + "&" + id_list_split[i][1].lower().replace("_", "="))
        building_list[building]["floor_list"] = floor_list
        building_list[building]["floor_key_list"] = floor_key_list
        
        lab_list = []
        lab_key_list = []
        for i in range (0, len(floor_list)):
            lab_list.append([])
            lab_key_list.append([])
            for j in range(0, len(id_list_split)):
                if floor_list[i][-1] == id_list_split[j][1][-1]:
                    lab_list[i].append(id_list_split[j][2].replace("_", " "))
                    lab_key_list[i].append(floor_key_list[i] + "&" + id_list_split[j][2].lower().replace("_", "="))
        building_list[building]["lab_list"] = lab_list
        building_list[building]["lab_key_list"] = lab_key_list
        
    return(building_list)

# calls lab_dictionary() on hood IDs.
# creates valid JSON string for dashboard treeview.
def treeview(id_list):

    dict = lab_dictionary(id_list)

    # final_string = '['
    final_string = '{\n"title": "Buildings",\n"children": [\n\t'
    for building in dict:
        floor_list = dict[building]["floor_list"]
        floor_key_list = dict[building]["floor_key_list"]
        lab_list = dict[building]["lab_list"]
        lab_key_list = dict[building]["lab_key_list"]
        
        building_string = '{\n\t"title": "' + building + '",\n\t"key": "' + dict[building]["building_key"] + '",\n\t"children": [\n\t'
        for i in range (0, len(floor_list)): 
            floor_string = '\t{"title": "' + floor_list[i] + '",\n\t\t"key": "' + floor_key_list[i] + '",\n\t\t"children": [\n\t\t'
            for j in range (0, len(lab_list[i])):
                if j == (len(lab_list[i])-1):
                    lab_string = '\t{"title": "' + lab_list[i][j] + '",\n\t\t\t"key": "' + lab_key_list[i][j] + '"}\n\t\t'
                else:
                    lab_string = '\t{"title": "' + lab_list[i][j] + '",\n\t\t\t"key": "' + lab_key_list[i][j] + '"},\n\t\t'
                floor_string = floor_string + lab_string
            if i == (len(floor_list)-1):
                floor_string = floor_string + ']}]\n\t'
            else:
                floor_string = floor_string + ']},\n\t'
            building_string = building_string + floor_string
        final_string = final_string + building_string + '},'
    final_string = final_string[0:-1] + ']}'

    return(final_string)

# if __name__ == '__main__':
#     app.run_server(debug=True)
