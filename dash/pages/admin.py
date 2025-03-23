import dash
from dash import html, Input, Output, callback, dash_table, State, MATCH
import dash_bootstrap_components as dbc
import pandas as pd
import boto3
from dotenv import load_dotenv
from dash import ctx
import dash_ag_grid as dag

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
    
    print("<<<")
    # print(json.dumps(res, indent=4))
    # print(res)
    
    res_dict = res['Item']["map"]["M"]
    # print(json.dumps(res_dict, indent=4))
    
    all_ids = [key + ".sashOpenTime.unocc" for key in res_dict.keys()]
    # print(all_ids)
    
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

    column_defs = [
        {
            "headerName": col,
            "field": col,
            "editable": True,
            "sortable": True,
            "filter": True,
            "resizable": True,
            "checkboxSelection": True if col == "id" else False
        } 
        for col in res_df.columns
    ]

    return html.Div([
        dag.AgGrid(
            id={
                'type': 'db-grid',
                'index': type
            },
            columnDefs=column_defs,
            columnSize="responsiveSizeToFit",
            rowData=res_df.to_dict('records'),
            # rowData = row_defs,
            defaultColDef={
                "sortable": True,
                "filter": True,
                "editable": True,
                "resizable": True
            },
            dashGridOptions={
                "rowSelection": "multiple",
                "animateRows": True,
                "domLayout": "autoHeight",
            },
            # style={'height': '400px', 'width': '100%'},
            style = {"height": None, "width": "100%"},
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
        ]),
        html.Div(id={'type': 'output-message', 'index': type, 'subtype': 'grid'}, style={'margin-top': '10px', 'color': 'green'}),
    ])


# PARAMS:
# type (string): One of "buildings", "labs", or "hoods"
def generate_table(type):
    res = dynamodb_client.get_item(
        TableName=TABLE_NAME, Key={"id": {"S": type}}
    )
    
    print("<<<")
    # print(json.dumps(res, indent=4))
    # print(res)
    
    res_dict = res['Item']["map"]["M"]
    # print(json.dumps(res_dict, indent=4))
    
    all_ids = [key + ".sashOpenTime.unocc" for key in res_dict.keys()]
    # print(all_ids)
    
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

    return html.Div([
        dash_table.DataTable(
            id={
                'type': 'db-table',
                'index': type
            },
            columns=[{'name': col, 'id': col, 'editable': True, "type": "text"} for col in res_df.columns],
            data=res_df.to_dict('records'),
            editable=True,
            row_deletable=True,
            # fixed_rows={'headers': True},
            sort_action='native',
            # style_header={"overflow": "hidden"},
            style_table={'overflowX': 'auto', 'maxHeight': '400px'},
            style_cell={'textAlign': 'left'},
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': '{{{}}} is blank'.format(col),
                        'column_id': col
                    },
                    'backgroundColor': 'tomato',
                    'color': 'white'
                } for col in res_df.columns
            ]
        ),
        html.Div(className="d-flex justify-content-between", children=[
                    dbc.Button("Add Row", id={
                        'type': 'add-row-table',
                        'index': type
                        }, color="link", n_clicks=0),
                    
                    dbc.Button("Save Changes", id={
                        'type': 'save-db-button-table',
                        'index': type
                    }, color="primary", className="m-1", n_clicks=0),
        ]),
        html.Div(id={'type': 'output-message', 'index': type, 'subtype': 'table'}, style={'margin-top': '10px', 'color': 'green'}),
    ])

