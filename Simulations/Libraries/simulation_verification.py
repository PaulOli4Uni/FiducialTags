import time
import subprocess
import os

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation
import shutil
import select
import glob

from Simulations.Libraries import directory_mappings
from Simulations.Libraries.data_classes import dc_pose
dc_pose = dc_pose.pose

# CHANGE INFO FOR EACH TEST

test_name = "test1"
marker_name = "3Markers"
# marker_name = "Pattern_Cropped_Gz"
camera_name = "Canon"

marker_pose = dc_pose(0,0,1,np.deg2rad(0),np.deg2rad(0),np.deg2rad(0))
# camera_pose = dc_pose(0.007,-0.0263,2.3198,np.deg2rad(-180-2.2752),np.deg2rad(0-2.4637),np.deg2rad(-180+0.7))
camera_pose = dc_pose(0.0+0.008,0-0.004,1+0.826+0.1198,np.deg2rad(-180),np.deg2rad(0),np.deg2rad(-180-.7))

movement_file_dir = '../Verification/Kuka_Files/CSV_Files_for_Test/MovMatrix_10.csv'
world_img_files_path = f"/home/paul/FiducialTags/Simulations/Worlds/{camera_name}"
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
    all_movement_cmds = process_csv_file(movement_file_dir, marker_pose, t=.6)
    print("[INFO] Starting Movement File")
    PlaySim(world_name)

    #  - Break into two. First 350 images and then the next 350
    # Calculate the midpoint index
    midpoint = len(all_movement_cmds) // 2

    # Split the list into two smaller lists
    # half_movement_cmds = all_movement_cmds[:midpoint]
    # half_movement_cmds = all_movement_cmds[midpoint:]
    half_movement_cmds = all_movement_cmds[595:]

    for img_num, move_cmd in enumerate(half_movement_cmds):
        print("New Mvm command")
        pose_str = RunPoseString(test_name, marker_name, move_cmd)
        print("Waiting for Mvm to complete")
        WaitMovementComplete(test_name, marker_name, pose_str)  # Only have to look at one camera
        print("Mvmnt Complete")
        TakeImage(world_img_files_path,img_num)
        print("Image Taken")


    PauseSim(world_name)
    print("[INFO] Movement File Finished")
    time.sleep(5)
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

    pose_cmd = f"gz topic -t /model/{CombineTestandObjectName(test_name, model_name)}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
    subprocess.run(pose_cmd, shell=True, capture_output=False, text=True)
    wait_cmd = f"gz topic -e -t /model/{CombineTestandObjectName(test_name, model_name)}/pos_contr"
    print(pose_cmd)
    #
    # scan_process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # poll_obj = select.poll()
    # poll_obj.register(scan_process.stdout, select.POLLIN)
    # pose_msg_not_sent = True
    # while pose_msg_not_sent:
    #     subprocess.run(pose_cmd, shell=True, capture_output=False, text=True)
    #     poll_result = poll_obj.poll(0)
    #     if poll_result:
    #         line = scan_process.stdout.readline()
    #         # print(line)
    #         poll_obj.unregister(scan_process.stdout)
    #         pose_msg_not_sent = False
    # print("Pose Given Successfully")
    return pose_cmd

def WaitMovementComplete(test_name, model_name, pose_cmd):

    wait_cmd = f"gz topic -e -t /model/{CombineTestandObjectName(test_name, model_name)}/move_fin"

    scan_process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    poll_obj = select.poll()
    poll_obj.register(scan_process.stdout, select.POLLIN)
    movement_command_not_received = True
    start_time = time.time()
    i = 0
    while movement_command_not_received:
        poll_result = poll_obj.poll(0)
        # print(poll_result)
        if poll_result:
            print(poll_result)
            line = scan_process.stdout.readline()
            # print(line)
            poll_obj.unregister(scan_process.stdout)
            movement_command_not_received = False
            return True
        elif time.time()-start_time > 4:
            if i < 3:
                print("POSE CMND RUN AGAIN")
                subprocess.run(pose_cmd, shell=True, capture_output=False, text=True)
                i = i+1
            else:
                # If mvmnt did not complete in 25 seconds,
                # Its probably done and we can move on
                print("WAIT POS SKIPPED")
                poll_obj.unregister(scan_process.stdout)
                movement_command_not_received = False
                return False
            start_time = time.time()
            #


def CombineTestandObjectName(test_name, object_name):
    return test_name + "_" + object_name

def TakeImage(folder_path, img_num):

    image_cmd = f"gz topic -t /TakeImg -m gz.msgs.Boolean -p 'data:True'"
    wait_cmd = f"gz topic -e -t /TakeImg"

    subprocess.run(image_cmd, shell=True, capture_output=False, text=True)
    time.sleep(3)
    start_time = time.time()
    while count_png_files(folder_path) < img_num + 1:
        if time.time() - start_time > 2:
            subprocess.run(image_cmd, shell=True, capture_output=False, text=True)
            start_time = time.time()


    #
    # scan_process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # poll_obj = select.poll()
    # poll_obj.register(scan_process.stdout, select.POLLIN)
    # take_img_msg_not_sent = True
    # while take_img_msg_not_sent:
    #     subprocess.run(image_cmd, shell=True, capture_output=False, text=True)
    #     poll_result = poll_obj.poll(0)
    #     if poll_result:
    #         line = scan_process.stdout.readline()
    #         # print(line)
    #         poll_obj.unregister(scan_process.stdout)
    #         take_img_msg_not_sent = False

def count_png_files(folder_path):
    # Use glob to find all .png files in the given folder
    png_files = glob.glob(f"{folder_path}/*.png")
    return len(png_files)

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
    # RoboDK movements relative to robot-arm flange (tool). Thus a remapping has to be done.
    # See Masters Book p118
    df['cumulative_x'] = initial_pose['X'] - df['X'].cumsum()
    df['cumulative_y'] = initial_pose['Y'] - df['Y'].cumsum()
    df['cumulative_z'] = initial_pose['Z'] + df['Z'].cumsum()
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