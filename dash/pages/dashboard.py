import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, dash_table, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_treeview_antd
import feffery_antd_components as fac
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
from dash import ctx

from .components.functions import synthetic_query, raw_query, format_time
from .components.components_getters import get_sidebar, get_titles, get_date_selector, get_live_fumehood_pane, get_stats_pane, get_comparison_selector, get_ranking_pane, get_comparison_graph_pane

# app = Dash(__name__, meta_tags=[
#         {"name": "viewport", "content": "width=device-width, initial-scale=1"},
#     ],)

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

def layout(building=None, floor=None, lab=None):
    sidebar = get_sidebar(building, floor, lab, labs_dict)
    titles = get_titles(building, floor, lab)
    date_selector = get_date_selector()
    stats_pane = get_stats_pane(building, floor, lab)
    ranking_pane = get_ranking_pane(building, floor, lab)
    comparison_graph_pane = get_comparison_graph_pane(building, floor, lab)
    
    header_row = dbc.Row(children=[titles, date_selector])

    if (lab is None) and (floor is None):
        overview = dbc.Row(className="mb-3", children=[html.H3("Overview"), stats_pane])
        comparisons = dbc.Row(
            [
                html.H3("Comparisons"),
                html.Div(
                    className="d-flex align-items-center",
                    children=[
                        html.H5("How does your building compare to other buildings on campus", className="me-2 mb-2")
                    ]
                ),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, overview, comparisons])
    elif lab is None:
        overview = dbc.Row(className="mb-3", children=[html.H3("Overview"), stats_pane])
        comparisons = dbc.Row(
            [
                html.H3("Comparisons"),
                html.Div(
                    className="d-flex align-items-center",
                    children=[html.H5(f"How does your floor compare to other floors in {building}", className="me-2 mb-2")]
                ),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, overview, comparisons])
    else:
        live_fumehood_pane = get_live_fumehood_pane()
        overview = dbc.Row(className="mb-3", children=[html.H3("Overview"), live_fumehood_pane, stats_pane])
        comparisons = dbc.Row(
            [
                html.H3("Comparisons"),
                get_comparison_selector(building, floor, lab),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, overview, comparisons])

    return html.Div(
        [
            dbc.Row(className="m-0", children=[sidebar, main_section]),
            
            html.Div(id='output-selected'),
            dcc.Location(id='url'),
        ]
    )

clientside_callback(
    """(value) => value""",
    Output('tree-search', 'searchKeyword'),
    Input('tree-search-keyword', 'value'),
)

clientside_callback(
    """
    function(selectedKeys) {
        if (selectedKeys && selectedKeys.length > 0) {
            var newUrl = `/dashboard${selectedKeys[0]}`;
            // Only redirect if the URL is different
            if (window.location.pathname + window.location.search !== newUrl) {
                window.location.href = newUrl;
            }
        }
        return "";
    }
    """,
    Output('output-selected', 'children'),
    Input('tree-search', 'selectedKeys'),
    prevent_initial_call=True
)

@callback(
    Output(component_id='date-picker-range', component_property='start_date'),
    Output(component_id='date-picker-range', component_property='end_date'),
    Input(component_id='date-picker-range', component_property='start_date'),
    Input(component_id='date-picker-range', component_property='end_date'),
    Input(component_id='date_selector', component_property='value')
)
def update_date_range(start_date, end_date, selected_range):
    trigger = ctx.triggered_id 
    if trigger == "date_selector" and selected_range:
        if selected_range == "day":
            start_date = datetime.now() - timedelta(days=1)
        elif selected_range == "week":
            start_date = datetime.now() - timedelta(weeks=1)
        elif selected_range == "month":
            start_date = datetime.now() - timedelta(weeks=4)
        elif selected_range == "year":
            start_date = datetime.now() - timedelta(weeks=52)
        end_date = datetime.now()
    return [start_date, end_date]

@callback(
    Output(component_id="ranking_table", component_property="rowData"),
    Output(component_id="ranking_table", component_property="dashGridOptions"),
    Output(component_id="ranking_table", component_property="getRowStyle"),
    Output(component_id="ranking_graph", component_property="figure"),
    # Output(component_id='ranking_table', component_property ='figure'),
    Input(component_id="date-picker-range", component_property="start_date"),
    Input(component_id="date-picker-range", component_property="end_date"),
    Input(component_id='date_selector', component_property="value"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')
)
def rankings(start_date, end_date, value, location, url):
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
    print(query)
    
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
    Input(component_id='date_selector', component_property="value"),
    Input(component_id="location_selector", component_property="value"),
    Input(component_id='url', component_property='search')
)
def individual(start_date, end_date, value, location, url):
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
        
    hood_count = int(list(lab_dict_inside['M']['hood_count'].values())[0])
    
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
