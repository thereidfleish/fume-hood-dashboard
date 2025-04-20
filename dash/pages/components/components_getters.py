from dash import html, dcc
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import feffery_antd_components as fac
import dash_svg as svg
from datetime import datetime, timedelta

from .functions import treeview, expanded_name, get_fumehood_text, get_level_text, format_building, format_floor, format_lab

def get_sidebar(building, floor, lab, labs_dict):
    return dbc.Col(
        fac.AntdSpace(
            [
                fac.AntdInput(
                    id='tree-search-keyword',
                    placeholder='Search for a building, floor or lab',
                    style={'width': '100%'},
                    mode='search',
                    allowClear=True,
                ),
                fac.AntdTree(
                    id='tree-search',
                    treeData=treeview(list(labs_dict.keys())),
                    defaultExpandAll=False,
                    caseSensitive=False,
                    defaultSelectedKeys=[expanded_name(building, floor, lab)],
                    defaultExpandedKeys=[expanded_name(building, floor, lab)],
                    highlightStyle={'background': '#ffffb8', 'padding': 0},
                ),
            ],
            direction='vertical',
            style={'width': '100%'},
        ),
        width=2
    )

def get_titles(building, floor, lab):
    title_text = ' '.join(
        filter(None, (format_building(building), format_floor(floor), format_lab(lab)))
    )
    return dbc.Col([
        html.H1(title_text),
        html.H6(
            f'The amount of time {get_fumehood_text(building, floor, lab)} was left closed overnight is 1 hr and 3 mins'
        ),
    ])

def get_date_selector():
    return dbc.Col(
        [
            html.Label('Time Range Filter'),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=datetime(2024, 1, 1),
                            max_date_allowed=datetime.now(),
                            initial_visible_month=datetime.now(),
                            start_date=datetime(2025, 1, 15) - timedelta(days=360),
                            end_date=datetime(2025, 1, 15),
                            clearable=False,
                            style={'font-size': '11px', 'width': '300px'},
                        )
                    ),
                    dbc.Col(html.Label('or'), width=1),
                    dbc.Col(
                        dcc.Dropdown(
                            id="date_selector",
                            options=[
                                {"label": "Past Day", "value": "day"},
                                {"label": "Past Week", "value": "week"},
                                {"label": "Past Month", "value": "month"},
                                {"label": "Past Year", "value": "year"},
                            ],
                            value="week",
                            clearable=False,
                        )
                    ),
                ],
                align="center",
            ),
        ]
    )

def get_live_fumehood_pane():
    return dbc.Col(
        className="card mx-1",
        children=[
            html.Div(
                children=[
                    html.Div(id="sashUpdateTimestamp"),
                    html.Div(
                        className="d-flex",
                        children=[
                            html.P("Fumehood"),
                            dcc.Dropdown(
                                options=[{'label': "Fumehood 1", 'value': "1"}],
                                value="1",
                                clearable=False,
                                id="fumehood_selector",
                                style={'minWidth': "200px"},
                            ),
                        ],
                    ),
                    html.P("🚨 Sash Open when Unoccupied NOW"),
                ]
            ),
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
                ], width="350", height="300"
            )
        ]
    )

def get_common_ranking_tabs(table_id, graph_id, columnDefs, graph_style=None):
    return dbc.Tabs(
        [
            dbc.Tab(
                dbc.Col(
                    dcc.Loading(
                        id="is-loading",
                        children=[
                            dag.AgGrid(
                                id=table_id,
                                columnDefs=columnDefs,
                                defaultColDef={
                                    "editable": False,
                                    "cellStyle": {"fontSize": "15px", "height": "50px"}
                                },
                                columnSize="sizeToFit",
                                dashGridOptions={'tooltipMouseTrack': True, 'tooltipShowDelay': 0, 'tooltipHideDelay': 10000}
                            )
                        ]
                    )
                ),
                label="Table"
            ),
            dbc.Tab(
                dbc.Col(
                    dcc.Loading(
                        id="is-loading",
                        children=[
                            dcc.Graph(
                                id=graph_id,
                                style=graph_style if graph_style else {'border-radius': '5px',
                                    'background-color': '#f3f3f3',
                                    "margin-bottom": "10px", 'max-width': "500px"}
                            )
                        ]
                    )
                ),
                label="Graph"
            )
        ]
    )

