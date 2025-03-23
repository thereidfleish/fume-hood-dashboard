import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import feffery_antd_components as fac
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone, timedelta
import requests
import numpy as np
from .components.functions import cascaderview, expanded_name

# Make a homepage of dashboard that gives an overview of the 
# project, source of data, and what each metric indicates. 

# app = Dash(__name__)
import boto3
from dotenv import load_dotenv
load_dotenv()
dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")

TABLE_NAME = "fumehoods"
labs_response = dynamodb_client.get_item(
    TableName=TABLE_NAME, Key={"id": {"S": "labs"}}
)

labs_dict = labs_response['Item']["map"]["M"]

# print(cascaderview(list(labs_dict.keys())))

dash.register_page(__name__, path='/')


def layout(building=None, floor=None, **other_unknown_query_strings):
    return html.Div([  # Switch to Div for better flow control
        html.Div([  # This div wraps the title and cascader for centralized styling
            html.H1("Cornell Fume Hood Dashboard", style={'textAlign': 'center'}),
            fac.AntdCascader(
                placeholder='Select a building, floor or lab',
                options=cascaderview(list(labs_dict.keys())),
                changeOnSelect=True,
                popupContainer='parent',
                popupClassName='cascaderPopup',
                locale='en-us',
                size='large',
                style={'width': '800px', 'display': 'block', 'margin': 'auto'}
            )
        ], style={
            'text-align': 'left',
            'padding': '20px'
        }),
        dbc.Row([  # Row for images
            dbc.Col(html.Img(src="/assets/campus.png", style={'width': '100%', 'height': 'auto'}), md=1)
            # dbc.Col(html.Img(src="/assets/building.png", style={'width': '70%', 'height': 'auto'}), md=1),
            # dbc.Col(html.Img(src="/assets/floor.png", style={'width': '70%', 'height': 'auto'}), md=1),
            # dbc.Col(html.Img(src="/assets/lab.png", style={'width': '70%', 'height': 'auto'}), md=1)
        ], justify="center"),
        dbc.Row([  # Row for images
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/baker.png", style={'width': '90%', 'height': 'auto'}),
                href="http://0.0.0.0:8055/dashboard?building="
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/bard.png", style={'width': '90%', 'height': 'auto'}),
                href="http://0.0.0.0:8055/dashboard?building=bard"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/biotech.png", style={'width': '90%', 'height': 'auto'}),
                href="http://0.0.0.0:8055/dashboard?building=biotech"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/olin.png", style={'width': '90%', 'height': 'auto'}),
                href="http://0.0.0.0:8055/dashboard?building=olin"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/weill.png", style={'width': '90%', 'height': 'auto'}),
                href="http://0.0.0.0:8055/dashboard?building=weill"
            )]), md=1)
    ], justify="center", style={'margin-top':'20px'})],
    style={'margin-top':'150px'})

