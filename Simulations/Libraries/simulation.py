import time
import subprocess
import os
from scipy.spatial.transform import Rotation
import shutil

from Simulations.Libraries import directory_mappings


tmp_movement_file_dir = 'tmp_files/tmp_file.txt'

def RunSim(main_config, tests_config):


    for test_config in tests_config:
        world_name = main_config.world_file[:-4]
        test_name = test_config.test_name
        print("[INFO] Strating test: " + test_name)
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
            LoadMarker(world_name, test_name, main_config.test_files_path, marker)

        for camera in test_config.cameras:
            LoadCamera(world_name, test_name, main_config.test_files_path, camera)

        for model in test_config.models:
            model_file = model.model_file
            path_to_model_file = directory_mappings.FilePathToModel(main_config.test_files_path, model_file)
            LoadModel(world_name, test_name, path_to_model_file, model_file[:-4], model.pose)


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
                RunPoseString(test_name, camera.camera_file[:-4], pose_message)

            PlaySim(world_name)
            WaitMovementComplete(test_name, test_config.cameras[0].camera_file[:-4])  # Only have to look at one camera
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
                StartCameraPoseCapture(test_name, camera_name, os.path.join(test_dir, gz_pose_file))

            RunPoseFile(test_name, camera_name, os.path.join(main_config.test_files_path, tmp_movement_file_dir))

        PlaySim(world_name)
        WaitMovementComplete(test_name, test_config.cameras[0].camera_file[:-4])  # Only have to look at one camera
        PauseSim(world_name)
        print("[INFO] Movement_file finished")

        # Remove Markers, Cameras and Models
        print("[INFO] Removing Markers and Cameras")
        for marker in test_config.markers:
            RemoveModel(world_name, test_name, marker.marker_file[:-4])
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
                StopCameraPoseCapture(test_name, camera_name, os.path.join(test_dir, gz_pose_file))

            RemoveModel(world_name, test_name, camera_name)

        for model in test_config.models:
            RemoveModel(world_name, test_name, model.model_file[:-4])
        # os.remove(os.path.join(main_config.test_files_path, tmp_movement_file_dir))  # Remove tmp_movement_file

    return True

def LoadMarker(world_name, test_name, main_path, marker_dc):

    path_to_marker_file = directory_mappings.FilePathToMarker(main_path, marker_dc.marker_file)
    LoadModel(world_name, test_name, path_to_marker_file, marker_dc.marker_file[:-4], marker_dc.pose)

def LoadCamera(world_name, test_name, main_path, camera_dc):

    camera_name = camera_dc.camera_file[:-4]
    path_to_camera_file = os.path.join(main_path, "Cameras", camera_dc.camera_file)

    LoadModel(world_name, test_name, path_to_camera_file, camera_name, camera_dc.pose)

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

def RunPoseString(test_name, model_name, pose_msg):

    pose_cmd = f"gz topic -t /model/{CombineTestandObjectName(test_name, model_name)}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
    result = subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)

def RunPoseFile(test_name, model_name, pose_file):

    pose_cmd = f"gz topic -t /model/{CombineTestandObjectName(test_name, model_name)}/file_pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_file}\"\'"
    result = subprocess.run(pose_cmd, shell=True, capture_output=True, text=True)

def StartCameraPoseCapture(test_name, model_name, gz_pose_file):

    pose_storage_start_cmd = f"gz service -s /model/{CombineTestandObjectName(test_name,model_name)}/PoseToFile --timeout 2000 --reqtype gz.msgs.VideoRecord " \
                       f"--reptype gz.msgs.Int32 --req \'start:true, stop:false, save_filename:\"{gz_pose_file}\"\'"
    # print(pose_storage_start_cmd)
    result = subprocess.run(pose_storage_start_cmd, shell=True, capture_output=True, text=True)
    # gz service -s /pose_to_file --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype gz.msgs.Int32 --req 'start:true, save_filename:"name.txt"'

def StopCameraPoseCapture(test_name, model_name, gz_pose_file):

    pose_storage_stop_cmd = f"gz service -s /model/{CombineTestandObjectName(test_name, model_name)}/PoseToFile --timeout 2000 --reqtype gz.msgs.VideoRecord " \
                       f"--reptype gz.msgs.Int32 --req \'start:false, stop:true, save_filename:\"{gz_pose_file}\"\'"
    # print(pose_storage_stop_cmd)
    result = subprocess.run(pose_storage_stop_cmd, shell=True, capture_output=True, text=True)

def StartCameraVideoRecord(model_name, video_file):

    camera_rcd_start_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:true, save_filename:\"{video_file}\"\'"
    print(camera_rcd_start_cmd)
    result = subprocess.run(camera_rcd_start_cmd, shell=True, capture_output=True, text=True)

def StopCameraVideoRecord(model_name, video_file):

    camera_rcd_stop_cmd = f"gz service -s /{model_name} --timeout 2000 --reqtype gz.msgs.VideoRecord --reptype " \
                     f"gz.msgs.Boolean --req \'start:false, save_filename:\"{video_file}\"\'"
    result = subprocess.run(camera_rcd_stop_cmd, shell=True, capture_output=True, text=True)

def WaitMovementComplete(test_name, model_name):

    wait_cmd = f"gz topic -e -t /model/{CombineTestandObjectName(test_name, model_name)}/move_fin "
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