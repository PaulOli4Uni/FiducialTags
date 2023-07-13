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
import shutil
from Libraries import camera_properties

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters_config = {"movement_file", "video_file", "gz_pose_file", "vid_pose_file", "cameras", "markers", "lights", "models"}
parameters_main = {"test_files_path", "world_file"}

tmp_movement_file_dir = 'tmp_files/tmp_file.txt'
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
class dc_model:
    model_file: str
    pose: dc_pose

@dataclass()
class dc_camera:
    camera_file: str
    pose: dc_pose
    config: camera_properties


@dataclass()
class dc_test_main_data:
    test_files_path: str
    world_file: str


@dataclass()
class dc_test_config_data:
    test_name: str
    movement_file: str
    video_file: bool
    gz_pose_file: bool
    vid_pose_file: bool
    cameras: [dc_camera]
    markers: [dc_marker]
    lights: []  # todo: Add lights data class
    models: [dc_model]


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
        if not CheckStrValueGiven(main_file_path, "test_files_path"): return False
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
        model_row_index = sheet[sheet["Parameter"] == "models"].index[0]

        max_row = len(sheet)

        sheet.set_index("Parameter", inplace=True)

        movement_file = sheet.loc["movement_file"]['Info']
        if not CheckStrValueGiven(movement_file, "movement_file"): return False
        if not CheckCorrectExtention(movement_file, ".txt"): return False
        if not CheckFileExists(os.path.join(tests_main.test_files_path, "Movement_Files", movement_file)): return False

        video_file = ReturnCellBoolValue(sheet.loc["video_file"]['Info'])
        gz_pose_file = ReturnCellBoolValue(sheet.loc["gz_pose_file"]['Info'])
        vid_pose_file = ReturnCellBoolValue(sheet.loc["vid_pose_file"]['Info'])

        # Import Cameras, markers and lights
        cameras = []
        if not ImportCameras(cameras, tests_main.test_files_path, sheet, camera_row_index, marker_row_index): return False

        markers = []
        if not ImportMarkers(markers, tests_main.test_files_path, sheet, marker_row_index, light_row_index): return False

        lights = []
        if not ImportLights(lights, tests_main.test_files_path, sheet, light_row_index, model_row_index): return False

        models = []
        if not ImportModels(models, tests_main.test_files_path, sheet, model_row_index, max_row): return False

        test_data = dc_test_config_data(test_name, movement_file, video_file, gz_pose_file, vid_pose_file, cameras,
                                        markers, lights, models)

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


def CheckStrValueGiven(cell_value, parameter_name):
    # Returns true if filename and extension matches (thus correct extension given)
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

def ReturnCellBoolValue(cell_value):

    if type(cell_value) != str:  # Any string value will always be true
        if np.isnan(cell_value):  # 'Nan' if no value is given, therefore 'False'
            return False
        else:
            return bool(cell_value)
    else:
        return True

