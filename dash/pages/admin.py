import dash
from dash import html, Input, Output, callback, dash_table, State, MATCH, callback_context, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import boto3
from dotenv import load_dotenv
from dash import ctx
import dash_ag_grid as dag
import json
from .components import functions
from datetime import datetime

# import dash_mantine_components as dmc
# import dash_iconify

dash.register_page(__name__)

# Load the environment variables from the .env file
load_dotenv()

dynamodb_client = boto3.client('dynamodb', region_name="us-east-1")
dyn_resource = boto3.resource("dynamodb", region_name="us-east-1")
TABLE_NAME = "fumehoods"
table = dyn_resource.Table(TABLE_NAME)

# PARAMS:
# type (string): One of "buildings", "labs", or "hoods"
def generate_grid(type):
    res = dynamodb_client.get_item(
        TableName=TABLE_NAME, Key={"id": {"S": type}}
    )
    
    # print("<<<")
    # print(json.dumps(res, indent=4))
    # print(res)
    
    res_dict = res['Item']["map"]["M"]
    # print(json.dumps(res_dict, indent=4))
    
    res_df = pd.DataFrame.from_dict({(i, j): res_dict[i][j]
                                  for i in res_dict.keys()
                                  for j in res_dict[i].keys()},
                                 orient='index')
    
    res_df.index = res_df.index.droplevel(1)
    res_df.index.name = "id"
    
    def process_item(x):
        if "NULL" in x.keys():
            return None
        elif "L" in x: 
            return ", ".join([list(item.values())[0] for item in x["L"]])
        return list(x.values())[0]
    
    res_df = res_df.apply(lambda col: col.map(lambda x: process_item(x))).iloc[:, ::-1].reset_index()
    
    # print("<<<\n\n", res_df.to_dict('records', index=True))

    col_building = ["baker", "bard", "biotech", "olin", "weill"]

    column_defs = [
        {
            "headerName": col,
            "field": col,
            "editable": True,
            "sortable": True,
            "filter": True,
            "resizable": True,
            "wrapText": True if col == "lab_id" else False,
            "autoHeight": True if col == "lab_id" else False,
            "checkboxSelection": True if col == "id" else False,
            "cellEditor": "agSelectCellEditor" if col == "building" else "agTextCellEditor",
            "cellEditorParams": {
            "values": col_building if col == "building" else None} 
        } 
        for col in res_df.columns
    ]

        
    dash_grid_options = {
            "rowSelection": "multiple",
            "animateRows": True
        }
    
    if type == "hoods":
        dash_grid_options.update({
            "components": {'button': 'button'},
            "cellRendererData": {'id': {'type': 'test-button-output', 'index': type}}
        })
        
    
    return html.Div([
        dag.AgGrid(
            id={
                'type': 'db-grid',
                'index': type
            },
            columnDefs=column_defs,
            columnSize="responsiveSizeToFit",
            rowData=res_df.to_dict('records'),
            defaultColDef={
                "sortable": True,
                "filter": True,
                "editable": True,
                "resizable": True
            },
            dashGridOptions=dash_grid_options,
            style = {"height": '300px', "width": "100%"},
            className="ag-theme-alpine"
        ),
        html.Div(className="d-flex justify-content-between", children=[
            dbc.Button("Add Row", id={
                'type': 'add-row-grid',
                'index': type
            }, color="link", n_clicks=0),

            dbc.Button("Delete Selected Rows", id={
                'type': 'delete-row-grid',
                'index': type
            }, color="link", n_clicks=0),

            dbc.Button("Save Changes", id={
                'type': 'save-db-button-grid',
                'index': type
            }, color="primary", className="m-1", n_clicks=0),

            dbc.Button("Test Points", id={
                'type': 'test-points-button',
                'index': type
            }, color="primary", className="m-1", n_clicks=0) if type == "hoods" else None,
        ]),
        html.Div(id={'type': 'output-message', 'index': type, 'subtype': 'grid'}, style={'marginTop': '10px', 'color': 'green'}),
        html.Div(id={'type': 'test-button-output', 'index': type, 'subtype': 'grid'}, style={'marginTop': '10px', 'color': 'green'}),
    ])

# Update DynamoDB for AgGrid
def update_grid(type, data):
    # print(">>> update_grid() called")
    df = pd.DataFrame(data).set_index("id")

    # if "id" not in df.columns:
    #     raise ValueError("Each row must have an 'id' field to serve as a key.")

    # df = df.set_index("id")

    def process_value(value):
        if isinstance(value, str) and ", " in value:
            return [v.strip() for v in value.split(",")]
        return value

    processed_data = df.applymap(process_value).to_dict(orient="index")

    item = {
        "id": type,
        "map": processed_data
    }

    with table.batch_writer() as writer:
        writer.put_item(Item=item)


