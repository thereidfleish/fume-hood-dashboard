import pandas as pd
from dateutil import tz
import requests
from requests.auth import HTTPBasicAuth
import html
import os
import json

### SYNTHETIC QUERY ###
def synthetic_query(targets, server, start, end, aggType):
    # print (targets)
    targets_req = []
    # print(targets)

    for target in targets:
        data = {}
        data["payload"] = {}
        data["payload"]["schema"] = server
        data["payload"]["additional"] = [aggType, "sum"]
        data["target"] = target
        targets_req.append(data)

    url = "https://portal.emcs.cornell.edu/api/datasources/proxy/5/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": targets_req

    }
    response = requests.post(url, json=data)
    print (response)
    # print(response)
    # if response.status_code != 200:
    #      raise Exception("BAD")
    # print(len(response.json()))

    master = pd.json_normalize(response.json(), record_path="datapoints", meta=["target", "metric"]).rename(columns={0: "value", 1: "timestamp"}).set_index("target").rename_axis(None)
    # Remove the rows where the metric is None (i.e., do not show the averaged rows because this is not useful)
    master = master[~master["metric"].isna()]
    master["timestamp"] = master["timestamp"].astype("datetime64[ms]").map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))

    master[["building", "floor", "lab", "hood"]] = [i[0:4] for i in master.index.str.split(".")]
    master[["floor", "lab", "hood"]] = master[["floor", "lab", "hood"]].replace(r'^.*?_', '', regex=True)
    
    # display(master)
    print (master)
    return master

### RAW QUERY ###
def raw_query(target, server, start, end, aggType):
    url = "https://ypsu0n34jc.execute-api.us-east-1.amazonaws.com/dev/query"
    data = {
        "range": {
            "from": start,
            "to": end,
        },
        "targets": [
        {
          "payload": {
            "schema": server,
            "additional": [
                    aggType,
                ]
          },
          "target": target
        }
      ],
    }
    response = requests.post(url, json=data)
    # print("Raw Query Response:", response)
    # print("Raw Query JSON:", response.json())
    # print(len(response.json()))

    master = pd.json_normalize(response.json(), record_path="datapoints", meta=["target"]).rename(columns={0: "value", 1: "timestamp"}).set_index("target").rename_axis(None)
    # Remove the rows where the metric is None (i.e., do not show the averaged rows because this is not useful)
    # master = master[~master["metric"].isna()]
    master["timestamp"] = master["timestamp"].astype("datetime64[ms]").map(lambda x: x.to_pydatetime().replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()))

    return master

### LIVE LAB STATUS ###
# Docs: https://bacapi.emcs.cornell.edu/docs
def live_lab_query(device_instance, object_identifier):
    url = f"https://bacapi.emcs.cornell.edu/{html.escape(device_instance)}/{html.escape(object_identifier)}"
    headers = {'accept': 'application/json'}
    auth = HTTPBasicAuth(os.environ.get("LIVE_LAB_STATUS_USERNAME"), os.environ.get("LIVE_LAB_STATUS_PW"))

    response = requests.get(url, headers=headers, auth=auth)

    print(response.status_code)
    print(response.json())
    return response.json()

### TREEVIEW ###
# deconstructs hood IDs into building, floor and lab. 
# stores all information in a dictionary with building keys and dictionary values.
# the inner dictionary has keys which correspond to floors, floor keys, labs, and lab keys. 
# the values of these keys are lists or nested lists.
def lab_dictionary(id_list):
    
    id_list_split = []
    for i in range(0, (len(id_list))):
        id_list_split.append(id_list[i].split("."))

    building_list = {}
    for i in range (0, len(id_list_split)):
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
                    floor_key_list.append(building_list[building]["building_key"] + "&" + id_list_split[i][1].lower().replace("_", "="))
        building_list[building]["floor_list"] = floor_list
        building_list[building]["floor_key_list"] = floor_key_list
        
        lab_list = []
        lab_key_list = []
        for i in range(len(floor_list)):
            lab_list.append([])
            lab_key_list.append([])
            for j in range(len(id_list_split)):
                current_floor = id_list_split[j][1].replace("_", " ")
                if floor_list[i] == current_floor:
                    lab_title = id_list_split[j][2].replace("_", " ")
                    # Only add if not already present
                    if lab_title not in lab_list[i]:
                        lab_list[i].append(lab_title)
                        lab_key_list[i].append(
                            floor_key_list[i] + "&" + id_list_split[j][2].lower().replace("_", "=")
                        )

        building_list[building]["lab_list"] = lab_list
        building_list[building]["lab_key_list"] = lab_key_list
        
    return(building_list)

