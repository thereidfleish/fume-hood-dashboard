import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone, timedelta
import requests
import numpy as np


#app = Dash(__name__)

dash.register_page(__name__)

def layout(building=None, **other_unknown_query_strings):
    return html.Div([
        # More content
        html.H1(f"Building {building} Page"),
        html.P(f"Showing Building {building} Page")
    ])