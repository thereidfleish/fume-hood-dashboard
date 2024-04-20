import pandas as pd
import numpy as np
import os

point_names_arr = np.array(pd.read_csv(
    "Lab_pointnames/olin_hall.csv"))[:, 2:5][2:]

rooms_df = pd.read_csv("Lab_pointnames/olin_rooms.csv")
rooms_df = rooms_df.drop_duplicates(subset=[rooms_df.columns[4]])
room_nums = np.array(rooms_df.iloc[:, 4].astype(
    str).replace(['Room', 'room'], '', regex=True))
column_names = ['Building', 'Hood', 'Lab', 'Floor', 'Server',
                'Flow Sensor', 'Sash', 'Hood Occupancy', 'Occupancy', 'Internal Temp']

# print(room_nums, "hi")
def process_rooms(room_nums, output_file):
    file_exists = os.path.isfile(output_file)

    if not file_exists:
        pd.DataFrame(columns=column_names).to_csv(output_file, index=False)

    for room in room_nums:
        room = room.strip()
        hood_num = 1
        another_hood = True
        output = []
        while another_hood:
            # hood_num += 1
            # building, hood, lab, floor, server, flow sensor, sash, hood occupancy, occupancy, internal temp
            room_info = [
                "olin",
                hood_num,
                room,
                str(room)[0],
                None,
                None,
                None,
                None,
                None,
                None,
            ]

            def vec_contains(x, y):
                # print(y)
                # if "359" in str(x) and "359" in str(y):
                #   print(x)
                return str(y) in str(x)

            vectorized_contains = np.vectorize(vec_contains)
            room_point_names = point_names_arr[
                vectorized_contains(point_names_arr[:, 2], str(room).lower() or str(room).upper())
            ]
            # print(room)
            if len(room_point_names) == 0:
                print(f"ROOM {room} FAILED")
                break

            hood_room_point_names = room_point_names[
                vectorized_contains(room_point_names[:, 2], "fh")
                | vectorized_contains(room_point_names[:, 2], "hood")
                | vectorized_contains(room_point_names[:, 2], "zone")
                | vectorized_contains(room_point_names[:, 2], "occ")
            ]

            flow_hood_room_point_names = hood_room_point_names[
                vectorized_contains(hood_room_point_names[:, 2], "flow")
            ]
            if len(flow_hood_room_point_names) == 0:
                flow_hood_room_point_names = room_point_names[
                    vectorized_contains(room_point_names[:, 2], "flow")
                ]

            sash_hood_room_point_names = hood_room_point_names[
                vectorized_contains(hood_room_point_names[:, 2], "sash")
            ]
            if len(sash_hood_room_point_names) == 0:
                sash_hood_room_point_names = room_point_names[
                    vectorized_contains(room_point_names[:, 2], "sash")
                ]

            occ_hood_room_point_names = hood_room_point_names[
                vectorized_contains(hood_room_point_names[:, 2], "occ")

            ]
            if len(occ_hood_room_point_names) == 0:
                occ_hood_room_point_names = room_point_names[
                    vectorized_contains(room_point_names[:, 2], "occ")
                ]

            temp_hood_room_point_names = hood_room_point_names[
                vectorized_contains(hood_room_point_names[:, 2], "temp")
            ]
            if len(temp_hood_room_point_names) == 0:
                temp_hood_room_point_names = room_point_names[
                    vectorized_contains(room_point_names[:, 2], "temp")
                ]

    ########################################################
            flow_boolean = True
            for i, val in enumerate(flow_hood_room_point_names):
                if "Hood flow" in val[0]:
                    room_info[5] = val[2]
                    flow_boolean = False
                    break

            if flow_boolean:
                print(f"FLOW FOR {room} HOOD {hood_num}")
                for i, val in enumerate(flow_hood_room_point_names):
                    if "Alarm" in val[0] or "alarm" in val[2] or "Minimum" in val[0] or "Supply" in val[0] or "Max" in val[0] or "Offset" in val[0] or "Exhaust" in val[0] or "SAV" in val[0] or "occ" in val[2]:
                        continue
                    print(i, f"{val[0]} | {val[2]}: ")
                print()

                inp = input()
                if inp != "":
                    room_info[5] = flow_hood_room_point_names[int(inp), 2]
                print()

            another_hood_inp = input(f"is there another hood for {room}")
            if another_hood_inp == "y":
                another_hood = True
            else:
                another_hood = False
            print()
    ######
            sash_boolean = True
            len_sash = len(sash_hood_room_point_names)
            sash_string = ""
            if sash_boolean:
                for i, val in enumerate(sash_hood_room_point_names):
                    if "Flow" in val[0] or "occ" in val[2]:
                        len_sash -= 1
                        continue
                    if "alarm" in val[2]:
                        len_sash -= 1
                        continue
                    # if "sash_pos" not in val[2]:
                    #     len_sash-=1
                    #     continue
                    if len_sash == 1:
                        room_info[6] = val[2]
                    else:
                        sash_string += f"{i}, {val[0]} | {val[2]}: \n"
                print()
                # print(sash_string)

                if len_sash > 1:
                    print(f"SASH FOR {room} HOOD {hood_num}")
                    print(sash_string)
                    # print(f"SASH FOR {room} HOOD {hood_num}")
                    inp = input()
                    if inp != "":
                        room_info[6] = sash_hood_room_point_names[int(inp), 2]
                    print()

    ######
                hood_occ_boolean = True
                for i, val in enumerate(occ_hood_room_point_names):
                    if "hood_sash" in val[2]:
                        room_info[7] = val[2]
                        hood_occ_boolean = False
                        break

                if hood_occ_boolean:
                    print(f"HOOD OCC FOR {room} HOOD {hood_num}")
                hood_occ_string = ""
                len_occ_hood = len(occ_hood_room_point_names)

                for i, val in enumerate(occ_hood_room_point_names):
                    if "Flow" in val[0] or "Decommission" in val[0] or "alarm" in val[2] or "sash" in val[2] or "Mode" in val[0] or "Setpoint" in val[0] or "Local" in val[0]:
                        len_occ_hood -= 1
                        continue
                    if len_occ_hood == 1:
                        room_info[7] = val[2]
                    else:
                        hood_occ_string += f"{i}, {val[0]} | {val[2]}: \n"
                if len_occ_hood > 1:
                    print(f"HOOD OCC FOR {room} HOOD {hood_num}")
                    print(hood_occ_string)
                    print()
                    inp = input()
                    if inp != "":
                        room_info[7] = occ_hood_room_point_names[int(inp), 2]
                    print()

                occ_boolean = True
                for i, val in enumerate(occ_hood_room_point_names):
                    if "occ_sensor" in val[2]:
                        room_info[8] = val[2]
                        occ_boolean = False
                        break

                if occ_boolean:
                    occ_string = ""
                    len_occ = len(occ_hood_room_point_names)

                    for i, val in enumerate(occ_hood_room_point_names):
                        if "Flow" in val[0] or "Decommission" in val[0] or "alarm" in val[2] or "sash" in val[2] or "Mode" in val[0]:
                            len_occ = len_occ - 1
                            continue
                        if len_occ == 1:
                            room_info[8] = val[2]
                        else:
                            occ_string += f"{i}, {val[0]} | {val[2]}: \n"
                            print(i, f"{val[0]} | {val[2]}: ")
                    if len_occ > 1:
                        print(f"OCC FOR {room} HOOD {hood_num}")
                        print(occ_string)
                        inp = input()
                        if inp != "":
                            room_info[8] = occ_hood_room_point_names[int(
                                inp), 2]
                        print()
    ###################
            len_temp = len(temp_hood_room_point_names)

            for i, val in enumerate(temp_hood_room_point_names):
                print(i, f"{val[0]} | {val[1]} | {val[2]}: ")

            if len_temp > 1:
                inp = input()
                if inp != "":
                    room_info[9] = temp_hood_room_point_names[int(inp), 2]
                print()
            else:
                room_info[9] = temp_hood_room_point_names[0, 2]
            output.append(room_info)
            hood_num += 1

        hood_num = 1
        output_df = pd.DataFrame(output, columns=column_names)
        output_df.to_csv(output_file, mode='a', header=False, index=False)


# output_file = "bard_point_names_sash_lol.csv"
# process_rooms(room_nums, output_file)
# output_df.to_csv("bard_point_names.csv")

if __name__ == "__main__":
    output_directory = "Lab_pointnames/Finished_pointnames"
    output_file = os.path.join(output_directory, "olin_point_names_basement.csv")
    process_rooms(room_nums, output_file)


# output_df = pd.DataFrame(np.array(output))
# output_df.columns = column_names
