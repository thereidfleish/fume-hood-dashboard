from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, State
from dash.dependencies import Input, Output, State
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json
import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import tz
import requests
import json

building_list = ["Biotech.Floor_3.Lab_317.Hood_1", "Biotech.Floor_4.Lab_433.Hood_1", "Biotech.Floor_4.Lab_441.Hood_1",
                 "Olin.Floor_1.Lab_123.Hood_1", "Olin.Floor_1.Lab_127.Hood_1", "Olin.Floor_2.Lab_234.Hood_1",
                 "Baker.Floor_3.Lab_322.Hood_1"]


def lab_dictionary(id_list):

    id_list_split = []
    for i in range(0, (len(id_list))):
        id_list_split.append(id_list[i].split("."))

    building_list = {}
    for i in range(0, len(id_list_split)):
        building = id_list_split[i][0]
        if (building not in building_list.keys()):
            building_key = "?building=" + building.lower()
            building_list[building] = {"building_key": building_key}

    for building in building_list:
        floor_list = []
        floor_key_list = []
        for i in range(0, len(id_list_split)):
            contains = False
            if building == id_list_split[i][0]:
                for j in range(0, len(floor_list)):
                    if floor_list[j] == id_list_split[i][1].replace("_", " "):
                        contains = True
                if contains == False:
                    floor_list.append(id_list_split[i][1].replace("_", " "))
                    floor_key_list.append(
                        building_list[building]["building_key"] + "&" + id_list_split[i][1].lower().replace("_", "="))
        building_list[building]["floor_list"] = floor_list
        building_list[building]["floor_key_list"] = floor_key_list

        lab_list = []
        lab_key_list = []
        for i in range(0, len(floor_list)):
            lab_list.append([])
            lab_key_list.append([])
            for j in range(0, len(id_list_split)):
                if floor_list[i][-1] == id_list_split[j][1][-1]:
                    lab_list[i].append(id_list_split[j][2].replace("_", " "))
                    lab_key_list[i].append(
                        floor_key_list[i] + "&" + id_list_split[j][2].lower().replace("_", "="))
        building_list[building]["lab_list"] = lab_list
        building_list[building]["lab_key_list"] = lab_key_list

    return (building_list)


# creates valid JSON string for dashboard treeview.
def treeview(id_list):

    dict = lab_dictionary(id_list)

    # final_string = '['
    final_string = '{\n"title": "Buildings",\n"children": [\n\t'
    for building in dict:
        floor_list = dict[building]["floor_list"]
        floor_key_list = dict[building]["floor_key_list"]
        lab_list = dict[building]["lab_list"]
        lab_key_list = dict[building]["lab_key_list"]

        building_string = '{\n\t"title": "' + building + '",\n\t"key": "' + \
            dict[building]["building_key"] + '",\n\t"children": [\n\t'
        for i in range(0, len(floor_list)):
            floor_string = '\t{"title": "' + \
                floor_list[i] + '",\n\t\t"key": "' + \
                floor_key_list[i] + '",\n\t\t"children": [\n\t\t'
            for j in range(0, len(lab_list[i])):
                if j == (len(lab_list[i])-1):
                    lab_string = '\t{"title": "' + lab_list[i][j] + \
                        '",\n\t\t\t"key": "' + lab_key_list[i][j] + '"}\n\t\t'
                else:
                    lab_string = '\t{"title": "' + lab_list[i][j] + \
                        '",\n\t\t\t"key": "' + lab_key_list[i][j] + '"},\n\t\t'
                floor_string = floor_string + lab_string
            if i == (len(floor_list)-1):
                floor_string = floor_string + ']}]\n\t'
            else:
                floor_string = floor_string + ']},\n\t'
            building_string = building_string + floor_string
        final_string = final_string + building_string + '},'
    final_string = final_string[0:-1] + ']}'

    return (final_string)


def tree(building_list):
    return html.Div([
        html.Img(src=dash.get_asset_url('logo.png')),
        # dbc.Button(
        #     html.Img(src=dash.get_asset_url('menu.png')),
        #     id="collapse-button",
        #     className="mb-3",
        #     color="",
        #     n_clicks=0,
        # ),
        dash_treeview_antd.TreeView(
            id='input',
            multiple=False,
            checkable=False,
            checked=[],
            selected=[],
            expanded=["?building=biotech"],
            data=json.loads(treeview(building_list))
        ),
    ])


collapse = html.Div(
    [
        dbc.Button(
            html.Img(src=dash.get_asset_url('menu.png')),
            id="collapse-button",
            className="mb-3",
            n_clicks=0,
        ),
        dbc.Collapse(
            tree(building_list),
            # dbc.Card(dbc.CardBody("This content is hidden in the collapse")),
            id="collapse",
            is_open=False,
        ),
    ]
)


@callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# app = dash.Dash(__name__)


# if __name__ == '__main__':
#     app.run_server(debug=True)
