"""


"""
import sys
import time
import pandas as pd
import numpy as np
from dataclasses import dataclass
import subprocess
import os
from dotenv import load_dotenv
import signal

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters_config = {"movement_path", "video_name", "gz_pose_file", "vid_pose_file", "cameras", "models", "lights"}
parameters_main = {"test_files_path", "world_file"}
@dataclass()
class dc_pose:
    X: float
    Y: float
    Z: float
    r: float
    p: float
    y: float

@dataclass()
class dc_model:
    model_name: str
    pose: dc_pose

@dataclass()
class dc_camera:
    camera_name: str
    camera_pose: dc_pose

@dataclass()
class dc_test_main_data:
    test_files_path: str
    world_file: str

@dataclass()
class dc_test_config_data:
    test_name: str
    movement_path: str
    video_name: str
    gz_pose_file: str
    vid_pose_file: str
    cameras: dc_camera
    models: dc_model
    lights: []  # todo: Add lights data class

def ImportSheet(tests_config, filename):
    # Read the entire Excel Workbook
    xls = pd.ExcelFile(filename)
    sheet_names = xls.sheet_names  # List of all the sheets in the workbook (by name)
    num_sheets = len(sheet_names) # Defines number of sheets

    if num_sheets < 2:
        print("[ERR] Two sheets or more must be present. First sheet must be called 'Main'")
        return False

    # Read all sheets to a map
    sheet_to_df_map = {}
    for sheet_name in sheet_names:
        sheet_to_df_map[sheet_name] = xls.parse(sheet_name)

    # Read 'Main' sheet data
    #XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    main_data = dc_test_main_data("~/", "file")

    # Read rest of Sheet data into dataclasses
    for i in range(1,num_sheets):

        print("[INFO] Reading sheet #" + str(i) + ": \'" + sheet_names[i] + "\'")

        sheet = sheet_to_df_map[sheet_names[i]]
        if not CheckAllRequiredParametersConfigPresent(sheet):
            return False


        test_name = sheet_names[i]

        camera_row_index = sheet[sheet["Parameter"] == "cameras"].index[0]
        model_row_index = sheet[sheet["Parameter"] == "models"].index[0]
        light_row_index = sheet[sheet["Parameter"] == "lights"].index[0]
        max_row = len(sheet)

        sheet.set_index("Parameter", inplace=True)

        movement_path = sheet.loc["movement_path"]['Info']
        if not CheckCorrectExtention(movement_path, ".txt"):
            return False

        video_name = sheet.loc["video_name"]['Info']
        if not CheckCorrectExtention(video_name, ".mp4"):
            return False

        gz_pose_file = sheet.loc["gz_pose_file"]['Info']
        if not CheckCorrectExtention(gz_pose_file, ".txt"):
            return False

        vid_pose_file = sheet.loc["vid_pose_file"]['Info']
        if type(vid_pose_file) == str: # Input file is of type string, thus value is given
            if not CheckCorrectExtention(vid_pose_file, ".txt"):
                return False
        else: # Make sure file value is not a number (will be used to determine if
            vid_pose_file = np.nan
            print("[INFO] Video to pose file not provided")

        # Import Cameras, Models and lights
        cameras = []



        models = []
        if not ImportModels(models, sheet, model_row_index, light_row_index):
            return False

        lights = []
        if not ImportLights(lights, sheet, light_row_index, max_row):
            return False

        test_data = dc_test_config_data(test_name, movement_path, video_name, gz_pose_file, vid_pose_file, cameras, models, lights)
        tests_config.append(test_data)

    return True

def CheckAllRequiredParametersConfigPresent(sheet):

    # Check that all headers are given
    if not all(header in sheet.columns for header in headers):
        print("[ERR] Headers of file incorrect")
        return False

    # Check that all parameters are present
    for param in parameters_config:
        if param not in sheet["Parameter"].values:
            print("[ERR] Parameter: \'" + param + "\' not found")
            return False
    return True


# Returns true if filename and extension matches (thus correct extension given)
def CheckCorrectExtention(filename, extension_type):
    print("[ERR]: Incorrect extension found for: \'" + filename + "\'")
    return filename.lower().endswith(extension_type)

def ImportCameras(cameras, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        camera_name = sheet_row["Info"]
        if not CheckCorrectExtention(camera_name, ".sdf"):
            return False

        camera_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(camera_pose) == str: # Type is a string and pose has been provided
            pose_list = [float(x) for x in camera_pose.split(',')]
            if len(pose_list) != 6:
                print("[WARN]: Incorrect number of pose variables provided for: \'" + camera_name + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        model = dc_model(camera_name, pose)
        cameras.append(model)
    return True

def ImportModels(models, sheet, start_index, end_index):

    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        model_name = sheet_row["Info"]
        if not CheckCorrectExtention(model_name, ".sdf"):
            print("[ERR]: Incorrect Model Extension found for: \'" + model_name + "\'")
            return False

        model_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(model_pose) == str: # Type is a string and pose has been provided
            pose_list = [float(x) for x in model_pose.split(',')]
            if len(pose_list) != 6:
                print("[WARN]: Incorrect number of pose variables provided for: \'" + model_name + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        model = dc_model(model_name, pose)
        models.append(model)

    return True

def ImportLights(lights, sheet, start_index, end_index):
    return True

def RunSimulation(tests_config):
    # Start Gazebo sim. Give time for sim to open fully
    current_dir = os.getcwd()
    print(current_dir)
    i = 0

    # Start Gazebo Simulator
    cmd_start = "gz sim " + current_dir + "/Worlds/" + tests_config[i].world_file
    # gazebo_sim = subprocess.Popen("exec " + cmd_start, stdout=subprocess.PIPE, shell=True)
    gazebo_sim = subprocess.Popen("exec " + cmd_start, stdout=subprocess.PIPE, shell=True)

    # Give time for simulator to start
    time.sleep(2)
    # Test if simulator has started
    cmd_start_test = "gz service -s /gazebo/resource_paths/get --reqtype gz.msgs.Empty --reptype gz.msgs.StringMsg_V --timeout 1000 --req \"\"" # Timout of 0.1s
    process = subprocess.Popen(cmd_start_test, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.returncode == 1: # Check if error has been returned from terminal command (should be a timeout error.) If yes, wait before testing again
        time.sleep(1)
        process = subprocess.Popen(cmd_start_test, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Gazebo has loaded

    """
    Spawning a Model
    gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Markers/DICT_4X4_50_s1000/DICT_4X4_50_s1000_id1/DICT_4X4_50_s1000_id1.sdf", name: "urd22f_model"'
    Spawming a Camera
    gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Cameras/Cam_Basic.sdf", name: "Cam"'

    """


if __name__ == '__main__':

    load_dotenv()

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
    # RunSimulation(tests_config)

