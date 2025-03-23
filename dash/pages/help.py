import dash
from dash import html
import dash_bootstrap_components as dbc
from .components.functions import cascaderview
import feffery_antd_components as fac
import pandas as pd
import json
import boto3
from dotenv import load_dotenv
load_dotenv()
dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")
TABLE_NAME = "fumehoods"
labs_response = dynamodb_client.get_item(
    TableName=TABLE_NAME, Key={"id": {"S": "labs"}}
)
labs_dict = labs_response['Item']["map"]["M"]

dash.register_page(__name__, path='/help')

def layout(building=None, floor=None, **other_unknown_query_strings):
    return html.Div(children=[
        html.H3(f"Fume Hood Dashboard Overview"),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Fume Hood Energy Consumption",
                                    className="home-title"),
                            html.P(
                                "Fume hoods help limit exposure to hazardous chemicals by acting as a local ventilation " +
                                "system in laboratories. They are Cornell University’s single highest demanding laboratory " +
                                "equipment and when they are used, gaseous products from chemical reactions which occur " +
                                "underneath a fume hood are quickly ventilated out of the room and replaced by safe outside air. " +
                                "Energy is consumed via running the fan as well as re-heating outside air that is removed from " +
                                "the laboratory, and is correlated to sash position. Therefore, lowering the fume hood sash " +
                                "saves energy.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2"),
            ], className = "col d-flex w-100"),
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Diagram",
                                    className="home-title"),
                        ]
                    ),
                    dbc.CardImg(src="assets/fumehood.png", top = False, 
                                ),
                ], className="mb-2")
            ], className = "col-auto d-flex flex-shrink-1 w-50"),
        ], className = "d-flex flex-row"),
        dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Project Goals",
                                    className="home-title"),
                            html.P(
                                "Our primary aims are to promote sustainable usage of fume hoods in Cornell laboratories, " +
                                "as well as analyze fume hood energy usage on Cornell’s campus.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2"),
        
        html.H3(f"Metric Descriptions"),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Energy (BTUh)",
                                    className="home-title"),
                            html.P(
                                "Energy usage in British thermal units per hour where 1 BTUh is equivalent to 0.000293 kW. " +
                                "BTUh is calculated using air flow, indoor temperature, and outdoor temperature values.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2")
            ]),
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Time",
                                    className="home-title"),
                            html.P(
                                "The chosen time interval over which data will be displayed. In general, energy " +
                                "usage is higher in the winter and lower in the summer due to the relative differences " +
                                "between indoor and outdoor air temperature.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Sash Position (in)",
                                    className="home-title"),
                            html.P(
                                "The height of the fume hood’s sash ranges from 0 to 20 inches. Increased sash position " +
                                "leads to increased air flow, and thus higher energy consumption.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2")
            ]),
            dbc.Col([
                dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Occupancy (occ/unocc)",
                                    className="home-title"),
                            html.P(
                                "Whether the lab is occupied at a given time. Best practice is for fume hoods to be " +
                                "turned off or have their sashes closed while labs are unoccupied.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2")
            ])  
        ]),

        html.H3(f"Data Sources"),
        dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.P(
                                "This project is in partnership with the Campus Sustainability Office and Cornell University’s E&S IT Department. " + 
                                "Data is queried from WebCTRL, Cornell’s Building Management System.",
                                className="home-text",
                            )
                        ]
                    ),
                ], className="mb-2")
    ], style={'overflow': 'visible', 
                'position': 'absolute',
            })