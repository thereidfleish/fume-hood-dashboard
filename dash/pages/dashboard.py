import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, dash_table, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
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

from .components.functions import synthetic_query, treeview, expanded_name

app = Dash(__name__)

dash.register_page(__name__)

# Load the environment variables from the .env file
load_dotenv()
dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")

labs_response = dynamodb_client.get_item(
    TableName="fumehoods", Key={"id": {"S": "labs"}}
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
                    dbc.Row([
                         dbc.Col([
                              html.H1(' '.join(filter(None, (format_building(building), format_floor(floor), format_lab(lab))))),
                                html.H6('This week, the amount of time the fumehood was left open overnight is 1 hr and 3 mins'),
                         ]),
                         dbc.Col([
                            html.Label('Time Range Filter'),
                            dcc.DatePickerRange(
                                id='date-picker-range',
                                min_date_allowed=datetime(2024, 1, 1),
                                max_date_allowed=datetime.now(),
                                initial_visible_month=datetime.now(),
                                start_date=datetime.now() - timedelta(days=7),
                                end_date=datetime.now(),
                                clearable=True,
                            ),
                            dcc.Dropdown(["Day", "Week", "Month", "Year"], "Week", clearable=False, id="date_selector")

                         ])
                    ]),

                    html.Div(className="d-flex", children=[
                         html.H4("How does your lab compare to other labs", className="me-2"),                    
                    dcc.Dropdown(options=[
                                    {'label': "on this floor", 'value': 'floor'},
                                    {'label': "in " + building.capitalize(), 'value': 'building'},
                                    {'label': 'across campus', 'value': 'cornell'},
                                ], value="building", clearable=False, id="location_selector", style={'minWidth': "200px"}),
                    ]),
                    

                    dbc.Row(children=[
                        # Nuo's Task
                        dbc.Col(
                            html.H1("Nuo add here!")
                        ),

                        dbc.Col(dcc.Loading(id="is-loading",children=[
                            dag.AgGrid(
                                id="ranking_table",
                                columnDefs=[{"headerName": "Ranking", "field": "Ranking_Emoji", "cellStyle": {"fontSize": "25px", "height": "50px"}}, 
                                            {"headerName": "Lab", "field": "lab"}, 
                                            #{"headerName": "Fumehood", "field": "hood_name"}, 
                                            {"headerName": "Time Opened (min)", "field": "value"}],
                                defaultColDef={"editable": False, 
                                               'cellRendererSelector': {"function": "rowPinningBottom(params)"},
                                               "cellStyle": {"fontSize": "15px", "height": "50px"}},
                                columnSize="sizeToFit"
                            )]
                        )),

                        # Steven add carousel
                        dbc.Col(dcc.Loading(id="is-loading",children=[
                            dcc.Graph(id="ranking_graph",
                                    # eventually change these styles into a classname to put in css file
                                    style={
                                        'border-radius': '5px', 'background-color': '#f3f3f3', "margin-bottom": "10px"}
                                    # figure=fig
                                )],
                            type="circle"
                        )),

                        # Maggie's Task
                        dbc.Col(
                            html.H1("Maggie add here!")
                        )
                    ]),

                
                    dbc.Col([
                        # Leaderboard and filter dropdown
                        dbc.Row(className="mb-3", children=[
                            dbc.Col([
                                html.H2("Energy Stats")
                            ]),
                            dbc.Col(className="col-md-2", children=[
                                html.Label('Time Range Filter'),
                                dcc.Dropdown(["Day","Week", "Month", "Year"],
                                            "Week", clearable=False, id="date_selector")
                            ]),
                        ]),

                        dbc.Row([
                            dbc.Col([
                               
                                    html.H4(
                                        "Energy Wasted"
                                    ),
                                    dbc.Progress(label="25%", value=25),
                                    html.P("30,000 / 90,000 BTU")
                                
                            ]),
                            dbc.Col([
                               
                                    html.H4(
                                        "Time When Sash Open"
                                    ),
                                    dbc.Progress(label="30%", value=30),
                                    html.P("260 / 3600 minutes")
                                
                            ]),
                             dbc.Col([
                               
                                    html.H4(
                                        "Average Sash Height"
                                    ),
                                    dbc.Progress(label="55%", value=55),
                                    html.P("30 / 52 cm")
                                
                            ]),
                        ]),

                        # Comparative stats card
                        html.H4(
                                        "30% of this hood's energy was wasted on April 20th"
                                    ),
                        html.P(
                                        "This is equivalent to:"
                                    ),

                    dbc.Row([
                        dbc.Col ([
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4("💰 $100",
                                                    className="card-title mb-0"),
                                        ]
                                    ),
                                ]
                            ),
                        ]),
                            

                        dbc.Col ([
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4("🏠 5 homes",
                                                    className="card-title mb-0"),
                                        ]
                                    ),
                                ]
                            ),
                        ]),
                        
                        dbc.Col([
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4("🏭 200 kg CO2e",
                                                    className="card-title mb-0"),
                                        ]
                                    ),
                                ]
                            ),
                        ])
                            

                    ]),
                
                    ]),

                # Visualization Section
                html.H2("Visualizations"),
                dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="sash_graph",
                                        style={'border-radius': '10px',
                                               'background-color': '#f3f3f3'}

                                        # figure=fig
                                    )],
                                type="circle"
                ),
                    
                    dbc.Row([
                        dbc.Col([
                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="pie",
                                        style={'border-radius': '10px',
                                               'background-color': '#f3f3f3'}

                                        # figure=fig
                                    )],
                                type="circle"
                            )
                        ]),

                        dbc.Col([
                            dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="sash_graphs",
                                        style={'border-radius': '10px',
                                               'background-color': '#f3f3f3'}

                                        # figure=fig
                                    )],
                                type="circle"
                            ),
                        ]),
                        
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
    Output(component_id="ranking_graph", component_property="figure"),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')
)
def rankings(start_date, end_date, location, url):
    print("====Getting Rankings====")

    url_query_params = parse_qs(urlparse(url).query)
    building = url_query_params["building"][0]
    floor = url_query_params["floor"][0]
    lab = url_query_params["lab"][0]

    if location == "floor":
        labs_df_filtered = labs_df.filter(like=building.capitalize() + "." + "Floor_" + floor, axis=0)
    elif location == "building":
        labs_df_filtered = labs_df.filter(like=building.capitalize(), axis=0)
    else:
        labs_df_filtered = labs_df

    print(labs_df_filtered.index)

    query = synthetic_query(targets=labs_df_filtered.index + ".Hood_1.sashOpenTime.unocc", server="biotech_main",
                                    start=str(start_date),
                                    end=str(end_date),
                                    aggType="aggD")
    
    # print("Query:", query)

    rankings = query.groupby([query.index, "building", "floor", "lab", "hood"], as_index=False).sum(numeric_only=True).sort_values(by="value")

    rankings["Ranking"] = np.arange(1, len(rankings) + 1)
    rankings['Ranking_Emoji'] = rankings['Ranking'].copy()
    rankings.loc[rankings['Ranking']==1, 'Ranking_Emoji'] = "🥇"
    rankings.loc[rankings['Ranking']==2, 'Ranking_Emoji'] = "🥈"
    rankings.loc[rankings['Ranking']==3, 'Ranking_Emoji'] = "🥉"

    print(rankings)

    # Get the lab number from the query parameters
    dashGridOptions={"animateRows": True, 'pinnedBottomRowData': rankings.loc[rankings['lab'] == lab].to_dict('records')}

    ranking_graph = px.bar(rankings, x="lab", y="value", labels={
                            "value": "Time Open when Unused",
                            "lab": "Lab",
                        },
                        title="Time Left Open Overnight"
    )

    return rankings.to_dict("records"), dashGridOptions, ranking_graph

