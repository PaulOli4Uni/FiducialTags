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
"""
The following tasks can be completed
Task 1 -> Move marker around relative csv file, take images
Task 2 -> Move marker around relative csv file with time, take video
Task 3 -> Move Calibration pattern to 30 preset locations, take images 
"""
task = 2
marker_pose = dc_pose(0,0,1,np.deg2rad(0),np.deg2rad(0),np.deg2rad(0))
camera_pose = dc_pose(0.0,0,1+0.826+0.1198,np.deg2rad(-180),np.deg2rad(0),np.deg2rad(-180-.7))  ## Canon Vid START Pose

test_name = "test1"
marker_name = "3Markers"
# marker_name = "Pattern_Cropped_Gz"
# camera_name = "Canon"
camera_name = "Canon_Vid"

# ALL TASKS
# marker_pose = dc_pose(0,0,1,np.deg2rad(0),np.deg2rad(0),np.deg2rad(0))
# camera_pose = dc_pose(0.007,-0.0263,2.3198,np.deg2rad(-180-2.2752),np.deg2rad(0-2.4637),np.deg2rad(-180+0.7)) ## Canon, img start pose
# camera_pose = dc_pose(0.0+0.008,0-0.004,1+0.826+0.1198,np.deg2rad(-180),np.deg2rad(0),np.deg2rad(-180-.7))  ## Canon Vid START Pose
world_img_files_path = f"/home/paul/FiducialTags/Simulations/Worlds/{camera_name}"

# Tasks 1 and 2
# movement_file_dir = '../Verification/Kuka_Files/CSV_Files_for_Test/MovMatrix_10.csv'
movement_file_dir = '/home/paul/Sim_Analysis/Verification/Dynamic_Tests/vid_Test1_sim/true_pose_test1.csv'

# Do Not Change
camera_file_dir = '../Verification/Cameras/' + camera_name + '.sdf'
marker_file_dir = os.path.join('../Verification', marker_name, (marker_name+'.sdf'))
camera_config_file_dir = camera_file_dir[:-4] + "_config.txt"
world_name = 'standard_world'
test_files_path = '../Verification'
tmp_movement_file_dir = '/home/paul/FiducialTags/Simulations/tmp_files/tmp_file.txt'

# poses generated via CHAT-GPT -> necesarry commands given at the bottom of the file
calibration_poses = """
0.256,-0.121,0.456,12.4,34.9,-123.0,1.0
-0.289,0.389,0.754,-23.7,15.3,145.7,1.0
0.123,-0.402,0.898,20.2,-30.4,55.4,1.0
-0.147,0.233,0.857,8.9,22.6,-160.8,1.0
0.291,-0.112,0.312,-9.3,5.2,89.5,1.0
-0.125,0.401,1.254,42.8,49.5,-110.2,1.0
0.134,-0.237,0.697,-48.5,-4.2,46.1,1.0
-0.298,0.118,0.634,35.9,19.9,169.8,1.0
0.148,-0.445,0.783,51.7,-45.8,-134.3,1.0
-0.234,0.127,1.089,7.4,24.6,75.6,1.0
0.216,-0.309,0.957,32.4,-9.6,-30.1,1.0
-0.153,0.112,1.372,46.1,14.2,95.9,1.0
0.104,-0.188,0.583,-28.9,49.9,-101.4,1.0
-0.275,0.331,1.203,23.1,5.7,150.1,1.0
0.137,-0.215,0.412,-19.4,37.4,-120.4,1.0
-0.088,0.294,0.867,36.2,-28.9,130.5,1.0
0.145,-0.244,0.512,10.6,45.1,-159.2,1.0
-0.143,0.318,1.156,-40.9,23.4,89.7,1.0
0.125,-0.212,0.768,48.3,-50.2,60.4,1.0
-0.111,0.243,0.949,-15.7,33.5,-170.3,1.0
0.299,-0.227,0.398,39.6,-18.2,140.8,1.0
-0.285,0.218,1.239,22.8,28.3,-85.9,1.0
0.117,-0.126,0.857,-30.6,50.7,111.2,1.0
-0.106,0.207,0.617,14.3,-46.4,-45.3,1.0
0.132,-0.249,1.473,-50.1,9.3,123.7,1.0
-0.088,0.289,0.359,5.8,14.7,-160.5,1.0
0.147,-0.198,0.784,-29.1,37.3,150.9,1.0
-0.123,0.145,1.411,52.6,-21.4,-79.2,1.0
0.128,-0.232,0.484,-44.5,53.8,105.3,1.0
-0.114,0.117,1.199,18.1,-14.6,-150.6,1.0
"""
def RunSim1():

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

