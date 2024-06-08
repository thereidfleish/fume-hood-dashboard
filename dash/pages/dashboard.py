import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, dash_table, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import boto3
from dotenv import load_dotenv

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
                    # Lab name
                    html.H1(' '.join(filter(None, (format_building(building), format_floor(floor), format_lab(lab))))),
                    html.H6('This week, the amount of time the fumehood was left open overnight is 1 hr and 3 mins'),

                    # Leaderboard and filter dropdown
                    dbc.Row(className="mb-3", children=[
                        dbc.Col(className="col-8", children=[
                            html.H2("Leaderboard")
                        ]),
                        dbc.Col(className="col-md-2", children=[
                            html.Label('Time Range Filter'),
                            dcc.Dropdown(["Day","Week", "Month", "Year"],
                                        "Week", clearable=False, id="date_selector")
                        ]),
                        dbc.Col(className="col-md-2", children=[
                            html.Label('Compare To'),
                            dcc.Dropdown([str(not bool(building) or building.capitalize()+" Floor "+floor), str(not bool(building) or building.capitalize()), "Campus"],
                                        floor, clearable=False, id="location_selector"),
                        ]),
                    ]),

                    dbc.Row(children=[
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
                                columnSize="sizeToFit",
                                dashGridOptions={"animateRows": False, 
                                                 'pinnedBottomRowData': (labs_df.loc[labs_df['lab'] == lab].head(1)).to_dict('records')},
                            )]
                        )),

                        dbc.Col(dcc.Loading(id="is-loading",children=[
                            dcc.Graph(id="ranking_graph",
                                    # eventually change these styles into a classname to put in css file
                                    style={
                                        'border-radius': '5px', 'background-color': '#f3f3f3', "margin-bottom": "10px"}
                                    # figure=fig
                                )],
                            type="circle"
                        ))
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
                dbc.Col([
                    dbc.Row(className="mb-3", children=[
                            dbc.Col([
                                html.H2("Visualizations")
                            ]),
                            dbc.Col([
                                html.Label('Time Range Filter'),
                                dcc.Dropdown(["Day","Week", "Month", "Year"],
                                            "Week", clearable=False, id="date_selector")
                            ]),
                    ]),

                    dcc.Loading(
                                id="is-loading",
                                children=[
                                    dcc.Graph(
                                        id="pie",
                                        style={'border-radius': '5px',
                                               'background-color': '#f3f3f3'}

                                        # figure=fig
                                    )],
                                type="circle"
                            )

                ]),

                    dbc.Row([
                        html.H3("Visualizations", className="mb-2"),
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
                                        id="sash_graph",
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

def synthetic_query(targets, server, start, end, aggType):
    targets_req = []

    for target in targets:
        data = {}
        data["payload"] = {}
        data["payload"]["schema"] = server
        data["payload"]["additional"] = [aggType, "sum"]
        data["target"] = target
        targets_req.append(data)

    url = "https://portal.emcs.cornell.edu/api/datasources/proxy/5/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": targets_req

    }
    response = requests.post(url, json=data)
    print(response)
    print(response.json())
    print(len(response.json()))

    master = pd.json_normalize(response.json(), record_path="datapoints", meta=["target", "metric"]).rename(columns={0: "value", 1: "timestamp"}).set_index("target").rename_axis(None)
    # Remove the rows where the metric is None (i.e., do not show the averaged rows because this is not useful)
    master = master[~master["metric"].isna()]
    master["timestamp"] = master["timestamp"].astype("datetime64[ms]").map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))

    master[["building", "floor", "lab", "hood"]] = [i[0:4] for i in master.index.str.split(".")]
    master[["floor", "lab", "hood"]] = master[["floor", "lab", "hood"]].replace(r'^.*?_', '', regex=True)
    
    # display(master)

    return master

