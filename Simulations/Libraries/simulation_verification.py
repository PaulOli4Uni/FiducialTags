import time
import subprocess
import os

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation
import shutil

from Simulations.Libraries import directory_mappings
from Simulations.Libraries.data_classes import dc_pose
dc_pose = dc_pose.pose

# CHANGE INFO FOR EACH TEST

test_name = "test1"
marker_name = "DICT_4X4_50_s100_id0"
camera_name = "KahnPhone_new"

marker_pose = dc_pose(0,0,1,np.deg2rad(0),np.deg2rad(0),np.deg2rad(0))
camera_pose = dc_pose(0,0,2,np.deg2rad(-180),np.deg2rad(0),np.deg2rad(-180))

movement_file_dir = '../Verification/MovMatrix_10.csv'

# Do Not Change
camera_file_dir = '../Verification/Cameras/' + camera_name + '.sdf'
marker_file_dir = os.path.join('../Verification', marker_name, (marker_name+'.sdf'))
camera_config_file_dir = camera_file_dir[:-4] + "_config.txt"
world_name = 'standard_world'
test_files_path = '../Verification'
tmp_movement_file_dir = 'tmp_files/tmp_file.txt'

def RunSim():

    print("[INFO] Starting test: " + test_name)
    test_dir = os.path.join(test_files_path, "Tests", test_name)
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

    # Load Marker
    LoadModel(world_name, test_name, marker_file_dir, marker_name, marker_pose)
    # Load Camera
    LoadModel(world_name, test_name, camera_file_dir, camera_name, camera_pose)


    # Check that all models have loaded
    num_models = 2
    num_model_cmd = "gz model --list"
    result = subprocess.run(num_model_cmd, shell=True, capture_output=True, text=True)

    while True:
        model_count = 0
        for char in result.stdout:  # Command output presents models with a '-' in bullet format
            if char == '-':
                model_count += 1

        if model_count == num_models:
            break
        else:
            time.sleep(0.1)

    # Prep Movement File (if time of first line = 0) set separate and create temp file for other commands
    all_movement_cmds = process_csv_file(movement_file_dir, marker_pose, t=0.5)
    print("[INFO] Starting Movement File")
    PlaySim(world_name)

    for move_cmd in all_movement_cmds:
        print(move_cmd)
        RunPoseString(test_name, marker_name, move_cmd)
        WaitMovementComplete(test_name, marker_name)  # Only have to look at one camera
        time.sleep(0.2)
        TakeImage()
        time.sleep(0.2)

    PauseSim(world_name)
    print("[INFO] Movement File Finished")

    # Remove Markers, Cameras and Models
    print("[INFO] Removing Markers and Cameras")

    RemoveModel(world_name, test_name, marker_name)
    RemoveModel(world_name, test_name, camera_name)

    return True

def LoadModel(world_name, test_name, path_to_model_inc_extension, model_name, model_pose):

    rot = Rotation.from_euler('xyz', [model_pose.r, model_pose.p, model_pose.y], degrees=False)
    rot_quart = rot.as_quat()

    spawn_cmd = f"gz service -s /world/{world_name}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean " \
                f"--timeout 1000 --req \'sdf_filename: \"{path_to_model_inc_extension}\", " \
                f"name: \"{CombineTestandObjectName(test_name, model_name)}\", pose: {{position: {{x:{model_pose.X},y:{model_pose.Y},z:{model_pose.Z}}}, " \
                f"orientation: {{x:{rot_quart[0]},y:{rot_quart[1]},z:{rot_quart[2]},w:{rot_quart[3]}}}}}\'"

    result = subprocess.run(spawn_cmd, shell=True, capture_output=True, text=True)
    # print(result)

