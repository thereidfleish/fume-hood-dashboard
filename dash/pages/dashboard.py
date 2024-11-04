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

                    
                
                    dbc.Row(children=[
                        # Nuo's Task
                            dbc.Col([
                                html.Div(
                                     
                                    children=[
                                        html.H4("Live Fumehood Status"),
                                        html.P("last updated 15 min ago"),
                                        html.P("🚨 Sash Open when Unoccupied NOW"),
                                    ]
                                ),

                            dbc.Col(
                                svg.Svg(children=[
                                    
                                    svg.Rect(
                                        x="10", y="10", width=200, height=200, 
                                        className = "entireSash",
                                        style={"fill": "#C4000080", "stroke": "black", "stroke-width": 2}
                                    ),
                                    svg.Path(
                                        d="M8.76763 1H13.4229M8.76763 1V5.22075C8.76763 5.57183 8.67522 7.00847 8.49968 7.31251L1.32141 21.4411C0.408196 23.0228 1.54971 25 3.37613 25H18.8143C20.6408 25 21.7823 23.0228 20.8691 21.4411L18.9254 17.6155M8.76763 1H8.17386M13.4229 1V5.22089C13.4229 5.57196 13.5153 7.00861 13.6909 7.31265L16.2306 12.3114M13.4229 1H14.0374M16.2306 12.3114H13.8169M16.2306 12.3114L17.578 14.9635M18.9254 17.6155H9.95454M18.9254 17.6155L17.578 14.9635M17.578 14.9635H12.4537", 
                                        fill="transparent",
                                        stroke="white",
                                        transform="translate(20, 180)",
                                        strokeWidth=1
                                    ),
                                    svg.Path(
                                        d="M4.05983 0.5C3.78369 0.5 3.55983 0.723858 3.55983 1C3.55983 1.27614 3.78369 1.5 4.05983 1.5V0.5ZM10.3818 1.5C10.6579 1.5 10.8818 1.27614 10.8818 1C10.8818 0.723858 10.6579 0.5 10.3818 0.5V1.5ZM13.6158 0.5C13.3396 0.5 13.1158 0.723858 13.1158 1C13.1158 1.27614 13.3396 1.5 13.6158 1.5V0.5ZM19.9377 1.5C20.2139 1.5 20.4377 1.27614 20.4377 1C20.4377 0.723858 20.2139 0.5 19.9377 0.5V1.5ZM23.1423 25.5C23.4184 25.5 23.6423 25.2761 23.6423 25C23.6423 24.7239 23.4184 24.5 23.1423 24.5V25.5ZM0.855469 24.5C0.579326 24.5 0.355469 24.7239 0.355469 25C0.355469 25.2761 0.579326 25.5 0.855469 25.5V24.5ZM0.855469 10.4627C0.579326 10.4627 0.355469 10.6865 0.355469 10.9627C0.355469 11.2388 0.579326 11.4627 0.855469 11.4627V10.4627ZM23.1423 11.4627C23.4184 11.4627 23.6423 11.2388 23.6423 10.9627C23.6423 10.6865 23.4184 10.4627 23.1423 10.4627V11.4627ZM20.8333 10.4627C20.5572 10.4627 20.3333 10.6865 20.3333 10.9627C20.3333 11.2388 20.5572 11.4627 20.8333 11.4627V10.4627ZM12.8321 11.4627C13.1082 11.4627 13.3321 11.2388 13.3321 10.9627C13.3321 10.6865 13.1082 10.4627 12.8321 10.4627V11.4627ZM11.1207 10.4627C10.8446 10.4627 10.6207 10.6865 10.6207 10.9627C10.6207 11.2388 10.8446 11.4627 11.1207 11.4627V10.4627ZM3.18615 11.4627C3.46229 11.4627 3.68615 11.2388 3.68615 10.9627C3.68615 10.6865 3.46229 10.4627 3.18615 10.4627V11.4627ZM4.05983 1.5H4.48787V0.5H4.05983V1.5ZM4.48787 1.5H9.95401V0.5H4.48787V1.5ZM9.95401 1.5H10.3818V0.5H9.95401V1.5ZM7.22094 22.7868C5.98765 22.7868 4.98787 21.787 4.98787 20.5537H3.98787C3.98787 22.3393 5.43536 23.7868 7.22094 23.7868V22.7868ZM9.45401 20.5537C9.45401 21.787 8.45423 22.7868 7.22094 22.7868V23.7868C9.00652 23.7868 10.454 22.3393 10.454 20.5537H9.45401ZM13.6158 1.5H14.0438V0.5H13.6158V1.5ZM14.0438 1.5H19.51V0.5H14.0438V1.5ZM19.51 1.5H19.9377V0.5H19.51V1.5ZM16.7769 22.7868C15.5436 22.7868 14.5438 21.787 14.5438 20.5537H13.5438C13.5438 22.3393 14.9913 23.7868 16.7769 23.7868V22.7868ZM19.01 20.5537C19.01 21.787 18.0102 22.7868 16.7769 22.7868V23.7868C18.5625 23.7868 20.01 22.3393 20.01 20.5537H19.01ZM9.45401 1V20.5537H10.454V1H9.45401ZM4.98787 20.5537V1H3.98787V20.5537H4.98787ZM19.01 1V20.5537H20.01V1H19.01ZM14.5438 20.5537V1H13.5438V20.5537H14.5438ZM21.5635 25.5H23.1423V24.5H21.5635V25.5ZM22.0635 25V10.9627H21.0635V25H22.0635ZM0.855469 25.5H2.5683V24.5H0.855469V25.5ZM2.5683 25.5H21.5635V24.5H2.5683V25.5ZM3.0683 25V10.9627H2.0683V25H3.0683ZM2.5683 10.4627H0.855469V11.4627H2.5683V10.4627ZM21.5635 11.4627H23.1423V10.4627H21.5635V11.4627ZM21.5635 10.4627H20.8333V11.4627H21.5635V10.4627ZM12.8321 10.4627H11.1207V11.4627H12.8321V10.4627ZM2.5683 11.4627H3.18615V10.4627H2.5683V11.4627Z",
                                        fill="transparent",
                                        stroke="white",
                                        transform="translate(60, 180)",
                                        strokeWidth=0.5
                                    ),
                                    svg.Rect(
                                        x="10", y="10", width=200,
                                        id = "closedSash",
                                        style={"fill": "#CBE1F1", "stroke": "black", "stroke-width": 2}
                                    ),
                                 ],
                                width="300", height="300"
                                )) 
                    ]),
                    
                        


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
                            html.Div(className="d-flex", children=[
                                html.H4("How does your lab compare to other labs", className="me-2"),                    
                                dcc.Dropdown(options=[
                                                {'label': "on this floor", 'value': 'floor'},
                                                {'label': "in " + format_building(building), 'value': 'building'},
                                                {'label': 'across campus', 'value': 'cornell'},
                                            ], value="building", clearable=False, id="location_selector", style={'minWidth': "200px"}),
                            ]),
                            dbc.Tabs([
                                dbc.Tab(
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
                                    )])), 
                                    label="Table"
                                ),
                                dbc.Tab(
                                    dbc.Col(dcc.Loading(id="is-loading",children=[
                                        dcc.Graph(id="ranking_graph",
                                                # eventually change these styles into a classname to put in css file
                                                style={
                                                    'border-radius': '5px', 'background-color': '#f3f3f3', "margin-bottom": "10px"}
                                                # figure=fig
                                            )
                                    ],
                                    type="circle"
                                    )), 
                                    label="Graph"
                                )
                            ])
                        ])),

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


@callback(
    Output("closedSash", "height"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')

)
def ssh_height (url, location):
    sash_complete_height = 30
    sash_height_data = 10
    return (sash_complete_height - sash_height_data) / sash_complete_height * 200

# if __name__ == '__main__':
#     app.run_server(debug=True)
