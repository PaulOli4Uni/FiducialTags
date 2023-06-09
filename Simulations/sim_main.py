"""


"""
import sys
import time
import pandas as pd
import numpy as np
from dataclasses import dataclass
import subprocess
import os

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters_config = {"movement_path", "video_name", "gz_pose_file", "vid_pose_file", "cameras", "models", "lights"}
parameters_main = {"test_files_path", "world_file"}


# ------------ DATA CLASSES ------------
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
    cameras: [dc_camera]
    models: [dc_model]
    lights: []  # todo: Add lights data class


# ------------ DATA IMPORT ------------

def ImportSheet(tests_main, tests_config, filename):
    # Read the entire Excel Workbook
    xls = pd.ExcelFile(filename)
    sheet_names = xls.sheet_names  # List of all the sheets in the workbook (by name)
    num_sheets = len(sheet_names)  # Defines number of sheets

    if num_sheets < 2:
        print("[ERR] Two sheets or more must be present. First sheet must be called 'Main'")
        return False

    # Read all sheets to a map
    sheet_to_df_map = {}
    for sheet_name in sheet_names:
        sheet_to_df_map[sheet_name] = xls.parse(sheet_name)

    # Read 'Main' sheet data
    print("[INFO] Reading 'Main' sheet")
    if sheet_names[0] != "Main":
        print("[ERR] First sheet of file not called 'Main'")
        return False
    else:  # Read the data
        sheet = sheet_to_df_map[sheet_names[0]]

        if not CheckAllRequiredParametersMainPresent(sheet): return False

        sheet.set_index("Parameter", inplace=True)
        file_path = sheet.loc["test_files_path"]['Info']
        if not CheckStrValueGiven(file_path, "video_name"): return False
        if not os.path.exists(file_path):  # Ensure the path exists
            print("[ERR] Path provided does not exist")
            return False

        world_file = sheet.loc["world_file"]['Info']
        if not CheckStrValueGiven(world_file, "world_file"): return False
        if not CheckCorrectExtention(world_file, ".sdf"): return False
        if not CheckFileExists(os.path.join(file_path, "Worlds"), world_file): return False

        tests_main.test_files_path = file_path
        tests_main.world_file = world_file

    # Read rest of Sheet data into dataclasses
    for i in range(1, num_sheets):

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
        if not CheckStrValueGiven(movement_path, "movement_path"): return False
        if not CheckCorrectExtention(movement_path, ".txt"): return False
        if not CheckFileExists(os.path.join(tests_main.test_files_path, "Movement_Files"), movement_path): return False

        video_name = sheet.loc["video_name"]['Info']
        if not CheckStrValueGiven(video_name, "video_name"): return False
        if not CheckCorrectExtention(video_name, ".mp4"): return False

        gz_pose_file = sheet.loc["gz_pose_file"]['Info']
        if not CheckStrValueGiven(gz_pose_file, "gz_pose_file"): return False
        if not CheckCorrectExtention(gz_pose_file, ".txt"): return False

        vid_pose_file = sheet.loc["vid_pose_file"]['Info']
        if type(vid_pose_file) == str:  # Input file is of type string, thus value is given
            # NB: Test should not be performed with 'CheckStrValueGiven(vid_pose_file, "vid_pose_file")' as a error
            # should not be returned if the input is not a string
            if not CheckCorrectExtention(vid_pose_file, ".txt"): return False
        else:  # Make sure file value is not a number (nan will tell sim program to not extract pose from generated
            # video folder)
            vid_pose_file = np.nan
            print("[INFO] Video to pose file not provided")

        # Import Cameras, Models and lights
        cameras = []
        if not ImportCameras(cameras, sheet, camera_row_index, model_row_index): return False

        models = []
        if not ImportModels(models, sheet, model_row_index, light_row_index): return False

        lights = []
        if not ImportLights(lights, sheet, light_row_index, max_row): return False

        test_data = dc_test_config_data(test_name, movement_path, video_name, gz_pose_file, vid_pose_file, cameras,
                                        models, lights)
        tests_config.append(test_data)
    return True


def CheckAllRequiredParametersMainPresent(sheet):
    # Check that all headers are given
    if not all(header in sheet.columns for header in headers):
        print("[ERR] Headers of file incorrect")
        return False

    # Check that all parameters are present
    for param in parameters_main:
        if param not in sheet["Parameter"].values:
            print("[ERR] Parameter: \'" + param + "\' not found")
            return False
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


def CheckStrValueGiven(cell_value,
                       parameter_name):  # Returns true if filename and extension matches (thus correct extension given)
    if type(cell_value) != str:
        print("[ERR] Non String data type given for parameter: " + parameter_name)
        return False
    else:
        return True


def CheckCorrectExtention(filename, extension_type):
    if filename.lower().endswith(extension_type):
        return True
    else:
        print("[ERR] Incorrect extension for file: \'" + filename + "\'. Must be of type: \'" + extension_type + "\'")
        return False


def CheckFileExists(path_to_file, filename):
    if os.path.exists(os.path.join(path_to_file, filename)):
        return True
    else:
        print(f"[ERR] {filename} does not exist")
        return False


def ImportCameras(cameras, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        camera_name = sheet_row["Info"]
        if not CheckCorrectExtention(camera_name, ".sdf"):
            return False

        camera_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(camera_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in camera_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + camera_name + "\'. Pose set as [0,0,0,0,0,0]")
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
        if type(model_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in model_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + model_name + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        model = dc_model(model_name, pose)
        models.append(model)

    return True


def ImportLights(lights, sheet, start_index, end_index):
    return True


# ------------ SIMULATION ------------
def StartGazebo(main_config):
    # Start Gazebo sim Give time for sim to open fully
    # Start Gazebo Simulator
    cmd_start = ["gz", "sim", os.path.join(main_config.test_files_path, "Worlds", main_config.world_file)]
    subprocess.Popen(cmd_start, shell=False)

    # Give time for simulator to start
    time.sleep(2)
    # Test if simulator has started
    cmd_start_test = "gz service -s /gazebo/resource_paths/get --reqtype gz.msgs.Empty --reptype gz.msgs.StringMsg_V " \
                     "--timeout 1000 --req \"\""  # Timout of 0.1s
    process = subprocess.Popen(cmd_start_test, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.returncode == 1:  # Check if error has been returned from terminal command (should be a timeout
        # error.) If yes, wait before testing again
        time.sleep(1)
        process = subprocess.Popen(cmd_start_test, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Gazebo has loaded
    time.sleep(2)

def RunSim(main_config, tests_config):


    return True


# ------------ MAIN ------------
if __name__ == '__main__':

    # Setup and import data
    filename = 'Test.xlsx'
    if not CheckCorrectExtention(filename, ".xlsx"):
        print("[ERR] Incorrect file extension given for .xlsx")
        sys.exit()

    main_config = dc_test_main_data
    tests_config = []
    if not ImportSheet(main_config, tests_config,
                       filename):  # Error found during import and 'False' has been returned
        sys.exit()

    print("[INFO] Starting Simulations")
    StartGazebo(main_config)  # Comment this line out if GZ already running
    RunSim(main_config, tests_config)
    """
        Spawning a Model
        gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Markers/DICT_4X4_50_s1000/DICT_4X4_50_s1000_id1/DICT_4X4_50_s1000_id1.sdf", name: "urd22f_model"'
        Spawming a Camera
        gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Cameras/Cam_Basic.sdf", name: "Cam"'

        """
