import dash
from dash import html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from urllib.parse import urlparse
from urllib.parse import parse_qs
import boto3
from dotenv import load_dotenv
from dash import ctx

from .components.functions import synthetic_query, raw_query, format_time, get_level_text, live_lab_query
from .components.components_getters import get_sidebar, get_titles, get_date_selector, get_live_fumehood_pane, get_stats_pane, get_comparison_selector, get_ranking_pane, get_comparison_graph_pane, get_within_ranking_pane

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

labs_df = labs_df.apply(lambda col: col.map(lambda x: list(x.values())[0]))



def layout(building=None, floor=None, lab=None):
    sidebar = get_sidebar(building, floor, lab, labs_dict)
    titles = get_titles(building, floor, lab)
    date_selector = get_date_selector()
    within_pane = get_within_ranking_pane(building, floor, lab)
    stats_pane = get_stats_pane(building, floor, lab)
    ranking_pane = get_ranking_pane(building, floor, lab)
    comparison_graph_pane = get_comparison_graph_pane(building, floor, lab)
    
    header_row = dbc.Row(children=[titles, date_selector])

    if (lab is None) and (floor is None):
        overview = dbc.Col(className="mb-3", children=[html.H3("Overview of your building"), stats_pane])
        within = dbc.Col(className="mb-3", children=[html.H3("Labs within your building"), within_pane])
        comparisons = dbc.Row(
            [
                html.H3("Your building compared to others"),
                dcc.Dropdown(
                    options=[{'label': 'Campus', 'value': 'cornell'}],
                    value='cornell',
                    id="location_selector",
                    style={"display": "none"},
                ),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, dbc.Row(className="mb-3", children=[overview, within]), comparisons])
    elif lab is None:
        overview = dbc.Col(className="mb-3", children=[html.H3("Overview of your floor"), stats_pane])
        within = dbc.Col(className="mb-3", children=[html.H3("Labs within your building"), within_pane])
        comparisons = dbc.Row(
            [
                html.H3("Your floor compared to others"),
                dcc.Dropdown(
                    options=[{'label': 'Campus', 'value': 'cornell'}],
                    value='cornell',
                    id="location_selector",
                    style={"display": "none"},
                ),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, dbc.Row(children=[overview, within]), comparisons])
    else:
        live = dbc.Col(className="mb-3", children=[html.H3("Live Status"), get_live_fumehood_pane()])
        within = dbc.Col(within_pane, style={'display': 'none'})
        overview = dbc.Col(className="mb-3", children=[html.H3("Overview of your lab"), stats_pane])
        comparisons = dbc.Row(
            [
                html.H3("Your lab compared to others"),
                get_comparison_selector(building, floor, lab),
                ranking_pane,
                comparison_graph_pane,
            ]
        )
        main_section = dbc.Col(className="m-2", children=[header_row, within, dbc.Row(children=[overview, live]), comparisons])

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
    Output("ranking_table", "rowData"),
    Output("ranking_table", "dashGridOptions"),
    Output("ranking_table", "getRowStyle"),
    Output("ranking_graph", "figure"),
    Output("within_ranking_table", "rowData"),
    Output("within_ranking_graph", "figure"),
    Output("sash_graph", "figure"),
    Output("sash_graph_average", "children"),
    Output("sash_graph_average_change", "children"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("date_selector", "value"),
    Input("location_selector", "value"),
    Input("url", "search")
)
def summary(start_date, end_date, value, location, url):
    # --- ----------------- ---
    # --- COMMON PROCESSING ---
    # --- ----------------- ---
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    week_prior_start_date = start_date - timedelta(weeks=1)
    date_diff_min = (end_date - start_date).total_seconds() // 60

    # Parse URL parameters
    params = parse_qs(urlparse(url).query)
    lab = params.get("lab", [None])[0]
    floor = params.get("floor", [None])[0]
    building = params.get("building", [None])[0]
    
    # Define labs_df_filtered early to avoid UnboundLocalError
    if location == "floor" and floor:
        labs_df_filtered = labs_df.filter(like=f"{building.capitalize()}.Floor_{floor}", axis=0)
    elif location == "building":
        labs_df_filtered = labs_df.filter(like=building.capitalize(), axis=0)
    else:
        labs_df_filtered = labs_df

    # --- -------- ---
    # --- RANKINGS ---
    # --- -------- ---

    # Query current and last-week ranking data
    targets_ranking = labs_df_filtered.index + ".Hood_1.sashOpenTime.unocc"
    query_ranking = synthetic_query(
        targets=targets_ranking, server="biotech_main",
        start=str(start_date), end=str(end_date), aggType="aggD"
    )
    last_week_query_ranking = synthetic_query(
        targets=targets_ranking, server="biotech_main",
        start=str(week_prior_start_date), end=str(start_date), aggType="aggD"
    )

    # Process ranking queries
    def process_query(q):
        # Reset index to include it as a grouping column
        q = q.reset_index()
        df = q.groupby(["index", "building", "floor", "lab", "hood"], as_index=False).sum(numeric_only=True)
        df['time_closed'] = (date_diff_min - df['value']).clip(lower=0)
        return df.rename(columns={'value': 'time_opened'})

    rankings_df = process_query(query_ranking)
    last_week_df = process_query(last_week_query_ranking)

    # Helper function to compute rankings and differences
    def compute_rankings(current_df, last_df, merging_keys):
        current_df = current_df.sort_values(by="time_closed", ascending=False)
        current_df["Ranking"] = current_df['time_closed'].rank(method='min', ascending=False).astype(int)
        last_df = last_df.sort_values(by="time_closed", ascending=False)
        last_df["Last_Week_Ranking"] = last_df['time_closed'].rank(method='min', ascending=False).astype(int)
        merged_df = current_df.merge(last_df[merging_keys + ["Last_Week_Ranking"]], on=merging_keys)
        merged_df['change'] = merged_df['Last_Week_Ranking'] - merged_df['Ranking']
        merged_df['change_display_string'] = merged_df['change'].apply(
            lambda x: f"↑{x}" if x > 0 else f"↓{abs(x)}" if x < 0 else "-"
        )
        merged_df["percent_time_closed"] = (merged_df['time_closed'] / date_diff_min * 100).round(0).astype(int).astype(str) + '%'
        merged_df['time_closed_hrmin'] = merged_df['time_closed'].apply(format_time)
        return merged_df

    # --- Within level ranking ---
    if lab is None:
        within_merging_keys = ['lab']
        within_rankings_df = compute_rankings(rankings_df.copy(), last_week_df.copy(), within_merging_keys)
        within_rankings_df = within_rankings_df.to_dict("records")
        # Create the ranking bar graph for within level
        within_ranking_graph = px.bar(
            within_rankings_df,
            x="lab",
            y="time_closed",
            labels={"time_closed": "Time Closed when Unused", "lab": "Lab"},
        )
    else:
        # Return empty data for the table and a blank figure.
        within_rankings_df = []  # hide table data
        within_ranking_graph = {"data": [], "layout": {}}

    # --- Same level ranking ---
    if lab is None:
        if floor is None:
            level, level_data, merging_keys = "building", building, ["building"]
        else:
            level, level_data, merging_keys = "floor", floor, ["building", "floor"]
        # Aggregate data to the required level
        rankings_df = rankings_df.groupby(merging_keys)[['time_opened', 'time_closed']].mean(numeric_only=True).reset_index()
        last_week_df = last_week_df.groupby(merging_keys)[['time_opened', 'time_closed']].mean(numeric_only=True).reset_index()
    else:
        level, level_data, merging_keys = "lab", lab, ["building", "floor", "lab", "hood"]

    rankings_df = compute_rankings(rankings_df, last_week_df, merging_keys)

    # Prepare grid options and row styling for the ranking table
    pinnedTopRowData = rankings_df.loc[rankings_df[level] == level_data].to_dict('records')
    dashGridOptions = {"animateRows": True, "pinnedTopRowData": pinnedTopRowData}
    getRowStyle = {
        "styleConditions": [
            {
                "condition": f"params.data.{level} == '{level_data}'",
                "style": {"backgroundColor": "blue", "color": "white", "opacity": 0.5},
            },
        ]
    }

    # Create the ranking bar graph for same level
    ranking_graph = px.bar(
        rankings_df,
        x=level,
        y="time_closed",
        labels={"time_closed": "Time Closed when Unused", level: level.capitalize()},
    )
    ranking_graph["data"][0]["marker"]["color"] = [
        "red" if c == lab else "blue" for c in ranking_graph["data"][0]["x"]
    ]

    # --- ---------- ---
    # --- SASH GRAPH ---
    # --- ---------- ---
    # Determine main query targets based on the page for sash graph
    if lab is not None:
        target = f"{building.capitalize()}.Floor_{floor}.Lab_{lab}.Hood_1.sashOpenTime.unocc"
        main_targets = [target]
    elif floor is not None:
        location_string = f"{building.capitalize()}.Floor_{floor}"
        main_targets = labs_df.filter(like=location_string, axis=0).index + ".Hood_1.sashOpenTime.unocc"
    elif building is not None:
        location_string = building.capitalize()
        main_targets = labs_df.filter(like=location_string, axis=0).index + ".Hood_1.sashOpenTime.unocc"
    else:
        main_targets = labs_df.index + ".Hood_1.sashOpenTime.unocc"

    # Query current sash graph data
    query_sash = synthetic_query(
        targets=main_targets, server="biotech_main",
        start=str(start_date), end=str(end_date), aggType="aggD"
    )
    query_sash['time_closed'] = (60 * 24 - query_sash['value']).clip(lower=0)
    query_sash = query_sash.rename(columns={'value': 'time_opened'})
    query_sash = query_sash.groupby("timestamp", as_index=False).mean(numeric_only=True)

    # Determine overall query targets for computing the comparison average
    if location == "floor" and floor is not None:
        overall_string = f"{building.capitalize()}.Floor_{floor}"
        overall_desc = f"all labs on {overall_string}"
        overall_targets = labs_df.filter(like=overall_string, axis=0).index + ".Hood_1.sashOpenTime.unocc"
    elif location == "building" and building is not None:
        overall_string = building.capitalize()
        overall_desc = f"all labs in {overall_string}"
        overall_targets = labs_df.filter(like=overall_string, axis=0).index + ".Hood_1.sashOpenTime.unocc"
    else:
        overall_desc = "all labs on campus"
        overall_targets = labs_df.index + ".Hood_1.sashOpenTime.unocc"

    overall_query = synthetic_query(
        targets=overall_targets, server="biotech_main",
        start=str(week_prior_start_date), end=str(start_date), aggType="aggD"
    )
    overall_query['time_closed'] = (60 * 24 - overall_query['value']).clip(lower=0)
    comparison_average = overall_query['time_closed'].mean()

    # Compute conditional coloring for the sash graph
    query_sash['above_average'] = query_sash['time_closed'] > comparison_average
    query_sash['above_average_label'] = np.where(query_sash['above_average'], 'Above Average', 'Below Average')

    # Create the sash graph with colored bars
    sash_fig = px.bar(
        query_sash,
        x="timestamp",
        y="time_closed",
        labels={"time_closed": "Time closed (mins)", "timestamp": "Date"},
        color='above_average_label',
        color_discrete_map={'Above Average': 'mediumseagreen', 'Below Average': '#d62728'}
    )
    sash_fig.update_layout(
        legend_title_text="",
        plot_bgcolor="white",
        yaxis=dict(gridcolor="lightgrey")
    )
    sash_fig.add_hline(
        y=comparison_average,
        annotation_text=f"Last week average of {overall_desc}",
        annotation_position="bottom right",
        annotation=dict(
            font=dict(color="black", size=12),
            bgcolor="rgba(255, 255, 255, 0.7)"
        )
    )
    sash_fig.update_traces(
        hovertemplate="Date: %{x}<br>Time Closed: %{y} mins"
    )

    # Calculate average and percent change for the sash graph display
    current_average = query_sash['time_closed'].mean()
    sash_graph_average_string = f'{current_average:.0f} mins'
    if comparison_average > 0:
        change = ((current_average - comparison_average) / comparison_average) * 100
    else:
        change = 0
    if change > 0:
        sash_graph_average_change_string = f'↑ {change:.0f}% from last week'
    elif change == 0:
        sash_graph_average_change_string = 'No change from last week'
    else:
        sash_graph_average_change_string = f'↓ {-change:.0f}% from last week'

    return (rankings_df.to_dict("records"),
            dashGridOptions,
            getRowStyle,
            ranking_graph,
            within_rankings_df,
            within_ranking_graph,
            sash_fig,
            sash_graph_average_string,
            sash_graph_average_change_string)



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
    device_instance = "49317"
    object_identifier = "AI:4"
    result = live_lab_query(device_instance, object_identifier)
    sash_height = result['present-value']
    timestamp = pd.to_datetime(result['timestamp']).tz_localize(tz="America/New_York")

    
    minutes_from_update = round((now - timestamp).total_seconds() / 60)
    
    sash_complete_height = 18
    sash_height_pixel = (sash_complete_height - sash_height) / sash_complete_height * 200
    
    last_update_string = f"Last updated {format_time(minutes_from_update)} ago"
    
    fumehood_selector_options = []
    for i in range(1, hood_count+1):
        fumehood_selector_options.append({'label': f"Fumehood {i}", 'value': f"{i}"})
    
    sash_height_label = f"←{sash_height} inches opened"

    
    return sash_height_pixel, last_update_string, fumehood_selector_options, sash_height_label, sash_height_pixel+10

# if __name__ == '__main__':
#     app.run_server(debug=True)