@callback(
    Output("ranking_table", "rowData"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_ranking_table(date, url):
    print("====Getting q====")

    query = synthetic_query(targets=["Biotech.Floor_4.Lab_403.Hood_1.sashOpenTime.unocc", "Biotech.Floor_4.Lab_403b.Hood_1.sashOpenTime.unocc"], server="biotech_main",
                                    start=str(datetime(2024, 5, 15)),
                                    end=str(datetime.now()),
                                    aggType="aggD")
    
    print("EDEN", query)

    rankings = query.groupby([query.index, "building", "floor", "lab", "hood"], as_index=False).sum(numeric_only=True).sort_values(by="value")

    rankings["Ranking"] = np.arange(1, len(rankings) + 1)
    rankings['Ranking_Emoji'] = rankings['Ranking'].copy()
    rankings.loc[rankings['Ranking']==1, 'Ranking_Emoji'] = "🥇"
    rankings.loc[rankings['Ranking']==2, 'Ranking_Emoji'] = "🥈"
    rankings.loc[rankings['Ranking']==3, 'Ranking_Emoji'] = "🥉"

    print(rankings)

    return rankings.to_dict("records")

@callback(
    Output("ranking_graph", "figure"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_ranking_graph(date, url):
    
    ranking_graph = px.bar(labs_df, x=labs_df.index, y="day_sash_time", labels={
                            "TimeOpened": "Time Open when Unused",
                            "lab_name": "Lab",
                        },
                        title="Time Left Open Overnight"
    )
    return ranking_graph

@callback(
    Output("sash_graph", "figure"),
    Output("pie", "figure"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_sash_graph(date, url):
    # Obtain sash height and occupancy data
    parsed_url = urlparse(url).query
    target = f"{parse_qs(parsed_url)['building'][0].capitalize()}.Floor_{parse_qs(parsed_url)['floor'][0]}.Lab_{parse_qs(parsed_url)['lab'][0]}.Hood_1"
    print("Target: "+target)
    print("======Getting data for occ======")
    sash_data_occ = synthetic_query(target=target + ".sashOpenTime.occ",
                                    start=str(datetime(2023, 11, 20)),
                                    end=str(datetime(2023, 11, 30)))
    print("sash_data_occ: ")
    print(sash_data_occ)
    print("======Getting data for unocc======")
    sash_data_unocc = synthetic_query(target=target + ".sashOpenTime.unocc",
                                      start=str(datetime(2023, 11, 20)),
                                    end=str(datetime(2023, 11, 30)))
    print("sash_data_unocc: ")
    print(sash_data_unocc)
    final_df = pd.DataFrame(
        data={"occ": sash_data_occ, "unocc": sash_data_unocc})
    print("final_df at line 352: ")
    print(final_df)

    # Convert to long version
    final_df_long = pd.melt(final_df, value_vars = ["occ", "unocc"], 
                            ignore_index = False).sort_index().dropna()
    print("final_df_long at line 358: ")
    print(final_df_long)
    final_df_long_copy = final_df_long.copy()
    final_df_long_copy['time'] = final_df_long_copy.index
    print("final_df_long_copy at line 362: ")
    print(final_df_long_copy)

    # Generate unoccupied periods with sash opened
    final_df_long_copy['is_occ'] = (final_df_long['variable'] == 'occ')
    final_df_long_copy['is_occ_cumsum'] = final_df_long_copy['is_occ'].cumsum()
    unocc_period_groups = final_df_long_copy.\
            loc[(~final_df_long_copy['is_occ']) & (final_df_long_copy['value']>1.4)].\
                groupby('is_occ_cumsum')['time']
    unocc_periods = pd.DataFrame({"from":unocc_period_groups.max(),
                                  "to":unocc_period_groups.min()})


    # Create the line chart
    sash_fig = px.line(final_df_long_copy, x=final_df_long_copy.index, y="value", custom_data = ['variable'],
                        labels={
                            "value": "Sash Height (in)",
                            "index": "Date and Time",
                        },
                        title="When and how much is your fume hood sash open?")
    sash_fig.update_traces(line_color='black', 
                           hovertemplate='Occupany: %{customdata}<br><b>Sash Height: %{y}</b><extra></extra>')

    # Loop through each unoccupied period
    for _, row in unocc_periods.iterrows():
        # Add rectangle shape for visual highlighting
        sash_fig.add_shape(type="rect",
                            x0=row['from'], y0=0, x1=row['to'], y1=1,
                            xref="x", yref="paper",
                            fillcolor="red", opacity=0.2,
                            layer="below", line_width=0)

    # Preprocess to add a column in `final_df_long_copy` indicating whether each point is in an unoccupied period

    # Add an invisible scatter trace for detailed hover text
    sash_fig.add_trace(go.Scatter(
        x=final_df_long_copy.index,
        y=final_df_long_copy["value"]+1.2,
        mode='markers',
        marker=dict(color='rgba(0,0,0,0)'),
        hovertemplate='%{text}<extra></extra>',
        hoverlabel=dict(font=dict(color='red')),
        text=[ "Sash open when the room is unoccupied" if condition else "" for condition in ~final_df_long_copy['is_occ'] ],
        showlegend=False
    ))

    sash_fig.update_layout(
        hovermode='x',
        hoverlabel=dict(bgcolor='white'),
        margin=dict(t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    
    pie_df = final_df_long[final_df_long["variable"] == "unocc"]
    time_interval = pie_df.index[1].minute - pie_df.index[0].minute
    pie_df["minutes"] = time_interval
    pie_df["status"] = np.where((pie_df["value"] > 1.6), "Bad - Sash Open when Unoccupied", "Good - Sash Closed when Unoccupied")
    #print(pie_df)
    
    pie_fig = px.pie(pie_df, values="minutes", names="status", color="status",
                        labels={
                            "value": "Sash Height (in)",
                            "index": "Date and Time",
                            },
                        title="How often is your fume hood open when the room is unoccupied?",
                        color_discrete_map={'Good - Sash Closed when Unoccupied': 'mediumseagreen', 'Bad - Sash Open when Unoccupied': '#d62728'},
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
    Output("energy_graph", "figure"),
    Input("date_selector", "value"),
    Input('url', 'search')
)
def update_energy_graph(date, url):
    parsed_url = urlparse(url).query
    target = f"{parse_qs(parsed_url)['building'][0].capitalize()}.Floor_{parse_qs(parsed_url)['floor'][0]}.Lab_{parse_qs(parsed_url)['lab'][0]}.Hood_1"
    energy_data_occ = synthetic_query(target=target + ".energy.occ",
                                    start=str(datetime(2023, 11, 24)),
                                    end=str(datetime(2023, 11, 30)))

    energy_data_unocc = synthetic_query(target=target + ".energy.unocc",
                                      start=str(datetime(2023, 11, 24)),
                                    end=str(datetime(2023, 11, 30)))

    #print(energy_data_occ)
    #print(energy_data_unocc)

    final_df = pd.DataFrame(
        data={"occ": energy_data_occ, "unocc": energy_data_unocc})
    final_df = final_df.fillna(0)
    final_df.index = final_df.index.map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))

    final_df_long = pd.melt(final_df, value_vars = ["occ", "unocc"], ignore_index = False)

    #print(final_df_long)

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

def expanded_name(building=None, floor=None, lab=None):
    result = "?building="
    if building != None:
        result += building
        if floor != None:
            result += "&floor="+floor
            if lab != None:
                result += "&lab="+lab
    return result

# if __name__ == '__main__':
#     app.run_server(debug=True)