def ImportCameras(cameras, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        # File name
        camera_file = sheet_row["Info"]
        if not CheckCorrectExtention(camera_file, ".sdf"): return False
        if not CheckFileExists(os.path.join(main_files_path, "Cameras", camera_file)): return False

        # Camera Model Pose
        camera_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(camera_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in camera_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + camera_file + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        # Camera Config
        cam_config_file_dir = os.path.join(main_files_path, "Cameras", (camera_file[:-4] + "_config.txt"))
        if not CheckFileExists(cam_config_file_dir): return False  # Check that Cam Config File Present
        cam_properties = camera_properties.CameraLoader(cam_config_file_dir)
        if not cam_properties.load_properties():
            print("[ERR] in Camera Config File ")
            return False

        camera = dc_camera(camera_file, pose, cam_properties)
        cameras.append(camera)
    return True


def ImportMarkers(markers, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        marker_file = sheet_row["Info"]
        if type(marker_file) != str:  # Check for NaN, (then no marker present)
            return True

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

def ImportModels(models, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        model_file = sheet_row["Info"]
        if type(model_file) != str:  # Check for NaN, (then no model present)
            return True

        if not CheckCorrectExtention(model_file, ".sdf"):
            print("[ERR]: Incorrect model Extension found for: \'" + model_file + "\'")
            return False
        if not CheckFileExists(FilePathToModel(main_files_path, model_file)): return False

        model_pose = sheet_row["Additional_Info"]
        pose = dc_pose(0, 0, 0, 0, 0, 0)
        if type(model_pose) == str:  # Type is a string and pose has been provided
            pose_list = [float(x) for x in model_pose.split(',')]
            if len(pose_list) != 6:
                print(
                    "[WARN]: Incorrect number of pose variables provided for: \'" + model_file + "\'. Pose set as [0,0,0,0,0,0]")
            else:
                pose = dc_pose(pose_list[0], pose_list[1], pose_list[2], pose_list[3], pose_list[4], pose_list[5])

        model = dc_model(model_file, pose)
        models.append(model)

    return True


def FilePathToMarker(main_files_path, marker_file):
    marker_name = marker_file[:-4]  # Drops extension from string
    marker_name_no_id = marker_name.rsplit('_', 1)[0]  # Removes _idXX portion of name
    path_to_marker_file = os.path.join(main_files_path, "Markers", marker_name_no_id, marker_name, marker_file)
    return path_to_marker_file

def FilePathToModel(main_files_path, model_file):
    path_to_model_file = os.path.join(main_files_path, "Models", model_file[:-4], model_file)
    return path_to_model_file
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


    for test_config in tests_config:
        world_name = main_config.world_file[:-4]
        print("[INFO] Strating test: " + test_config.test_name)
        test_dir = os.path.join(main_config.test_files_path, "Tests", test_config.test_name)
        print("[INFO] Making directory for test results at: \'" + test_dir + "\'")
        # os.makedirs(test_dir)
        if not os.path.exists(test_dir): # Create the directory
            os.makedirs(test_dir)
        else:  # Clear the directory of its contents
            # os.remove(test_dir)
            shutil.rmtree(test_dir)
            os.makedirs(test_dir)
        # Load Markers, Cameras and Models
        print("[INFO] Spawning Markers and Cameras")
        for marker in test_config.markers:
            LoadMarker(world_name, main_config.test_files_path, marker)

        for camera in test_config.cameras:
            LoadCamera(world_name, main_config.test_files_path, camera)

        for model in test_config.models:
            model_file = model.model_file
            path_to_model_file = FilePathToModel(main_config.test_files_path, model_file)
            LoadModel(world_name, path_to_model_file, model_file[:-4], model.pose)


        # Check that all models have loaded
        num_models = len(test_config.markers) + len(test_config.cameras) + len(test_config.models)

        num_model_cmd = "gz model --list"
        result = subprocess.run(num_model_cmd, shell=True, capture_output=True, text=True)

        while True:
            model_count = 0
            for char in result.stdout:  # Command output presents models with a '-' in buller format
                if char == '-':
                    model_count += 1

            if model_count == num_models:
                break
            else:
                time.sleep(0.1)

        # Prep Movement File (if time of first line = 0) set separate and create temp file for other commands
        pose_message = LoadPoseMovementFile(main_config.test_files_path, test_config.movement_file)
        if pose_message:
            print("[INFO] Moving camera(s) to starting position")
            for camera in test_config.cameras:
                RunPoseString(camera.camera_file[:-4], pose_message)

            PlaySim(world_name)
            WaitMovementComplete(test_config.cameras[0].camera_file[:-4])  # Only have to look at one camera
            PauseSim(world_name)

        print("[INFO] Running movement_file")
        for camera in test_config.cameras:
            camera_name = camera.camera_file[:-4]

            if test_config.video_file:
                topic_names = camera.config.get_all_topic_names()
                for topic_name in topic_names:
                    video_file = f"vid_{camera_name}_{topic_name}.mp4"
                    StartCameraVideoRecord(topic_name, os.path.join(test_dir, video_file))

            if test_config.gz_pose_file:
                gz_pose_file = f"gz_pose_{camera_name}.txt"
                StartCameraPoseCapture(camera_name, os.path.join(test_dir, gz_pose_file))

            RunPoseFile(camera_name, os.path.join(main_config.test_files_path, tmp_movement_file_dir))

        PlaySim(world_name)
        WaitMovementComplete(test_config.cameras[0].camera_file[:-4])  # Only have to look at one camera
        PauseSim(world_name)
        print("[INFO] Movement_file finished")

        # Remove Markers, Cameras and Models
        print("[INFO] Removing Markers and Cameras")
        for marker in test_config.markers:
            RemoveModel(world_name, marker.marker_file[:-4])
        for camera in test_config.cameras:
            camera_name = camera.camera_file[:-4]

            if test_config.video_file:
                # video_file = f"vid_{camera_name}.mp4"
                # StopCameraVideoRecord(camera_name, os.path.join(test_dir, video_file))
                topic_names = camera.config.get_all_topic_names()
                for topic_name in topic_names:
                    video_file = f"vid_{camera_name}_{topic_name}.mp4"
                    StopCameraVideoRecord(topic_name, os.path.join(test_dir, video_file))

            if test_config.gz_pose_file:
                gz_pose_file = f"gz_pose_{camera_name}.txt"
                StopCameraPoseCapture(camera_name, os.path.join(test_dir, gz_pose_file))

            RemoveModel(world_name, camera_name)

        for model in test_config.models:
            RemoveModel(world_name, model.model_file[:-4])
        # os.remove(os.path.join(main_config.test_files_path, tmp_movement_file_dir))  # Remove tmp_movement_file

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

    spawn_cmd = f"gz service -s /world/{world_name}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean " \
                f"--timeout 1000 --req \'sdf_filename: \"{path_to_model_inc_extension}\", " \
                f"name: \"{model_name}\", pose: {{position: {{x:{model_pose.X},y:{model_pose.Y},z:{model_pose.Z}}}, " \
                f"orientation: {{x:{rot_quart[0]},y:{rot_quart[1]},z:{rot_quart[2]},w:{rot_quart[3]}}}}}\'"

    result = subprocess.run(spawn_cmd, shell=True, capture_output=True, text=True)
    # print(result)

def RemoveModel(world_name, model_name):

    remove_cmd = f"gz service -s /world/{world_name}/remove --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean " \
                 f"--timeout 1000 --req 'name: \"{model_name}\", type: 2'"
    result = subprocess.run(remove_cmd, shell=True, capture_output=True, text=True)
    # print(result)

def PlaySim(world_name):
    play_cmd = f"gz service -s /world/{world_name}/control --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean --timeout 1000 --req 'pause: false'"
    result = subprocess.run(play_cmd, shell=True, capture_output=True, text=True)
    # print(result)

def PauseSim(world_name):
    pause_cmd = f"gz service -s /world/{world_name}/control --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean --timeout 1000 --req 'pause: true'"
    result = subprocess.run(pause_cmd, shell=True, capture_output=True, text=True)
    # print(result)

def LoadPoseMovementFile(main_path, movement_file):
    """
    Prepares the Pose Movement File and create tmp file which should be called
    Temporary filename will be 'tmp_movement.txt'
    Checks if the first movement command has a time of zero (starting position) and removes this when creating tmp file


    Parameters
    ----------
    main_path
    movement_file

    Returns
    -------
    False -> if First line's last number is NOT a zero. Tmp file can be used directly
    String Pose Line - > if first line's last number IS a zero. The pose line returned has to be run first before
    running the tmp file. (To ensure camera is at correct starting position)
    """
    file_path = os.path.join(main_path, "Movement_Files", movement_file)
    with open(file_path, 'r') as file:
        lines = file.readlines()

    first_line = lines[0].rstrip()
    last_number = float(first_line.split(',')[-1])

    if last_number == 0.0:
        tmp_filename = tmp_movement_file_dir
        tmp_lines = lines[1:]

        with open(tmp_filename, 'w') as tmp_file:
            tmp_file.writelines(tmp_lines)

        # print(f"First line stored: {first_line}")
        # print(f"Temporary file '{tmp_filename}' created.")

        # Change time of last line to 1 second before returning pose command
        initial_pose_cmd = first_line.split(',')
        last_number_index = len(initial_pose_cmd) - 1
        initial_pose_cmd[last_number_index] = '1'

        initial_pose_cmd = ','.join(initial_pose_cmd)
        return initial_pose_cmd
    else:
        tmp_filename = 'tmp_file.txt'
        with open(tmp_filename, 'w') as tmp_file:
            tmp_file.writelines(lines)

        # print(f"Temporary file '{tmp_filename}' created.")
        return False

def RunPoseString(model_name, pose_msg):

    pose_cmd = f"gz topic -t /model/{model_name}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
    result = subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)

def RunPoseFile(model_name, pose_file):

    pose_cmd = f"gz topic -t /model/{model_name}/file_pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_file}\"\'"
    result = subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)

def StartCameraPoseCapture(model_name, gz_pose_file):

    pose_storage_start_cmd = f"gz service -s /model/{model_name}/PoseToFile --timeout 2000 --reqtype gz.msgs.VideoRecord " \
                       f"--reptype gz.msgs.Int32 --req \'start:true, stop:false, save_filename:\"{gz_pose_file}\"\'"
    # print(pose_storage_start_cmd)
    result = subprocess.run(pose_storage_start_cmd, shell=True, capture_output=True, text=True)
    # gz service -s /pose_to_file --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype gz.msgs.Int32 --req 'start:true, save_filename:"name.txt"'

def StopCameraPoseCapture(model_name, gz_pose_file):

    pose_storage_stop_cmd = f"gz service -s /model/{model_name}/PoseToFile --timeout 2000 --reqtype gz.msgs.VideoRecord " \
                       f"--reptype gz.msgs.Int32 --req \'start:false, stop:true, save_filename:\"{gz_pose_file}\"\'"
    # print(pose_storage_stop_cmd)
    result = subprocess.run(pose_storage_stop_cmd, shell=True, capture_output=True, text=True)

def StartCameraVideoRecord(model_name, video_file):

    camera_rcd_start_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:true, save_filename:\"{video_file}\"\'"
    result = subprocess.run(camera_rcd_start_cmd, shell=True, capture_output=True, text=True)

def StopCameraVideoRecord(model_name, video_file):

    camera_rcd_stop_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:false, save_filename:\"{video_file}\"\'"
    result = subprocess.run(camera_rcd_stop_cmd, shell=True, capture_output=True, text=True)

def WaitMovementComplete(model_name):

    wait_cmd = f"gz topic -e -t /model/{model_name}/move_fin "
    process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE)

    movement_command_not_received = True
    while movement_command_not_received:
        output = process.stdout.readline()
        # If value received, break from while
        if process.poll() is not None:
            break
        if output:
            process.terminate()
            movement_command_not_received = False




# ------------ MAIN ------------
if __name__ == '__main__':

    test_path = os.path.dirname(os.path.abspath(__file__))
    # Setup and import data

    filename = test_path + "/Calibration.xlsx"
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

