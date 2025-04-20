import dash
from dash import html
import dash_bootstrap_components as dbc
import feffery_antd_components as fac
from .components.functions import cascaderview, expanded_name
from dash import html, dcc, Input, Output, callback, clientside_callback
import urllib.parse
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
    return html.Div([

        # dcc.Location(id='url'), 
        html.Div([
            html.H1("Cornell Fume Hood Dashboard", style={'textAlign': 'center'}),
            dbc.Row([  # Row for the cascader and button
                dbc.Col([  # Column containing both the cascader and the button
                    fac.AntdCascader(
                        id='building-cascader',
                        placeholder='Select a building, floor or lab',
                        options=cascaderview(list(labs_dict.keys())),
                        changeOnSelect=True,
                        popupContainer='parent',
                        popupClassName='cascaderPopup',
                        locale='en-us',
                        size='large',
                        style={'width': '70%', 'display': 'inline-block'},
                    ),
                    dbc.Button("Search", id="search-button", n_clicks=0, style={'margin-left': '10px'})
                ], width=12)
            ], justify="center", style={'margin-left': '20%','padding': '20px', 'display': 'flex', 'align-items': 'center'})
        ], style={'text-align': 'left'}),

        dbc.Row([  # Row for images
            dbc.Col(html.A(html.Img(src="/assets/campus.png", style={'width': '100%', 'height': 'auto'}), href="dashboard?building=campus"), md=1)
            # dbc.Col(html.Img(src="/assets/building.png", style={'width': '70%', 'height': 'auto'}), md=1),
            # dbc.Col(html.Img(src="/assets/floor.png", style={'width': '70%', 'height': 'auto'}), md=1),
            # dbc.Col(html.Img(src="/assets/lab.png", style={'width': '70%', 'height': 'auto'}), md=1)
        ], justify="center"),
        dbc.Row([  # Row for images
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/baker.png", style={'width': '90%', 'height': 'auto'}),
                href="dashboard?building=baker"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/bard.png", style={'width': '90%', 'height': 'auto'}),
                href="dashboard?building=bard"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/biotech.png", style={'width': '90%', 'height': 'auto'}),
                href="dashboard?building=biotech"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/olin.png", style={'width': '90%', 'height': 'auto'}),
                href="dashboard?building=olin"
            )]), md=1),
            dbc.Col(html.Div([html.A(
                html.Img(src="/assets/weill.png", style={'width': '90%', 'height': 'auto'}),
                href="dashboard?building=weill"
            )]), md=1)
    ], justify="center", style={'margin-top':'20px'})],
    style={'margin-top':'150px'})
    

@callback(
    Output('search-button', 'href'),
    Output('search-button', 'disabled'),
    Input('building-cascader', 'value')
)
def update_output(cascader_value):
    if cascader_value is None:
        return "", True
    return f"/dashboard{cascader_value[-1]}", False

