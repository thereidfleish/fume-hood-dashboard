from dash import Dash, html, dcc, Input, Output
import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json

app = Dash(__name__)

dash.register_page(__name__, path_template="/report/<report_id>")


def layout(report_id=None):
    return html.Div(
        f"The user requested report ID: {report_id}."
    )

if __name__ == '__main__':
    app.run_server(debug=True)