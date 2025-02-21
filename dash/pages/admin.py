import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, dash_table, State, MATCH
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

from .components.functions import synthetic_query, treeview, expanded_name, raw_query

dash.register_page(__name__)

# Load the environment variables from the .env file
load_dotenv()

dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")
dyn_resource = boto3.resource("dynamodb", region_name="us-east-1")
TABLE_NAME = "fumehoods"
table = dyn_resource.Table(TABLE_NAME)


# PARAMS:
# type (string): One of "buildings", "labs", or "hoods"
def generate_table(type):
    res = dynamodb_client.get_item(
        TableName=TABLE_NAME, Key={"id": {"S": type}}
    )
    
    res_dict = res['Item']["map"]["M"]
    
    res_df = pd.DataFrame.from_dict({(i, j): res_dict[i][j]
                                  for i in res_dict.keys()
                                  for j in res_dict[i].keys()},
                                 orient='index')
    
    res_df.index = res_df.index.droplevel(1)
    
    res_df = res_df.applymap(lambda x: list(x.values())[0]).iloc[:, ::-1]
    
    print("<<<\n\n", res_df)

    return html.Div([
        dash_table.DataTable(
            id={
                'type': 'db-table',
                'index': type
            },
            columns=[{'name': col, 'id': col, 'editable': True} for col in res_df.columns],
            data=res_df.to_dict('records'),
            editable=True,
            row_deletable=True,
            # fixed_rows={'headers': True},
            sort_action='native',
            # style_header={"overflow": "hidden"},
            style_table={'overflowX': 'auto', 'maxHeight': '400px'},
        ),
        html.Div(className="d-flex justify-content-between", children=[
                    dbc.Button("Add Row", id={
                        'type': 'add-row-button',
                        'index': type
                        }, color="link", n_clicks=0),
                    
                    dbc.Button("Save Changes", id={
                        'type': 'save-db-button',
                        'index': type
                    }, color="primary", className="m-1", n_clicks=0),
        ])
    ])

# Update DynamoDB
def update_dynamodb(type, column_name, new_value):
    buildings = {
                "id": "buildings",
                "map": buildings_names_df.to_dict()
    }
    
    with table.batch_writer() as writer:
        writer.put_item(Item=get_buildings_dict())
#     dynamodb_client.update_item(
#         Key={'id': type},
#         UpdateExpression=f"SET {column_name} = :val",
#         ExpressionAttributeValues={':val': new_value}
# )
    
@callback(
Output({'type': 'output-message', 'index': MATCH}, 'children'),
Input({'type': 'save-db-button', 'index': MATCH}, 'n_clicks'),
State({'type': 'db-table', 'index': MATCH}, 'data'),
prevent_initial_call=True
)
def save_changes(data):
    try:
        update_dynamodb(data["index"], data)
        return "Changes saved successfully!"
    except Exception as e:
        return f"Error updating database: {str(e)}"

@callback(
    Output({'type': 'db-table', 'index': MATCH}, 'data'),
    Input({'type': 'add-row-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-table', 'index': MATCH}, 'data'),
    State({'type': 'db-table', 'index': MATCH}, 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows
    

def layout(**other_unknown_query_strings):
    return html.Main(className="p-2", children=[
        
        html.H1("Admin Dashboard"),
        
        html.Div(id='output-message', style={'margin-top': '10px', 'color': 'green'}),
        
        html.H3("Buildings"),
        generate_table("buildings"),
        
        html.H3("Labs"),
        generate_table("labs"),
        
        html.H3("Hoods"),
        generate_table("hoods"),

    ])


