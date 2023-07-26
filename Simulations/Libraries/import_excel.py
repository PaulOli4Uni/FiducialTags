"""
Standard used in this library.
xx_file -> refers to the variable file. Thus -> Extension is included
xx_name -> Refers to the name of the file (variable). Thus -> NO Extension in the name

"""
import pandas as pd
import numpy as np
import os
from Simulations.Libraries import camera_properties, directory_mappings

from Simulations.Libraries.data_classes import dc_pose, dc_marker, dc_camera, dc_model, dc_test_main_data, \
    dc_test_config_data

headers = {'Parameter', 'Info', 'Additional_Info'}
parameters_config = {"movement_file", "video_file", "gz_pose_file", "vid_pose_file", "cameras", "markers", "lights",
                     "models"}
parameters_main = {"test_files_path", "world_file"}

# ------------ DATA CLASSES ------------
dc_pose = dc_pose.pose
dc_marker = dc_marker.marker
dc_model = dc_model.model
dc_camera = dc_camera.camera
dc_test_main_data = dc_test_main_data.test_main_data
dc_test_config_data = dc_test_config_data.test_config_data

def Import_Excel(testfile_path):


    no_import_error = True
    main_config = dc_test_main_data
    tests_config = []

    if not _CheckCorrectExtention(testfile_path, ".xlsx"):
        print("[ERR] Incorrect file extension given for .xlsx")
        no_import_error = False

    if no_import_error:
        if not _ImportSheet(main_config, tests_config, testfile_path):  # Error found during import and 'False' has been returned
            no_import_error = False

    return no_import_error, main_config, tests_config

def _ImportSheet(tests_main, tests_config, filename):
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

        if not _CheckAllRequiredParametersMainPresent(sheet): return False

        sheet.set_index("Parameter", inplace=True)
        main_file_path = sheet.loc["test_files_path"]['Info']
        if not _CheckStrValueGiven(main_file_path, "test_files_path"): return False
        if not os.path.exists(main_file_path):  # Ensure the path exists
            print("[ERR] Path provided does not exist")
            return False

        world_file = sheet.loc["world_file"]['Info']
        if not _CheckStrValueGiven(world_file, "world_file"): return False
        if not _CheckCorrectExtention(world_file, ".sdf"): return False
        if not _CheckFileExists(os.path.join(main_file_path, "Worlds", world_file)): return False

        tests_main.test_files_path = main_file_path
        tests_main.world_file = world_file

    # Read rest of Sheet data into dataclasses
    for i in range(1, num_sheets):

        print("[INFO] Reading sheet #" + str(i) + ": \'" + sheet_names[i] + "\'")

        sheet = sheet_to_df_map[sheet_names[i]]
        if not _CheckAllRequiredParametersConfigPresent(sheet):
            return False

        test_name = sheet_names[i]

        camera_row_index = sheet[sheet["Parameter"] == "cameras"].index[0]
        marker_row_index = sheet[sheet["Parameter"] == "markers"].index[0]
        light_row_index = sheet[sheet["Parameter"] == "lights"].index[0]
        model_row_index = sheet[sheet["Parameter"] == "models"].index[0]

        max_row = len(sheet)

        sheet.set_index("Parameter", inplace=True)

        movement_file = sheet.loc["movement_file"]['Info']
        if not _CheckStrValueGiven(movement_file, "movement_file"): return False
        if not _CheckCorrectExtention(movement_file, ".txt"): return False
        if not _CheckFileExists(
            os.path.join(tests_main.test_files_path, "Movement_Files", movement_file)): return False

        video_file = _ReturnCellBoolValue(sheet.loc["video_file"]['Info'])
        gz_pose_file = _ReturnCellBoolValue(sheet.loc["gz_pose_file"]['Info'])
        vid_pose_file = _ReturnCellBoolValue(sheet.loc["vid_pose_file"]['Info'])

        # Import Cameras, markers and lights
        cameras = []
        if not _ImportCameras(cameras, tests_main.test_files_path, sheet, camera_row_index,
                             marker_row_index): return False

        markers = []
        if not _ImportMarkers(markers, tests_main.test_files_path, sheet, marker_row_index,
                             light_row_index): return False

        lights = []
        if not _ImportLights(lights, tests_main.test_files_path, sheet, light_row_index,
                            model_row_index): return False

        models = []
        if not _ImportModels(models, tests_main.test_files_path, sheet, model_row_index, max_row): return False

        test_data = dc_test_config_data(test_name, movement_file, video_file, gz_pose_file, vid_pose_file, cameras,
                                        markers, lights, models)

        tests_config.append(test_data)
    return True

def _CheckAllRequiredParametersMainPresent(sheet):
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

def _CheckAllRequiredParametersConfigPresent(sheet):
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

def _CheckStrValueGiven(cell_value, parameter_name):
    # Returns true if filename and extension matches (thus correct extension given)
    if type(cell_value) != str:
        print("[ERR] Non String data type given for parameter: " + parameter_name)
        return False
    else:
        return True

def _CheckCorrectExtention(file, extension_type):
    if file.lower().endswith(extension_type):
        return True
    else:
        print("[ERR] Incorrect extension for file: \'" + file + "\'. Must be of type: \'" + extension_type + "\'")
        return False

def _CheckFileExists(file):
    if os.path.exists(file):
        return True
    else:
        print(f"[ERR] {file} does not exist")
        return False

def _ReturnCellBoolValue(cell_value):

    if type(cell_value) != str:  # Any string value will always be true
        if np.isnan(cell_value):  # 'Nan' if no value is given, therefore 'False'
            return False
        else:
            return bool(cell_value)
    else:
        return True

def _ImportCameras(cameras, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        # File name
        camera_file = sheet_row["Info"]
        if not _CheckCorrectExtention(camera_file, ".sdf"): return False
        if not _CheckFileExists(os.path.join(main_files_path, "Cameras", camera_file)): return False

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
        if not _CheckFileExists(cam_config_file_dir): return False  # Check that Cam Config File Present
        cam_properties = camera_properties.CameraLoader(cam_config_file_dir)
        if not cam_properties.load_properties():
            print("[ERR] in Camera Config File ")
            return False

        camera = dc_camera(camera_file, pose, cam_properties)
        cameras.append(camera)
    return True

def _ImportMarkers(markers, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        marker_file = sheet_row["Info"]
        if type(marker_file) != str:  # Check for NaN, (then no marker present)
            return True

        if not _CheckCorrectExtention(marker_file, ".sdf"):
            print("[ERR]: Incorrect marker Extension found for: \'" + marker_file + "\'")
            return False
        if not _CheckFileExists(directory_mappings.FilePathToMarker(main_files_path, marker_file)): return False

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

def _ImportLights(lights, main_files_path, sheet, start_index, end_index):
    return True

def _ImportModels(models, main_files_path, sheet, start_index, end_index):
    for i in range(start_index, end_index):
        sheet_row = sheet.iloc[i]

        model_file = sheet_row["Info"]
        if type(model_file) != str:  # Check for NaN, (then no model present)
            return True

        if not _CheckCorrectExtention(model_file, ".sdf"):
            print("[ERR]: Incorrect model Extension found for: \'" + model_file + "\'")
            return False
        if not _CheckFileExists(directory_mappings.FilePathToModel(main_files_path, model_file)): return False

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





