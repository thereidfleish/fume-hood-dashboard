# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ])

app.layout = html.Div([
    dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="..")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Buildings", header=True),
                dbc.DropdownMenuItem("Biotech", href="dashboard"),
                dbc.DropdownMenuItem("Baker", href="dashboard"),
            ],
            nav=True,
            in_navbar=True,
            label="Dashboard",
        ),
        dbc.NavItem(dbc.NavLink("About", href="404")),
        dbc.NavItem(dbc.NavLink("Help", href="404")),
        
    ],
    brand=html.Img(src="/assets/esw_logo.png", height="80px", width="auto"),
    brand_href="#",
    color="#B5E0BC",
    dark=False,
),

	html.H1('Cornell Fume Hood Dashboard'),

    html.Div(
        [
            html.Div(
                dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"], refresh=True)
                # html.A('Biotech', href='/biotech')
            )
            for page in dash.page_registry.values()
        ]
    ),

	dash.page_container
])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8055)