@callback(
    Output({'type': 'test-button-output', 'index': "hoods"}, 'children'),
    Input({'type': 'db-grid', 'index': "hoods"}, 'cellRendererData') 
)
def run_test(data):
    if data:
        return f"Button clicked in row: {json.dumps(data)}"
    return "No data received."


# @callback(
#     Output({'type': 'test-button-output', 'index': "hoods"}, 'children'),
#     Input({'type': 'test-button-output', 'index': "hoods"}, 'cellRendererData')
# )
# def run_test(data):
#     ctx = callback_context
#     if ctx.triggered or data:
#         return f"Button clicked in row: {json.dumps(data)}"
#     return "No data received."
        
@callback(
    Output({'type': 'output-message', 'index': MATCH, 'subtype': 'grid'}, 'children'),
    Input({'type': 'save-db-button-grid', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    prevent_initial_call=True
)
def save_aggrid_changes(n_clicks, data):
    if n_clicks > 0:
        try:
            update_grid(ctx.triggered_id["index"], data)
            return "Changes saved successfully!"
        except Exception as e:
            return f"Error updating database: {str(e)}"


def test_point(id, building, is_synthetic):
   if is_synthetic is True:
       try:
           functions.synthetic_query([id], building+"_main", str(datetime(2024, 10, 10)), str(datetime(2024, 10, 20)), "aggD")
           return "success"
       except Exception as e:
           return str(e)
   else:
       try:
           functions.raw_query([id], building+"_main", str(datetime(2024, 10, 10)), str(datetime(2024, 10, 20)), "aggD")
           return "success"
       except Exception as e:
           return str(e)

def test_all_points(arr_points):
  tested_points = []
  for point in arr_points:
      message = test_point(point["id"], point["building"], point["is_synthetic"])
      if (message == "success"):
          tempDict = {
              "id": point["id"], 
              "message": message
          }
          tested_points.append(tempDict)
      else:
          tempDict = {
              "id": point["id"], 
              "message": message
          }
          tested_points.append(tempDict)
  return tested_points

@callback(
   Output({'type': 'test-button-output', 'index': MATCH, 'subtype': 'grid'}, 'children'),
   Output({'type': 'download-csv', 'index': MATCH}, 'data'),
   Input({'type': 'test-points-button', 'index': MATCH}, 'n_clicks'),
   State({'type': 'db-grid', 'index': MATCH}, 'rowData'),
   State({'type': 'db-grid', 'index': MATCH}, 'selectedRows'),
   prevent_initial_call=True
)
def get_points(n_clicks, data, selected_rows):
    if n_clicks > 0:
       print("button clicked")
       points_to_test = []
       selected_points = []
       if selected_rows:
           for obj in selected_rows:
               base_id = obj["id"]
               building = obj["building"]
                # Synthetic version
               selected_points.append({
                    "id": base_id + ".sashOpenTime.unocc",
                    "building": building,
                    "is_synthetic": True
                })

                # Raw version
               selected_points.append({
                    "id": base_id,
                    "building": building,
                    "is_synthetic": False
               })
       else:
            for obj in data:
               base_id = obj["id"]
               building = obj["building"]
                # Synthetic version
               points_to_test.append({
                    "id": base_id + ".sashOpenTime.unocc",
                    "building": building,
                    "is_synthetic": True
                })

                # Raw version
               points_to_test.append({
                    "id": base_id,
                    "building": building,
                    "is_synthetic": False
               })
       if selected_points == []:
           results = test_all_points(points_to_test)
       else:
           results = test_all_points(selected_points)
       results_df = pd.DataFrame(results, columns=["id", "message"])
       return json.dumps(results), dcc.send_data_frame(results_df.to_csv, "test_results.csv")

@callback(
    Output({'type': 'db-table', 'index': MATCH}, 'data'),
    Input({'type': 'add-row-table', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-table', 'index': MATCH}, 'data'),
    State({'type': 'db-table', 'index': MATCH}, 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@callback(
    Output({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    Input({'type': 'add-row-grid', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    State({'type': 'db-grid', 'index': MATCH}, 'columnDefs'))
def add_row_grid(n_clicks, rows, columns):
    if rows is None:
        rows = []
    if n_clicks:
        new_row = {col['field']: '' for col in columns}
        rows.append(new_row)
    return rows

@callback(
    Output({'type': 'db-grid', 'index': MATCH}, 'deleteSelectedRows'),
    Input({'type': 'delete-row-grid', 'index': MATCH}, 'n_clicks')
    )
def delete_row_grid(_):
    return True


def layout(**other_unknown_query_strings):
    return html.Main(className="p-2", children=[
        html.H1("Admin Dashboard"),

        html.H3("Occupants"),
        generate_grid("occupants"),

        html.H3("Buildings"),
        generate_grid("buildings"),
        
        html.H3("Labs"),
        generate_grid("labs"),
        
        html.H3("Hoods"),
        generate_grid("hoods"),
        
        dcc.Download(id={'type': 'download-csv', 'index': 'hoods'})
    ])

