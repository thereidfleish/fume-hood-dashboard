import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, dash_table, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import dash_svg as svg
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from dateutil import tz
import requests
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import boto3
from dotenv import load_dotenv

from .components.functions import synthetic_query, treeview, expanded_name, raw_query

app = Dash(__name__)

dash.register_page(__name__)

# Load the environment variables from the .env file
load_dotenv()
dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")

TABLE_NAME = "fumehoods"

labs_response = dynamodb_client.get_item(
    TableName=TABLE_NAME, Key={"id": {"S": "labs"}}
)

labs_dict = labs_response['Item']["map"]["M"]

labs_df = pd.DataFrame.from_dict({(i, j): labs_dict[i][j]
                                  for i in labs_dict.keys()
                                  for j in labs_dict[i].keys()},
                                 orient='index')

labs_df.index = labs_df.index.droplevel(1)

labs_df = labs_df.applymap(lambda x: list(x.values())[0])


def format_building(building):
    return "" if building is None else building.capitalize()


def format_floor(floor):
    return "" if floor is None else "Floor " + floor


def format_lab(lab):
    return "" if lab is None else "Lab " + lab

# Format `time_closed` to show in days, hours and minutes
def format_time(minutes):
    if minutes > 1440:  # More than 24 hours (1440 minutes)
        days = int(minutes // 1440)
        remaining_minutes = minutes % 1440
        hours = int(remaining_minutes // 60)
        minutes_left = int(remaining_minutes % 60)
        return f"{days}d {hours}h {minutes_left}m"
    elif minutes > 60:  # More than 60 minutes
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours}h {remaining_minutes}m"
    else:  # 60 minutes or less
        return f"{int(minutes)}m"


def layout(building=None, floor=None, lab=None, **other_unknown_query_strings):

    # if lab == None:
    #     return html.Div([
    #         html.H3("Showing when no lab is selected"),
    #     ])
    # else:
    return html.Div([
        # dcc.Location(id='url', refresh=False),  # URL location component

        dbc.Row([
            # sidebar
            dbc.Col([
                dash_treeview_antd.TreeView(
                    id='input',
                    multiple=False,
                    checkable=False,
                    checked=[],
                    selected=[expanded_name(building, floor, lab)],
                    expanded=[expanded_name(building, floor, lab)],
                    data=json.loads(treeview(list(labs_dict.keys())))
                )
            ], width=3),

            # Main Section (Building and Date )
            dbc.Col([
                dbc.Row(children=[
                    

                    dbc.Col([
                        html.H1(' '.join(filter(None, (format_building(
                            building), format_floor(floor), format_lab(lab))))),
                        html.H6(
                            'This week, the amount of time the fumehood was left closed overnight is 1 hr and 3 mins'),
                    ]),
                    dbc.Col([
                        html.Label('Time Range Filter'),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=datetime(2024, 1, 1),
                            max_date_allowed=datetime.now(),
                            initial_visible_month=datetime.now(),
                            start_date=datetime(2024, 10, 15) - timedelta(days=7),
                            end_date=datetime(2024, 10, 15),
                            clearable=True,
                        ),
                        dcc.Dropdown(["Day", "Week", "Month", "Year"],
                                     "Week", clearable=False, id="date_selector")

                    ])
                ]),

                dbc.Row(children=[
                    html.H4("Live Fumehood Status"),

                ],),
                
                dbc.Row(children=[
                    # Nuo's Task

                        # Nuo's Task
                            dbc.Col([
                                html.Div(
                                     
                                    children=[
                                        html.Div(id="sashUpdateTimestamp"),
                                        html.Div(className="d-flex", children=[
                                            html.P("Fumehood"),                    
                                            dcc.Dropdown(options=[{'label': "Fumehood 1", 'value': "1"}], value="1", clearable=False, id="fumehood_selector", style={'minWidth': "200px"}),
                                        ]),
                                        html.P("🚨 Sash Open when Unoccupied NOW"),

                                    ]
                                ),
                                 dbc.Col(
                                svg.Svg(children=[
                                    svg.Rect(
                                        x="0", y="0", width=220, height=220, 
                                        className = "Sash",
                                        style={"fill": "#93939340", "stroke": "black", "stroke-width": 2}
                                    ),
                                    svg.Rect(
                                        x="10", y="10", width=200, height=200, 
                                        className = "entireSash",
                                        style={"fill": "#C4000080", "stroke": "black", "stroke-width": 2}
                                    ),
                                    svg.Path(
                                        d="M8.76763 1H13.4229M8.76763 1V5.22075C8.76763 5.57183 8.67522 7.00847 8.49968 7.31251L1.32141 21.4411C0.408196 23.0228 1.54971 25 3.37613 25H18.8143C20.6408 25 21.7823 23.0228 20.8691 21.4411L18.9254 17.6155M8.76763 1H8.17386M13.4229 1V5.22089C13.4229 5.57196 13.5153 7.00861 13.6909 7.31265L16.2306 12.3114M13.4229 1H14.0374M16.2306 12.3114H13.8169M16.2306 12.3114L17.578 14.9635M18.9254 17.6155H9.95454M18.9254 17.6155L17.578 14.9635M17.578 14.9635H12.4537", 
                                        fill="transparent",
                                        stroke="white",
                                        transform="translate(60, 180)",
                                        strokeWidth=1
                                    ),
                                    svg.Path(
                                        d="M4.05983 0.5C3.78369 0.5 3.55983 0.723858 3.55983 1C3.55983 1.27614 3.78369 1.5 4.05983 1.5V0.5ZM10.3818 1.5C10.6579 1.5 10.8818 1.27614 10.8818 1C10.8818 0.723858 10.6579 0.5 10.3818 0.5V1.5ZM13.6158 0.5C13.3396 0.5 13.1158 0.723858 13.1158 1C13.1158 1.27614 13.3396 1.5 13.6158 1.5V0.5ZM19.9377 1.5C20.2139 1.5 20.4377 1.27614 20.4377 1C20.4377 0.723858 20.2139 0.5 19.9377 0.5V1.5ZM23.1423 25.5C23.4184 25.5 23.6423 25.2761 23.6423 25C23.6423 24.7239 23.4184 24.5 23.1423 24.5V25.5ZM0.855469 24.5C0.579326 24.5 0.355469 24.7239 0.355469 25C0.355469 25.2761 0.579326 25.5 0.855469 25.5V24.5ZM0.855469 10.4627C0.579326 10.4627 0.355469 10.6865 0.355469 10.9627C0.355469 11.2388 0.579326 11.4627 0.855469 11.4627V10.4627ZM23.1423 11.4627C23.4184 11.4627 23.6423 11.2388 23.6423 10.9627C23.6423 10.6865 23.4184 10.4627 23.1423 10.4627V11.4627ZM20.8333 10.4627C20.5572 10.4627 20.3333 10.6865 20.3333 10.9627C20.3333 11.2388 20.5572 11.4627 20.8333 11.4627V10.4627ZM12.8321 11.4627C13.1082 11.4627 13.3321 11.2388 13.3321 10.9627C13.3321 10.6865 13.1082 10.4627 12.8321 10.4627V11.4627ZM11.1207 10.4627C10.8446 10.4627 10.6207 10.6865 10.6207 10.9627C10.6207 11.2388 10.8446 11.4627 11.1207 11.4627V10.4627ZM3.18615 11.4627C3.46229 11.4627 3.68615 11.2388 3.68615 10.9627C3.68615 10.6865 3.46229 10.4627 3.18615 10.4627V11.4627ZM4.05983 1.5H4.48787V0.5H4.05983V1.5ZM4.48787 1.5H9.95401V0.5H4.48787V1.5ZM9.95401 1.5H10.3818V0.5H9.95401V1.5ZM7.22094 22.7868C5.98765 22.7868 4.98787 21.787 4.98787 20.5537H3.98787C3.98787 22.3393 5.43536 23.7868 7.22094 23.7868V22.7868ZM9.45401 20.5537C9.45401 21.787 8.45423 22.7868 7.22094 22.7868V23.7868C9.00652 23.7868 10.454 22.3393 10.454 20.5537H9.45401ZM13.6158 1.5H14.0438V0.5H13.6158V1.5ZM14.0438 1.5H19.51V0.5H14.0438V1.5ZM19.51 1.5H19.9377V0.5H19.51V1.5ZM16.7769 22.7868C15.5436 22.7868 14.5438 21.787 14.5438 20.5537H13.5438C13.5438 22.3393 14.9913 23.7868 16.7769 23.7868V22.7868ZM19.01 20.5537C19.01 21.787 18.0102 22.7868 16.7769 22.7868V23.7868C18.5625 23.7868 20.01 22.3393 20.01 20.5537H19.01ZM9.45401 1V20.5537H10.454V1H9.45401ZM4.98787 20.5537V1H3.98787V20.5537H4.98787ZM19.01 1V20.5537H20.01V1H19.01ZM14.5438 20.5537V1H13.5438V20.5537H14.5438ZM21.5635 25.5H23.1423V24.5H21.5635V25.5ZM22.0635 25V10.9627H21.0635V25H22.0635ZM0.855469 25.5H2.5683V24.5H0.855469V25.5ZM2.5683 25.5H21.5635V24.5H2.5683V25.5ZM3.0683 25V10.9627H2.0683V25H3.0683ZM2.5683 10.4627H0.855469V11.4627H2.5683V10.4627ZM21.5635 11.4627H23.1423V10.4627H21.5635V11.4627ZM21.5635 10.4627H20.8333V11.4627H21.5635V10.4627ZM12.8321 10.4627H11.1207V11.4627H12.8321V10.4627ZM2.5683 11.4627H3.18615V10.4627H2.5683V11.4627Z",
                                        fill="transparent",
                                        stroke="white",
                                        transform="translate(135, 180)",
                                        strokeWidth=0.5
                                    ),
                                    svg.Rect(
                                        x="10", y="10", width=200,
                                        id = "closedSash",
                                        style={"fill": "#CBE1F1", "stroke": "black", "stroke-width": 2}
                                    ),
                                    svg.Text(
                                        x="230", 
                                        id="sashHeightLabel",
                                        style={"fill": "black", "fontSize": "12px"}
                                    ),
                                 ],
                                width="350", height="300", 
                                )), 
                    ],style={
                "maxHeight": "25rem",
                "padding": "1rem",
                "backgroundColor": "#fff",
                "borderRadius": "1rem",
                "boxShadow": "0px 4px 4px 0px rgba(0, 0, 0, 0.25)",
            },),

                    # Maggie's Task
                    dbc.Col([
                        html.H4("Energy wasted by this lab is equivalent to",
                                className="section-title"),
                        html.Div([
                            dbc.Card(
                                [
                                    html.Span("💰", className="metric-emoji"),
                                    html.Span("$100", className="metric-text")
                                ],
                                className="metric-card energy-cost"
                            ),
                            dbc.Card(
                                [
                                    html.Span("🏠", className="metric-emoji"),
                                    html.Span("5 homes' energy",
                                              className="metric-text")
                                ],
                                className="metric-card energy-homes"
                            ),
                            dbc.Card(
                                [
                                    html.Span("🏭", className="metric-emoji"),
                                    html.Span(
                                        "200kg CO₂ and xx trees absorb in a day", className="metric-text")
                                ],
                                className="metric-card energy-co2"
                            )
                        ], className="metric-container"),
                    ], style={
                        "maxHeight": "25rem",
                        "padding": "1rem",
                        "backgroundColor": "#fff",
                        "borderRadius": "1rem",
                        "boxShadow": "0px 4px 4px 0px rgba(0, 0, 0, 0.25)"
                    }, className="mb-4")]),
  

                # Visualization Section
                html.H2("Visualizations", className="me-3"),
                html.Div(className="d-flex align-items-center", children=[
                            html.H5("How does your lab compare to labs in ",
                                        className="me-2 mb-2"),
                            html.Div(style={'position': 'relative'}, children=[
                                dcc.Dropdown(
                                    options=[
                                        {'label': format_floor(floor), 'value': 'floor'},
                                        {'label': format_building(building), 'value': 'building'},
                                        {'label': "Campus", 'value': 'cornell'},
                                    ],
                                    value="building",
                                    clearable=False,
                                    id="location_selector",
                                    style={'minWidth': "200px", 'maxWidth': "200px"},
                                    className="mb-2"
                                )
                            ]),
                        ]),
                        
                dbc.Row([
                    dbc.Col([dcc.Loading(id="is-loading", children=[
                        dbc.Card([
                            html.Div(className="d-flex flex-wrap align-items-center", children=[
                                html.H4("What is the ranking of your lab?",
                                        className="me-2 mb-0", style={'whiteSpace': 'nowrap'}),
                            ]),
                            html.Br(),
                            dbc.Tabs([
                                dbc.Tab(
                                    dbc.Col(dcc.Loading(id="is-loading", children=[
                                        dag.AgGrid(
                                            id="ranking_table",
                                            columnDefs=[{"headerName": "Ranking", "field": "Ranking_Emoji", "cellStyle": {"fontSize": "25px", "height": "50px"}},
                                                        {"headerName": "Lab", "field": "lab"},
                                                        # {"headerName": "Fumehood", "field": "hood_name"},
                                                        {"headerName": "Time Closed", "field": "time_closed_hrmin"},
                                                        {"headerName": "Percent of Time Closed", "field": "percent_time_closed"},
                                                        {"headerName": "Change", "field": "change_display_string"}],
                                            defaultColDef={"editable": False,
                                                           'cellRendererSelector': {"function": "rowPinningTop(params)"},
                                                           "cellStyle": {"fontSize": "15px", "height": "50px"}},
                                            columnSize="sizeToFit"
                                        )
                                    ])),
                                    label="Table"
                                ),
                                dbc.Tab(
                                    dbc.Col(dcc.Loading(id="is-loading", children=[
                                        dcc.Graph(id="ranking_graph",
                                                # eventually change these styles into a classname to put in css file
                                                style={
                                                    'border-radius': '5px', 'background-color': '#f3f3f3', "margin-bottom": "10px"}
                                                )
                                    ], type="circle")),
                                    label="Graph"
                                )
                            ]),
                        ], style={
                        "height": "40rem",
                        "padding": "1rem",
                        "backgroundColor": "#fff",
                        "borderRadius": "1rem",
                        "boxShadow": "0px 4px 4px 0px rgba(0, 0, 0, 0.25)"
                        }
                        )
                    ])], width=6),

                    dbc.Col([dcc.Loading(id="is-loading", children=[
                        dbc.Card([
                            html.H4("When and how much is your fume hood sash closed?"),
                            html.P("Daily Average:"),
                            html.Div(id='sash_graph_average'),
                            html.Div(id='sash_graph_average_change'),
                            dcc.Graph(
                                id="sash_graph",
                                style={'border-radius': '10px',
                                       'background-color': '#f3f3f3'}

                                # figure=fig
                            )
                        ], style={
                        "height": "40rem",
                        "padding": "1rem",
                        "backgroundColor": "#fff",
                        "borderRadius": "1rem",
                        "boxShadow": "0px 4px 4px 0px rgba(0, 0, 0, 0.25)"
                        }
                        ),
                    ], type="circle")])
                ], className="mb-4"),
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
        if (input[0].includes("lab")) {
            window.open(`/dashboard${input[0]}`, "_self");
        }
        return input[0];
    }
    """,
    Output('output-selected', 'children'),
    Input('input', 'selected'), prevent_initial_call=True
)


@callback(
    Output(component_id="ranking_table", component_property="rowData"),
    Output(component_id="ranking_table", component_property="dashGridOptions"),
    Output(component_id="ranking_table", component_property="getRowStyle"),
    Output(component_id="ranking_graph", component_property="figure"),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')
)
def rankings(start_date, end_date, location, url):
    # print("====Getting Rankings====")

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    date_diff_min = ((end_date - start_date).total_seconds())//60
    week_prior_start_date = start_date - timedelta(weeks=1)

    url_query_params = parse_qs(urlparse(url).query)
    building = url_query_params["building"][0]
    floor = url_query_params["floor"][0]
    lab = url_query_params["lab"][0]

    if location == "floor":
        labs_df_filtered = labs_df.filter(
            like=building.capitalize() + "." + "Floor_" + floor, axis=0)
    elif location == "building":
        labs_df_filtered = labs_df.filter(like=building.capitalize(), axis=0)
    else:
        labs_df_filtered = labs_df

    query = synthetic_query(targets=labs_df_filtered.index + ".Hood_1.sashOpenTime.unocc", server="biotech_main",
                            start=str(start_date),
                            end=str(end_date),
                            aggType="aggD")
    
    last_week_query = synthetic_query(targets=labs_df_filtered.index + ".Hood_1.sashOpenTime.unocc", server="biotech_main",
                            start=str(week_prior_start_date),
                            end=str(start_date),
                            aggType="aggD")

    rankings = query.groupby([query.index, "building", "floor",
                             "lab", "hood"], as_index=False).sum(numeric_only=True)
    last_week_rankings = last_week_query.groupby([last_week_query.index, "building", "floor",
                             "lab", "hood"], as_index=False).sum(numeric_only=True)

    rankings['time_closed'] = (date_diff_min - rankings['value'])
    rankings.loc[rankings['time_closed'] < 0, 'time_closed'] = 0
    rankings = rankings.rename({'value': 'time_opened'}, axis=1)

    rankings = rankings.sort_values(by="time_closed", ascending=False)

    rankings["Ranking"] = rankings['time_closed'].rank(method='min', ascending=False).astype(int)
    rankings['Ranking_Emoji'] = rankings['Ranking'].copy()
    rankings.loc[rankings['Ranking']==1, 'Ranking_Emoji'] = "🥇"
    rankings.loc[rankings['Ranking']==2, 'Ranking_Emoji'] = "🥈"
    rankings.loc[rankings['Ranking']==3, 'Ranking_Emoji'] = "🥉"
    
    last_week_rankings['time_closed'] = (date_diff_min - last_week_rankings['value'])
    last_week_rankings.loc[last_week_rankings['time_closed'] < 0, 'time_closed'] = 0
    last_week_rankings = last_week_rankings.rename({'value': 'time_opened'}, axis=1)

    last_week_rankings = last_week_rankings.sort_values(by="time_closed", ascending=False)

    last_week_rankings["Last_Week_Ranking"] = last_week_rankings['time_closed'].rank(method='min', ascending=False).astype(int)
    
    rankings = rankings.merge(last_week_rankings[["building", "floor", "lab", "hood", "Last_Week_Ranking"]], on=["building", "floor", "lab", "hood"])

    rankings['change'] = rankings['Last_Week_Ranking'] - rankings['Ranking']

    rankings['change_display_string'] = rankings['change'].apply(lambda x: f"↑{x}" if x > 0 else f"↓{abs(x)}" if x < 0 else "-")


    rankings["percent_time_closed"] = (rankings['time_closed'] / date_diff_min * 100).round(0).astype(int).astype(str) + '%'

    rankings['time_closed_hrmin'] = rankings['time_closed'].apply(format_time)

    # Get the lab number from the query parameters
    dashGridOptions = {"animateRows": True, 'pinnedTopRowData': rankings.loc[rankings['lab'] == lab].to_dict('records')}

    getRowStyle = {"styleConditions": [
            {
                "condition": f"params.data.lab == {lab}",
                "style": {"backgroundColor": "blue", "color": "white", "opacity": 0.5},
            },
        ]
    }

    ranking_graph = px.bar(rankings, x="lab", y="time_closed", labels={
        "time_closed": "Time Closed when Unused",
        "lab": "Lab",
    },
        #title="Time Closed Overnight"
    )

    ranking_graph["data"][0]["marker"]["color"] = ["red" if c ==
                                                   lab else "blue" for c in ranking_graph["data"][0]["x"]]

    return rankings.to_dict("records"), dashGridOptions, getRowStyle, ranking_graph


@callback(
    Output(component_id="sash_graph", component_property="figure"),
    Output(component_id='sash_graph_average', component_property='children'),
    Output(component_id='sash_graph_average_change', component_property='children'),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')
)
def individual(start_date, end_date, location, url):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    week_prior_start_date = start_date - timedelta(weeks=1)
    date_diff_min = ((end_date - start_date).total_seconds())//60

    # print("====Getting Individual====")
    url_query_params = urlparse(url).query
    target = f"{parse_qs(url_query_params)['building'][0].capitalize()}.Floor_{parse_qs(url_query_params)['floor'][0]}.Lab_{parse_qs(url_query_params)['lab'][0]}.Hood_1.sashOpenTime.unocc"

    query = synthetic_query(targets=[target], server="biotech_main",
                            start=str(start_date),
                            end=str(end_date),
                            aggType="aggD")

    week_prior_query = synthetic_query(targets=[target], server="biotech_main",
                                       start=str(week_prior_start_date),
                                       end=str(start_date),
                                       aggType="aggD")
    
    url_query_params = parse_qs(urlparse(url).query)
    building = url_query_params["building"][0]
    floor = url_query_params["floor"][0]
    lab = url_query_params["lab"][0]
    
    if location == "floor":
        location_string = building.capitalize() + "." + "Floor_" + floor
        location_string_describe = f"on {location_string}"
        labs_df_filtered = labs_df.filter(like=location_string, axis=0)
    elif location == "building":
        location_string = building.capitalize()
        location_string_describe = f"in {location_string}"
        labs_df_filtered = labs_df.filter(like=location_string, axis=0)
    else:
        location_string = "Cornell"
        location_string_describe = f"at {location_string}"
        labs_df_filtered = labs_df

    all_query = synthetic_query(targets=labs_df_filtered.index + ".Hood_1.sashOpenTime.unocc", server="biotech_main",
                                    start=str(week_prior_start_date),
                                    end=str(start_date),
                                    aggType="aggD")

    query['time_closed'] = (60*24 - query['value'])
    query.loc[query['time_closed'] < 0, 'time_closed'] = 0
    query = query.rename({'value': 'time_opened'}, axis=1)

    week_prior_query['time_closed'] = (60*24 - week_prior_query['value'])
    week_prior_average = week_prior_query['time_closed'].mean()


    query['above_average'] = query['time_closed'] > week_prior_average
    query['above_average_label'] = np.where(query['above_average'], 'Above Average', 'Below Average')


    all_query['time_closed'] = (60*24 - all_query['value'])
    all_query.loc[all_query['time_closed'] < 0, 'time_closed'] = 0
    all_query = all_query.rename({'value':'time_opened'}, axis=1)

    average = all_query['time_closed'].mean()

    # Create the line chart
    sash_fig = px.bar(query, x="timestamp", y="time_closed",
                      labels={
                          "time_closed": "Time closed (mins)",
                          "timestamp": "Date",
                      },
                      color='above_average_label',
                      color_discrete_map={
                          'Above Average': 'mediumseagreen', 'Below Average': '#d62728'}
                      #title="When and how much is your fume hood sash closed?"
                      )
    
    sash_fig.update_layout(legend_title_text="",
                           plot_bgcolor="white",
                            yaxis=dict(gridcolor="lightgrey"
    ))

    sash_fig.add_hline(
    y=week_prior_average,
    annotation_text="Last week average of this lab",
    annotation_position="bottom right",
    annotation=dict(
        font=dict(
            color="black", 
            size=12   
        ),
        bgcolor="rgba(255, 255, 255, 0.7)"  
    ))

    sash_fig.add_hline(y=average,
                       annotation_text=f"Last week average of all labs {location_string_describe}",
                       annotation_position="bottom right",
                       annotation=dict(
        font=dict(
            color="black", 
            size=12   
        ),
        bgcolor="rgba(255, 255, 255, 0.7)"  
    ))
    
    sash_fig.update_traces(
        customdata = query['above_average_label'],
        hovertemplate="Date: %{x}<br>Time Closed: %{y} mins"
    )

    total_mins_unocc = query["time_opened"].sum()
    
    sash_graph_average = query["time_closed"].mean()
    sash_graph_average_string = f'{sash_graph_average:.0f} mins'
    
    if average > 0: 
        sash_graph_average_change = ((query["time_closed"].mean() - average) / average) * 100 
    else: 
        sash_graph_average_change = 0
    if sash_graph_average_change > 0:
        sash_graph_average_change_string = f'↑ {sash_graph_average_change:.0f}% from last week'
    elif sash_graph_average_change == 0:
        sash_graph_average_change_string = f'No change from last week'
    else:
        sash_graph_average_change_string = f'↓ {-sash_graph_average_change:.0f}% from last week'

    return sash_fig, sash_graph_average_string, sash_graph_average_change_string


@callback(
    Output(component_id="closedSash", component_property="height"),
    Output(component_id="sashUpdateTimestamp", component_property="children"),
    Output(component_id="fumehood_selector", component_property="options"),
    Output(component_id="sashHeightLabel", component_property="children"),
    Output(component_id="sashHeightLabel", component_property="y"),
    Input(component_id='url', component_property='search'),
    Input(component_id='fumehood_selector', component_property='value')
)
def ssh_height(url, hood):
    url_query_params_parse = parse_qs(urlparse(url).query)
    building = url_query_params_parse["building"][0]
    floor = url_query_params_parse["floor"][0]
    lab = url_query_params_parse["lab"][0]
    
    
    lab_full_string = f'{building.capitalize()}.Floor_{floor}.Lab_{lab}'
    
    lab_dict_inside = labs_dict[lab_full_string]
    hood_count = int(lab_dict_inside['M']['hood_count']['N'])
    
    hood_response = dynamodb_client.get_item(
        TableName=TABLE_NAME, Key={"id": {"S": "hoods"}}, ProjectionExpression="#map_alt.#hood", ExpressionAttributeNames={"#map_alt":"map", "#hood":f"{lab_full_string}.Hood_{hood}"}
    )

    hood_dict = hood_response['Item']["map"]["M"]
    
    hood_full_string = f'{lab_full_string}.Hood_{1}'
    
    hood_dict_inside = hood_dict[hood_full_string]
    hood_point_name = hood_dict_inside['M']['sash_position_sensor']['S']
    
    now = pd.Timestamp.now().tz_localize(tz="America/New_York")
    one_day_ago = now - timedelta(days=1)

    sash_query = raw_query(target=hood_point_name, server="biotech_main",
                        start=str(one_day_ago),
                        end=str(now),
                        aggType="aggD")
    
    last_sash_height = sash_query['value'].iloc[-1]
    last_timestamp = pd.to_datetime(sash_query['timestamp'].iloc[-1]).round('min')
    
    minutes_from_update = round((now - last_timestamp).total_seconds() / 60)
    
    sash_complete_height = 18
    sash_height_data = last_sash_height
    sash_height_pixel = (sash_complete_height - sash_height_data) / sash_complete_height * 200
    
    last_update_string = f"Last updated {format_time(minutes_from_update)} ago"
    
    fumehood_selector_options = []
    for i in range(1, hood_count+1):
        fumehood_selector_options.append({'label': f"Fumehood {i}", 'value': f"{i}"})
    
    sash_height_label = f"←{sash_height_data} inches opened"

    
    return sash_height_pixel, last_update_string, fumehood_selector_options, sash_height_label, sash_height_pixel+10

# if __name__ == '__main__':
#     app.run_server(debug=True)