# Update DynamoDB for Dash Table
def update_table(type, data):
    # print(">>> update_table() called")
    df = pd.DataFrame.from_dict(data).set_index("id")
    
    def process_value(value):
        if isinstance(value, str) and ", " in value:  
            return value.split(", ")  
        return value 
    
    processed_data = df.apply(lambda col: col.map(lambda x: process_value(x))).to_dict("index")

    item = {
        "id": type,
        "map": processed_data
    }

    with table.batch_writer() as writer:
        writer.put_item(Item=item)

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
    Output({'type': 'output-message', 'index': MATCH, 'subtype': 'table'}, 'children'),
    Input({'type': 'save-db-button-table', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-table', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)
def save_datatable_changes(n_clicks, data):
    if n_clicks:
        try:
            update_table(ctx.triggered_id["index"], data)
            return "Changes saved successfully!"
        except Exception as e:
            return f"Error updating database: {str(e)}"
        
@callback(
    Output({'type': 'output-message', 'index': MATCH, 'subtype': 'grid'}, 'children'),
    Input({'type': 'save-db-button-grid', 'index': MATCH}, 'n_clicks'),
    State({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    prevent_initial_call=True
)
def save_aggrid_changes(n_clicks, data):
    if n_clicks:
        try:
            update_grid(ctx.triggered_id["index"], data)
            return "Changes saved successfully!"
        except Exception as e:
            return f"Error updating database: {str(e)}"



# 1. Create callback similar to above that takes in a button push and the state of the table
# 2. Inside the callback, get the list of synthetic and point names
# - Example for synthetic names: all_ids = [object["id"] + ".sashOpenTime.unocc" for object in data]
# 3. Create a separate function that takes in an array of objects (see A below) of point/synthetic names and corresponding building names and whether it is a synthetic point
# # and returns an array of objects where each object has an id (point name/synthetic), the status (T/F), a message ("success" or "error") (see B below)
# 4. Create an inner function that actually tests each point that is called in a try/catch by the outer function above using a loop.  This inner function takes in three parameters — id, building, is_synthetic
# - determines the server of the building by querying the building table
# - call the synthetic_query or raw_query function in functions.py depending on whether its synthetic or not
# - throws an error if no data is returned or not a 200 status code or any other error in the original function

# A:
# [
#     {
#     "id": "#biotech/biotech_2nd_floor/second_floor_fume_hood_lab_spaces/lab_257_control/hood_sash",
#     "building": "biotech",
#     "is_synthetic": False
#     },
#     {
#     "id": "#3-40/fh_sash_pos",
#     "building": "weill",
#     "is_synthetic": False
#     }
# ]

# B:
# [
#     {
#     "id": "#biotech/biotech_2nd_floor/second_floor_fume_hood_lab_spaces/lab_257_control/hood_sash",
#     "status": True,
#     "message": "success"
#     },
#     {
#     "id": "#3-40/fh_sash_pos",
#     "status": False,
#     "message": {{error message from try/catch}}
#     }
# ]


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
    # Output({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    Output({'type': 'db-grid', 'index': MATCH}, 'deleteSelectedRows'),
    Input({'type': 'delete-row-grid', 'index': MATCH}, 'n_clicks')
    # State({'type': 'db-grid', 'index': MATCH}, 'rowData'),
    # State({'type': 'db-grid', 'index': MATCH}, 'selectedRows')
    )
def delete_row_grid(_):
    # if n_clicks > 0 and selected_rows:
    #     selected_ids = [row['id'] for row in selected_rows]
    #     updated_data = [row for row in rows if row['id'] not in selected_ids]
    #     try:
    #         update_grid(ctx.triggered_id['index'], updated_data) 
    #         return updated_data, "Selected rows deleted successfully!"
    #     except Exception as e:
    #         return rows, f"Error deleting rows: {str(e)}"
    # return rows
    return True


def layout(**other_unknown_query_strings):
    return html.Main(className="p-2", children=[
        
        html.H1("Admin Dashboard"),

        # html.H3("Occupants"),
        # generate_table("occupants"),

        # html.H3("Buildings"),
        # generate_table("buildings"),
        
        # html.H3("Labs"),
        # generate_table("labs"),
        
        # html.H3("Hoods"),
        # generate_table("hoods"),

        html.H3("Occupants"),
        generate_grid("occupants"),

        html.H3("Buildings"),
        generate_grid("buildings"),
        
        html.H3("Labs"),
        generate_grid("labs"),
        
        html.H3("Hoods"),
        generate_grid("hoods"),

    ])



