# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import requests
import json


app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Fume Hood Dashboard'),

    html.P("A (very basic, preliminary) web dashboard for Cornell Fume Hoods"),

    html.Div(id='output-selected'),

    dash_treeview_antd.TreeView(
        id='input',
        multiple=False,
        checkable=False,
        checked=['0-0-1'],
        selected=[],
        expanded=['0'],
        data={
            'title': 'Biotech',
            'key': '0',
            'children': [{
                'title': 'Floor 1',
                'key': '0-0',
                'children': [
                    {'title': 'Lab 1', 'key': '0-0-1'},
                    {'title': 'Lab 2', 'key': '0-0-2'},
                    {'title': 'Lab 3', 'key': '0-0-3'},
                ],
            }]}
    ),

])

@app.callback(Output('output-selected', 'children'),
              [Input('input', 'selected')])
def _display_selected(selected):
    return 'You have checked {}'.format(selected)



if __name__ == '__main__':
    app.run_server(debug=True)
