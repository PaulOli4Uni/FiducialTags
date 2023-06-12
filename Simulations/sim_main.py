"""
Standard used in this library.
xx_file -> refers to the variable file. Thus -> Extension is included
xx_name -> Refers to the name of the file (variable). Thus -> NO Extension in the name

"""
import sys
import time
import pandas as pd
import numpy as np
from dataclasses import dataclass
import subprocess
import os
from scipy.spatial.transform import Rotation

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters_config = {"movement_path", "video_file", "gz_pose_file", "vid_pose_file", "cameras", "markers", "lights"}
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
class dc_marker:
    marker_file: str
    pose: dc_pose


@dataclass()
class dc_camera:
    camera_file: str
    pose: dc_pose


@dataclass()
class dc_test_main_data:
    test_files_path: str
    world_file: str


@dataclass()
class dc_test_config_data:
    test_name: str
    movement_path: str
    video_file: str
    gz_pose_file: str
    vid_pose_file: str
    cameras: [dc_camera]
    markers: [dc_marker]
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
        main_file_path = sheet.loc["test_files_path"]['Info']
        if not CheckStrValueGiven(main_file_path, "video_file"): return False
        if not os.path.exists(main_file_path):  # Ensure the path exists
            print("[ERR] Path provided does not exist")
            return False

        world_file = sheet.loc["world_file"]['Info']
        if not CheckStrValueGiven(world_file, "world_file"): return False
        if not CheckCorrectExtention(world_file, ".sdf"): return False
        if not CheckFileExists(os.path.join(main_file_path, "Worlds", world_file)): return False

        tests_main.test_files_path = main_file_path
        tests_main.world_file = world_file

    # Read rest of Sheet data into dataclasses
    for i in range(1, num_sheets):

        print("[INFO] Reading sheet #" + str(i) + ": \'" + sheet_names[i] + "\'")

        sheet = sheet_to_df_map[sheet_names[i]]
        if not CheckAllRequiredParametersConfigPresent(sheet):
            return False

        test_name = sheet_names[i]

        camera_row_index = sheet[sheet["Parameter"] == "cameras"].index[0]
        marker_row_index = sheet[sheet["Parameter"] == "markers"].index[0]
        light_row_index = sheet[sheet["Parameter"] == "lights"].index[0]
        max_row = len(sheet)

        sheet.set_index("Parameter", inplace=True)

        movement_path = sheet.loc["movement_path"]['Info']
        if not CheckStrValueGiven(movement_path, "movement_path"): return False
        if not CheckCorrectExtention(movement_path, ".txt"): return False
        if not CheckFileExists(os.path.join(tests_main.test_files_path, "Movement_Files", movement_path)): return False

        video_file = sheet.loc["video_file"]['Info']
        if not CheckStrValueGiven(video_file, "video_file"): return False
        if not CheckCorrectExtention(video_file, ".mp4"): return False

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

        # Import Cameras, markers and lights
        cameras = []
        if not ImportCameras(cameras, tests_main.test_files_path, sheet, camera_row_index, marker_row_index): return False

        markers = []
        if not ImportMarkers(markers, tests_main.test_files_path, sheet, marker_row_index, light_row_index): return False

        lights = []
        if not ImportLights(lights, tests_main.test_files_path, sheet, light_row_index, max_row): return False

        test_data = dc_test_config_data(test_name, movement_path, video_file, gz_pose_file, vid_pose_file, cameras,
                                        markers, lights)
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


def CheckCorrectExtention(file, extension_type):
    if file.lower().endswith(extension_type):
        return True
    else:
        print("[ERR] Incorrect extension for file: \'" + file + "\'. Must be of type: \'" + extension_type + "\'")
        return False


def CheckFileExists(file):
    if os.path.exists(file):
        return True
    else:
        print(f"[ERR] {file} does not exist")
        return False