def RunSim2():

    print("[INFO] Starting test: " + test_name)
    test_dir = os.path.join(test_files_path, "Tests", test_name)
    print("[INFO] Making directory for test results at: \'" + test_dir + "\'")
    # os.makedirs(test_dir)
    if not os.path.exists(test_dir):  # Create the directory
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

    # REMAP CSV FILE FOR SIMULATIONS

    process_csv_file_video(movement_file_dir, marker_pose,tmp_movement_file_dir)
    # Prep Movement File (if time of first line = 0) set separate and create temp file for other commands
    pose_message = LoadPoseMovementFile(tmp_movement_file_dir, tmp_movement_file_dir)
    if pose_message:
        print("[INFO] Moving MARKER to starting position")
        print(pose_message)
        RunPoseString(test_name, marker_name, pose_message.rstrip())

        PlaySim(world_name)
        WaitMovementComplete_PoseFile(test_name, marker_name)
        PauseSim(world_name)

    print("[INFO] Starting Movement File")
    RunPoseFile(test_name, marker_name, tmp_movement_file_dir)
    camera_topic = "cam_basic"
    StartCameraVideoRecord(camera_topic, world_img_files_path+"/vid.mp4")
    PlaySim(world_name)
    WaitMovementComplete_PoseFile(test_name, marker_name)
    PauseSim(world_name)
    StopCameraVideoRecord(camera_topic, world_img_files_path+"/vid.mp4")
    print("[INFO] Movement File Finished")
    # Remove Markers, Cameras and Models
    print("[INFO] Removing Markers and Cameras")
    RemoveModel(world_name, test_name, marker_name)
    RemoveModel(world_name, test_name, camera_name)

    return True
def RunSim3():

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
    # all_movement_cmds = process_csv_file(movement_file_dir, marker_pose, t=.6)
    print("[INFO] Starting Movement File")
    PlaySim(world_name)

    for img_num, move_cmd in enumerate(calibration_poses.strip().splitlines()):
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
def process_csv_file_video(csv_filename, initial_pose, txt_filename):
    # Read the CSV file into a DataFrame
    initial_pose = {'X': initial_pose.X, 'Y': initial_pose.Y, 'Z': initial_pose.Z, 'r': initial_pose.r, 'p': initial_pose.p, 'y': initial_pose.y}
    # Define column names
    columns = ['X', 'Y', 'Z', 'r', 'p', 'y', 'time']

    # Read the CSV file into a DataFrame with explicitly defined column names
    df = pd.read_csv(csv_filename, names=columns)
    # Initialize the new DataFrame with the initial pose
    df_new = pd.DataFrame(index=df.index, columns=['x', 'y', 'z', 'roll', 'pitch', 'yaw', 'time'])
    # Calculate the cumulative sum for translations (x, y, z) and rotations (r, p, y)
    # RoboDK movements relative to robot-arm flange (tool). Thus a remapping has to be done.
    # See Masters Book p118
    # df_new['x'] = initial_pose['X'] - df['X'].cumsum()
    # df_new['y'] = initial_pose['Y'] - df['Y'].cumsum()
    # df_new['z'] = initial_pose['Z'] - df['Z'].cumsum()
    # df_new['roll'] = np.rad2deg(initial_pose['r']) - df['r'].cumsum()
    # df_new['pich'] = np.rad2deg(initial_pose['p']) - df['p'].cumsum()
    # df_new['yaw'] = np.rad2deg(initial_pose['y']) -  df['y'].cumsum()
    # df_new['time'] = df['time']

    df_new['x'] = initial_pose['X'] - df['Y']
    df_new['y'] = initial_pose['Y'] - df['X']
    df_new['z'] = initial_pose['Z'] - df['Z']
    df_new['roll'] = np.rad2deg(initial_pose['r']) - df['p']
    df_new['pitch'] = np.rad2deg(initial_pose['p']) - df['r']
    df_new['yaw'] = np.rad2deg(initial_pose['y']) - df['y']
    df_new['time'] = df['time']
    df_new.to_csv(txt_filename, index=False, header=False, float_format='%.6f', sep=',')
    # return processed_data