def RemoveModel(world_name, test_name, model_name):

    remove_cmd = f"gz service -s /world/{world_name}/remove --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean " \
                 f"--timeout 1000 --req 'name: \"{CombineTestandObjectName(test_name, model_name)}\", type: 2'"
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
def WritePoseTmpfile(main_path, tmp_filename, lines, degrees):

    with open(os.path.join(main_path, tmp_filename), 'w') as tmp_file:

        if degrees: #  No changes have to be made
            tmp_file.writelines(lines)
        else: #  Convert to degrees
            for line in lines:
                tmp_file.write(ConvertLineRad2Deg(line))

def ConvertLineRad2Deg(line):
    values = line.strip().split(',')
    values[3] = str(np.rad2deg(float(values[3])))
    values[4] = str(np.rad2deg(float(values[4])))
    values[5] = str(np.rad2deg(float(values[5])))
    return ','.join(values) + '\n'

def RunPoseString(test_name, model_name, pose_msg):
    print("New Mvm command")
    wait_cmd = f"gz topic -e -t /model/{CombineTestandObjectName(test_name, model_name)}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
    process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE)

    movement_command_not_received = True
    while movement_command_not_received:
        pose_cmd = f"gz topic -t /model/{CombineTestandObjectName(test_name, model_name)}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
        subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)

        output = process.stdout.readline()
        print("This is output: " + str(output))
        # If value received, break from while
        if process.poll() is not None:
            print('1')
            break
        if output:
            print('2')
            process.terminate()
            movement_command_not_received = False


def WaitMovementComplete(test_name, model_name):

    wait_cmd = f"gz topic -e -t /model/{CombineTestandObjectName(test_name, model_name)}/move_fin"
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

def CombineTestandObjectName(test_name, object_name):
    return test_name + "_" + object_name

def TakeImage():
    image_cmd = f"gz topic -t /TakeImg -m gz.msgs.Boolean -p 'data:True'"
    result = subprocess.run(image_cmd, shell=True, capture_output=True, text=True)


def process_csv_file(csv_filename, initial_pose, t=0.1):
    # Read the CSV file into a DataFrame
    initial_pose = {'X': initial_pose.X, 'Y': initial_pose.Y, 'Z': initial_pose.Z, 'r': initial_pose.r, 'p': initial_pose.p, 'y': initial_pose.y}
    # Define column names
    columns = ['X', 'Y', 'Z', 'r', 'p', 'y']

    # Read the CSV file into a DataFrame with explicitly defined column names
    df = pd.read_csv(csv_filename, names=columns)

    # Convert mm to meters for translations (x, y, z)
    df['X'] = df['X'] / 1000.0  # Convert from mm to m
    df['Y'] = df['Y'] / 1000.0  # Convert from mm to m
    df['Z'] = df['Z'] / 1000.0  # Convert from mm to m

    # Calculate the cumulative sum for translations (x, y, z) and rotations (r, p, y)
    # RoboDK movements relative to robot-arm flange (tool). Thus an remappig has to be done. Luckily its a direct remapping
    # No remapping on the provided pose for marker starting position
    # See Masters Book p118
    df['cumulative_x'] = initial_pose['X'] - df['X'].cumsum()
    df['cumulative_y'] = initial_pose['Y'] - df['Y'].cumsum()
    df['cumulative_z'] = initial_pose['Z'] - df['Z'].cumsum()
    df['cumulative_r'] = np.rad2deg(initial_pose['r'])  - df['r'].cumsum()
    df['cumulative_p'] = np.rad2deg(initial_pose['p']) - df['p'].cumsum()
    df['cumulative_yaw'] = np.rad2deg(initial_pose['y']) + df['y'].cumsum()


    # Add the extra variable with the given value (default is 0.1)
    df['extra'] = t

    # Select only the required columns and convert each row into a string
    processed_data = df[
        ['cumulative_x', 'cumulative_y', 'cumulative_z', 'cumulative_r', 'cumulative_p', 'cumulative_yaw',
         'extra']].astype(str).apply(','.join, axis=1).tolist()

    return processed_data


RunSim()