def ImportCameras(cameras, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        camera_file = sheet_row["Info"]
        if not CheckCorrectExtention(camera_file, ".sdf"):
            return False
        if not CheckFileExists(os.path.join(main_files_path, "Cameras", camera_file)): return False

        camera_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(camera_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in camera_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + camera_file + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        camera = dc_camera(camera_file, pose)
        cameras.append(camera)
    return True


def ImportMarkers(markers, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        marker_file = sheet_row["Info"]
        if not CheckCorrectExtention(marker_file, ".sdf"):
            print("[ERR]: Incorrect marker Extension found for: \'" + marker_file + "\'")
            return False
        if not CheckFileExists(FilePathToMarker(main_files_path, marker_file)): return False

        marker_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(marker_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in marker_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + marker_file + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        marker = dc_marker(marker_file, pose)
        markers.append(marker)

    return True


def ImportLights(lights, main_files_path, sheet, start_index, end_index):
    return True

def FilePathToMarker(main_files_path, marker_file):
    marker_name = marker_file[:-4]  # Drops extension from string
    marker_name_no_id = marker_name.rsplit('_', 1)[0]  # Removes _idXX portion of name
    path_to_marker_file = os.path.join(main_files_path, "Markers", marker_name_no_id, marker_name, marker_file)
    return path_to_marker_file

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

    i = 0 # <- For every world

    # Load Markers & Cameras
    world_name = main_config.world_file[:-4]

    for marker in tests_config[i].markers:
        LoadMarker(world_name, main_config.test_files_path, marker)

    for camera in tests_config[i].cameras:
        LoadCamera(world_name, main_config.test_files_path, camera)

    # Prep Movement File (if time of first line = 0) set seperate and create temp file for other commands
        # Move Camera to correct position (if needed ^- see above)
        # Play Pause

    # Loads movement file
    # Start Camera Record
    # Play
    # Func fin -> Pause Sim
    time.sleep(2) # todo: remove line
    # Remove Markers and Cameras
    for marker in tests_config[i].markers:
        RemoveModel(world_name, marker.marker_file[:-4])
    for camera in tests_config[i].cameras:
        RemoveModel(world_name, camera.camera_file[:-4])
    return True

def LoadMarker(world_name, main_path, marker_dc):

    path_to_marker_file = FilePathToMarker(main_path, marker_dc.marker_file)
    LoadModel(world_name, path_to_marker_file, marker_dc.marker_file[:-4], marker_dc.pose)

def LoadCamera(world_name, main_path, camera_dc):

    camera_name = camera_dc.camera_file[:-4]
    path_to_camera_file = os.path.join(main_path, "Cameras", camera_dc.camera_file)

    LoadModel(world_name, path_to_camera_file, camera_name, camera_dc.pose)

def LoadModel(world_name, path_to_model_inc_extension, model_name, model_pose):

    rot = Rotation.from_euler('xyz', [model_pose.r, model_pose.p, model_pose.y], degrees=False)
    rot_quart = rot.as_quat()

    # Working spawn command
    # gz service -s /world/standard_world/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Simulations/Markers/DICT_4X4_50_s500/DICT_4X4_50_s500_id1/DICT_4X4_50_s500_id1.sdf", name: "DICT_4X4_50_s500_id77", pose: {position: {x:1,y:1,z:2}, orientation: {x:0.5609,y:0.4305,z:-0.0923,w:0.70105}}'

    spawn_cmd = f"gz service -s /world/{world_name}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean " \
                f"--timeout 1000 --req \'sdf_filename: \"{path_to_model_inc_extension}\", " \
                f"name: \"{model_name}\", pose: {{position: {{x:{model_pose.X},y:{model_pose.Y},z:{model_pose.Z}}}, " \
                f"orientation: {{x:{rot_quart[0]},y:{rot_quart[1]},z:{rot_quart[2]},w:{rot_quart[3]}}}}}\'"

    result = subprocess.run(spawn_cmd, shell=True, capture_output=True, text=True)
    print(result)
    # subprocess.run(spawn_cmd)

def RemoveModel(world_name, model_name):

    remove_cmd = f"gz service -s /world/{world_name}/remove --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean " \
                 f"--timeout 1000 --req 'name: \"{model_name}\", type: 2'"
    result = subprocess.run(remove_cmd, shell=True, capture_output=True, text=True)
    print(result)


# ------------ MAIN ------------
if __name__ == '__main__':
    print(os.path.dirname(os.path.abspath(__file__)))
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
    # StartGazebo(main_config)  # Comment this line out if GZ already running
    RunSim(main_config, tests_config)
    """
        Spawning a marker
        gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Markers/DICT_4X4_50_s1000/DICT_4X4_50_s1000_id1/DICT_4X4_50_s1000_id1.sdf", name: "urd22f_marker"'
        Spawming a Camera
        gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 1000 --req 'sdf_filename: "/home/stb21753492/FiducialTags/Cameras/Cam_Basic.sdf", name: "Cam"'

        """