def LoadPoseMovementFile(mvm_file_path,tmp_file_path):

    degrees = True

    with open(mvm_file_path, 'r') as file:
        lines = file.readlines()

    i = 0  # Used to keep track of the first line (dep on 'degree=xxx' present or not in text file)
    first_line = lines[i].strip()
    # See if conversion to degrees is necesarry
    if first_line.startswith('degrees='):
        degrees_str = first_line.split('=')[1].strip().lower()
        if degrees_str == 'true':
            degrees = True
        i = 1

    first_line = lines[i].rstrip()
    last_number = float(first_line.split(',')[-1])

    if last_number == 0.0:

        tmp_lines = lines[i+1:]

        WritePoseTmpfile(tmp_file_path, tmp_lines)

        # Change time of last line to 1 second before returning pose command
        initial_pose_cmd = first_line.split(',')
        last_number_index = len(initial_pose_cmd) - 1
        initial_pose_cmd[last_number_index] = '1'

        initial_pose_cmd = ','.join(initial_pose_cmd)

        if not degrees:
            initial_pose_cmd = ConvertLineRad2Deg(initial_pose_cmd)

        return initial_pose_cmd
    else:
        tmp_lines = lines[i:]
        WritePoseTmpfile(tmp_file_path, tmp_lines)
        # print(f"Temporary file '{tmp_filename}' created.")
        return False
def WritePoseTmpfile(tmp_file_path, lines):

    with open(tmp_file_path, 'w') as tmp_file:
            tmp_file.writelines(lines)
def WaitMovementComplete_PoseFile(test_name, model_name):

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
def RunPoseFile(test_name, model_name, pose_file):

    pose_cmd = f"gz topic -t /model/{CombineTestandObjectName(test_name, model_name)}/file_pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_file}\"\'"
    result = subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)
def StartCameraVideoRecord(model_name, video_file):

    camera_rcd_start_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:true, save_filename:\"{video_file}\"\'"
    print(camera_rcd_start_cmd)
    result = subprocess.run(camera_rcd_start_cmd, shell=True, capture_output=True, text=True)

def StopCameraVideoRecord(model_name, video_file):
    camera_rcd_stop_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:false, save_filename:\"{video_file}\"\'"
    result = subprocess.run(camera_rcd_stop_cmd, shell=True, capture_output=True, text=True)


"""
<plugin
                    filename="Take_Image"
                    name="gz::sim::v7::systems::TakeImages">
                    <service>cam_basic</service>
                    <path>/home/paul/FiducialTags/Simulations/Worlds/Canon_Vid</path>
                </plugin>
"""

if task == 1:
    RunSim1()
elif task == 2:
    RunSim2()
elif task == 3:
    RunSim3()



"""
CHAT GPT INFO TO GENERATE calibration_poses

generate text that i can paste into a csv file. The information is in the form x,y,z,r,p,y,t
where x,y,z are all coordinates in meters, and should be randomly assigned with the following limitations
-0.3<x<0.3
-0.45<y<0.45
+0.1<z<+1.5

after z > 0.9
make the new x and y paramaters
he list with the following new parameters
-0.15<x<0.15
-0.25<y<0.25

r,p,y are all orientations in degrees and should be limited as follow

-55<r<55
0-55<p<55
-170<y<170

t is a constant and should be 1.0
Generate around 30 lines
"""