@callback(
    Output("sash_graph", "figure"),
    Output("pie", "figure"),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id='url', component_property='search')
)
def individual(start_date, end_date, url):
    print("====Getting Individual====")
    url_query_params = urlparse(url).query
    target = f"{parse_qs(url_query_params)['building'][0].capitalize()}.Floor_{parse_qs(url_query_params)['floor'][0]}.Lab_{parse_qs(url_query_params)['lab'][0]}.Hood_1.sashOpenTime.unocc"
    print("Target: "+target)

    query = synthetic_query(targets=[target], server="biotech_main",
                                    start=str(start_date),
                                    end=str(end_date),
                                    aggType="aggD")
    
    print("EDEN", query)

    # Create the line chart
    sash_fig = px.bar(query, x="timestamp", y="value",
                        labels={
                            "value": "Time open overnight (mins)",
                            "timestamp": "Date",
                        },
                        title="When and how much is your fume hood sash open?")
    
    print(datetime.fromisoformat(start_date))
    print(end_date)

    total_mins_unocc = query["value"].sum()
    total_mins_in_time_period = (datetime.fromisoformat(end_date)-datetime.fromisoformat(start_date)).total_seconds() / 60

    pie_df = pd.DataFrame([[total_mins_unocc, "Wasted"], [total_mins_in_time_period - total_mins_unocc, "Used"]], columns=["Mins", "Type"]) # time sash opened v.s. time sash unopened
    print(pie_df)
    
    pie_fig = px.pie(pie_df, values="Mins", names="Type", color="Type", 
                        title=str(round(total_mins_unocc/total_mins_in_time_period*100)).rstrip('0') + "% of your fume hood's energy was wasted when unused",
                        color_discrete_map={'Used': 'mediumseagreen', 'Wasted': '#d62728'},
                        # hover_data = {"occupancy": True, "value": False},
                        # custom_data = ['occupancy']
                        )

    pie_fig.update_layout(
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=-0.5
        )
    )

    return sash_fig, pie_fig

# if __name__ == '__main__':
#     app.run_server(debug=True)