# calls lab_dictionary() on hood IDs.
# creates valid JSON string for dashboard treeview.
def treeview(id_list):
    lab_dict = lab_dictionary(id_list)
    tree_data = []
    for building, b_data in lab_dict.items():
        building_node = {
            "title": building,
            "key": "?building="+building.lower(),
            "children": []
        }
        # Loop through each floor for this building
        for i, floor in enumerate(b_data.get("floor_list", [])):
            floor_title = f"{building} {floor}"
            floor_node = {
                "title": floor_title,
                "key": b_data["floor_key_list"][i].lower(),
                "children": []
            }
            # Loop through each lab on this floor
            for j, lab in enumerate(b_data["lab_list"][i]):
                lab_title = f"{building} {lab}"
                lab_node = {
                    "title": lab_title,
                    "key": b_data["lab_key_list"][i][j].lower()
                }
                floor_node["children"].append(lab_node)
            building_node["children"].append(floor_node)
        tree_data.append(building_node)
    return tree_data

def expanded_name(building=None, floor=None, lab=None):
    result = "?building="
    if building is not None:
        result += building
        if floor is not  None:
            result += "&floor="+floor
            if lab is not None:
                result += "&lab="+lab
    return result

def cascaderview(id_list):
    lab_dict = lab_dictionary(id_list)
    tree_data = []
    for building, b_data in lab_dict.items():
        # Create the building node (title remains the same)
        building_node = {
            "value": "?building="+building.lower(), 
            "label": building,
            "children": []
        }
        # Loop through each floor for this building
        for i, floor in enumerate(b_data.get("floor_list", [])):
            floor_title = f"{building} {floor}"
            floor_node = {
                "value": b_data["floor_key_list"][i].lower(),
                "label": floor_title,
                "children": []
            }
            # Loop through each lab on this floor
            for j, lab in enumerate(b_data["lab_list"][i]):
                lab_title = f"{building} {lab}"
                lab_node = {
                    "value": b_data["lab_key_list"][i][j].lower(),
                    "label": lab_title
                }
                floor_node["children"].append(lab_node)
            building_node["children"].append(floor_node)
        tree_data.append(building_node)
    return tree_data

def get_fumehood_text(building, floor, lab):
    if lab is not None:
        return "fumehood(s) in this lab"
    elif floor is not None:
        return "fumehoods on this floor"
    else:
        return "fumehoods in this building"
    
def get_level_text(building, floor, lab):
    if lab is not None:
        return "lab"
    elif floor is not None:
        return "floor"
    else:
        return "building"
    

def format_building(building):
    return "" if building is None else building.capitalize()


def format_floor(floor):
    return "" if floor is None else "Floor " + floor


def format_lab(lab):
    return "" if lab is None else "Lab " + lab

# Format `time_closed` to show in days, hours and minutes
def format_time(minutes):
    if minutes > 1440:  # More than 24 hours (1440 minutes)
        days = int(minutes // 1440)
        remaining_minutes = minutes % 1440
        hours = int(remaining_minutes // 60)
        minutes_left = int(remaining_minutes % 60)
        return f"{days}d {hours}h {minutes_left}m"
    elif minutes > 60:  # More than 60 minutes
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return f"{hours}h {remaining_minutes}m"
    else:  # 60 minutes or less
        return f"{int(minutes)}m"