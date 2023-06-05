"""
Parameters = {"world_file", "movement_path", "video_name", "gz_pose_file", "vid_pose_file", "models", "lights"}

"""
import time

import pandas as pd
import numpy as np
from dataclasses import dataclass
import subprocess
import os

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters = {"world_file", "movement_path", "video_name", "gz_pose_file", "vid_pose_file", "models", "lights"}

@dataclass()
class pose:
    x: float
    y: float
    z: float
    r: float
    p: float
    y: float

@dataclass
class model:
    model_name: str
    pose: pose

@dataclass
class test_config_data:
    test_name: str
    world_file: str
    movement_path: str
    video_name: str
    gz_pose_file: str
    vid_pose_file: str
    models: model
    lights: []  # todo: Add lights data class

def ImportSheet(tests_config, filename):
    # Read the entire Excel Workbook
    xls = pd.ExcelFile(filename)
    sheet_names = xls.sheet_names  # List of all the sheets in the workbook (by name)
    num_sheets = len(sheet_names) # Defines number of sheets

    # Read all sheets to a map
    sheet_to_df_map = {}
    for sheet_name in sheet_names:
        sheet_to_df_map[sheet_name] = xls.parse(sheet_name)

    # Read Sheet data into dataclasses
    for i in range(0,num_sheets):

        print("[INFO] Reading sheet #" + str(i+1) + ": \'" + sheet_names[i] + "\'")

        sheet = sheet_to_df_map[sheet_names[i]]
        if not CheckAllRequiredParametersPresent(sheet):
            return False


        test_name = sheet_names[i]

        model_row_index = sheet[sheet["Parameter"] == "models"].index[0]
        light_row_index = sheet[sheet["Parameter"] == "lights"].index[0]
        max_row = len(sheet)

        sheet.set_index("Parameter", inplace=True)

        world_file = sheet.loc["world_file"]['Info']
        if not CheckCorrectExtention(world_file, ".sdf"):
            print("[ERR] World file \'" + world_file + "\' has incorrect extention")
            return False

        movement_path = sheet.loc["movement_path"]['Info']
        if not CheckCorrectExtention(movement_path, ".txt"):
            print("[ERR] Movement Path file \'" + movement_path + "\' has incorrect extention")
            return False

        video_name = sheet.loc["video_name"]['Info']
        if not CheckCorrectExtention(video_name, ".mp4"):
            print("[ERR] Video file \'" + world_file + "\' has incorrect extention")
            return False

        gz_pose_file = sheet.loc["gz_pose_file"]['Info']
        if not CheckCorrectExtention(gz_pose_file, ".txt"):
            print("[ERR] Gazebo Pose file \'" + gz_pose_file + "\' has incorrect extention")
            return False

        vid_pose_file = sheet.loc["vid_pose_file"]['Info']
        if type(vid_pose_file) == str: # Input file is of type string, thus value is given
            if not CheckCorrectExtention(vid_pose_file, ".txt"):
                print("[ERR] Video Pose file \'" + vid_pose_file + "\' has incorrect extention")
                return False
        else: # Make sure file value is not a number (will be used to determine if
            vid_pose_file = np.nan
            print("[INFO] Video to pose file not provided")

        # Import Models and lights
        models = []
        if not ImportModels(models, sheet, model_row_index, light_row_index):
            return False

        lights = []
        if not ImportLights(lights, sheet, light_row_index, max_row):
            return False

        test_data = test_config_data(test_name, world_file, movement_path, video_name, gz_pose_file, vid_pose_file, models, lights)
        tests_config.append(test_data)

    return True

def CheckAllRequiredParametersPresent(sheet):

    # Check that all headers are given
    if not all(header in sheet.columns for header in headers):
        print("[ERR] Headers of file incorrect")
        return False

    # Check that all parameters are present
    for param in parameters:
        if param not in sheet["Parameter"].values:
            print("[ERR] Parameter: \'" + param + "\' not found")
            return False
    return True


# Returns true if filename and extension matches (thus correct extension given)
def CheckCorrectExtention(filename, extension_type):
    return filename.lower().endswith(extension_type)

def ImportModels(models, sheet, start_index, end_index):

    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        model_name = sheet_row["Info"]
        if not CheckCorrectExtention(model_name, "obj"):
            print("[ERR]: Incorrect Model Extension found for: \'" + model_name + "\'")
            return False

        model_pose = sheet_row["Additional_Info"]
        pose = [0, 0, 0, 0, 0, 0]
        if type(model_pose) == str: # Type is a string and pose has been provided
            pose_list = [float(x) for x in model_pose.split(',')]
            if len(pose_list) != 6:
                print("[WARN]: Incorrect number of pose variables provided for: \'" + model_name + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = [pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5]]

        model = [model_name, pose]
        models.append(model)

    return True

def ImportLights(lights, sheet, start_index, end_index):
    return True

def RunSimulation(tests_config):
    # Start Gazebo sim. Give time for sim to open fully
    current_dir = os.getcwd()
    print(current_dir)
    i = 0

    gazebo_sim = subprocess.Popen("gz sim " + current_dir + "/Worlds/" + tests_config[i].world_file, shell=True)
    # gazebo_sim = subprocess.Popen("gz sim " , shell=True)
    time.sleep(100)


    gazebo_sim.terminate()

if __name__ == '__main__':

    # Setup and import data
    filename = 'Test.xlsx'
    if not CheckCorrectExtention(filename, ".xlsx"):
        print("[ERR] Incorrect file extention given for .xlsx")
        exit()

    print("Importing .xlsx file")
    tests_config = []
    if not ImportSheet(tests_config, filename):
        exit()

    # Start Running Simulations
    print("Starting Simulations")
    RunSimulation(tests_config)