def get_within_ranking_pane(building, floor, lab):
    columnDefs = [
        {"headerName": "Ranking", "field": "Ranking", "cellStyle": {"fontSize": "25px", "height": "50px"}},
        {"headerName": "Lab", "field": "lab"},
        {"headerName": "% Time Closed", "field": "percent_time_closed", "tooltipField": "time_closed_hrmin"},
        {"headerName": "Change", "field": "change_display_string"}
    ]
    
    return dbc.Col(
        className="card mx-1",
        children=[
            dcc.Loading(
                id="is-loading",
                children=[
                    get_common_ranking_tabs(
                        "within_ranking_table", "within_ranking_graph", columnDefs
                    )
                ]
            )
        ]
    )

def get_stats_pane(building, floor, lab):
    return dbc.Col(children=[
        dbc.Row(
            className="card mx-1 mb-3",
            children=[
                html.H4(
                    f"Total energy wasted by {get_fumehood_text(building, floor, lab)}",
                    className="section-title"
                ),
                dbc.Card(
                    [
                        html.Span("1000 kWh", className="metric-text")
                    ],
                    className="metric-card"
                )
            ]
        ),
        dbc.Row(
            className="card mx-1",
            children=[
                html.H4(
                    f"Energy wasted by {get_fumehood_text(building, floor, lab)} is equivalent to",
                    className="section-title"
                ),
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
                        html.Span("5 homes' energy", className="metric-text")
                    ],
                    className="metric-card energy-homes"
                ),
                dbc.Card(
                    [
                        html.Span("🏭", className="metric-emoji"),
                        html.Span("200kg CO₂ and xx trees absorb in a day", className="metric-text")
                    ],
                    className="metric-card energy-co2"
                ),
            ]
        )
    ])

def get_comparison_selector(building, floor, lab):
    return html.Div(
        className="d-flex align-items-center",
        children=[
            html.H5("Compare to labs in ", className="me-2 mb-2"),
            html.Div(
                children=[
                    dcc.Dropdown(
                        className="mb-2",
                        options=[
                            {'label': format_floor(floor), 'value': 'floor'},
                            {'label': format_building(building), 'value': 'building'},
                            {'label': "Campus", 'value': 'cornell'},
                        ],
                        value="building",
                        clearable=False,
                        id="location_selector",
                        style={"width": "200px"},
                    )
                ]
            ),
        ]
    )

def get_ranking_pane(building, floor, lab):
    if lab is None:
        columnDefs = [
            {"headerName": "Ranking", "field": "Ranking", "cellStyle": {"fontSize": "25px", "height": "50px"}},
            {"headerName": "Average % Time Closed", "field": "percent_time_closed", "tooltipField": "time_closed_hrmin"},
            {"headerName": "Change", "field": "change_display_string"}
        ]
        if floor is None:
            columnDefs.insert(1, {"headerName": "Building", "field": "building"})
        else:
            columnDefs.insert(1, {"headerName": "Floor", "field": "floor"})
    else:
        columnDefs = [
            {"headerName": "Ranking", "field": "Ranking", "cellStyle": {"fontSize": "25px", "height": "50px"}},
            {"headerName": "Lab", "field": "lab"},
            {"headerName": "% Time Closed", "field": "percent_time_closed", "tooltipField": "time_closed_hrmin"},
            {"headerName": "Change", "field": "change_display_string"}
        ]
    
    return dbc.Col(
        className="card mx-1",
        children=[
            dcc.Loading(
                id="is-loading",
                children=[
                    html.H4("Time closed over entire period"),
                    get_common_ranking_tabs("ranking_table", "ranking_graph", columnDefs)
                ]
            )
        ]
    )

def get_comparison_graph_pane(building, floor, lab):
    return dbc.Col(
        className="card mx-1",
        children=[
            dcc.Loading(
                id="is-loading",
                children=[
                    html.H4("Time closed per day"),
                    html.P("Daily Average:"),
                    html.Div(id='sash_graph_average'),
                    html.Div(id='sash_graph_average_change'),
                    dcc.Graph(
                        id="sash_graph",
                        style={'border-radius': '10px', 'background-color': '#f3f3f3'}
                    )
                ]
            )
        ]
    )