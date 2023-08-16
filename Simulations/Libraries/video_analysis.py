import os
import cv2
import numpy as np
from scipy.spatial.transform import Rotation

ARUCO_DICT = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
    "DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
    "DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
    "DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
    "DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}



def AnalyseVideo(main_config, tests_config):

    for test_config in tests_config:
        world_name = main_config.world_file[:-4]
        test_name = test_config.test_name

        capture_pose = test_config.vid_pose_file
        capture_marker_corner = test_config.marker_corner_file

        print(f"[INFO] Analysing Video of test: {test_name}")

        test_dir = os.path.join(main_config.test_files_path, "Tests", test_config.test_name)
        if not os.path.exists(test_dir):  # Check if test dir exists
            print("[ERR] " + test_name + " test does not exist. Skipping")
            continue

        pose_dir = os.path.join(test_dir, "marker_pose")
        if capture_pose:
            if not os.path.exists(pose_dir):
                os.mkdir(pose_dir)
        else:
            print(f"[INFO] For {test_name}, not capturing pose info")

        marker_corner_dir = os.path.join(test_dir, "marker_corners")
        if capture_marker_corner:
            if not os.path.exists(os.path.join(marker_corner_dir)):
                os.mkdir(marker_corner_dir)
        else:
            print(f"[INFO] For, {test_name} not capturing marker area")

        # Create dictionary to store all marker info for the specific test.
        marker_info_by_dict = {}

        for marker in test_config.markers:
            dictionary = marker.dictionary
            id = marker.id
            size = marker.size
            pose = marker.pose

            if dictionary not in marker_info_by_dict:
                marker_info_by_dict[dictionary] = []

            marker_info_by_dict[dictionary].append((id, size, pose))

        # -- Video file for each camera used in the test (some cameras record with more than one lens)
        for camera in test_config.cameras:
            camera_name = camera.camera_file[:-4]

            if test_config.video_file:
                topic_names = camera.config.get_all_topic_names()
                for topic_name in topic_names:
                    video_name = f"vid_{camera_name}_{topic_name}"
                    video_file = f"{video_name}.mp4"
                    video_file_dir = os.path.join(test_dir, video_file)

                    if not os.path.exists(video_file_dir):
                        print("[ERR] video" + video_file_dir + " does not exist. Skipping test")
                        continue
                    else:

                        if capture_pose:
                            marker_files = create_marker_files(test_config.markers,
                                                               pose_dir, video_name, "poses")
                            _ExtractPoseFromVideo(video_file_dir, video_name, marker_info_by_dict, marker_files)

                        if capture_marker_corner:
                            marker_files = create_marker_files(test_config.markers,
                                                               marker_corner_dir, video_name, "corners")
                            _ExtractMarkerCornersFromVideo(video_file_dir, video_name, marker_info_by_dict, marker_files)

def _ExtractPoseFromVideo(video_file, video_name, marker_info_by_dict, marker_files):

    print("[INFO] Extracting pose")

    cap = cv2.VideoCapture(video_file)

    aruco_dicts = list(marker_info_by_dict.keys())

    # Define the camera matrix (replace with your own values)
    camera_matrix = np.array([[1188.3078, 0, 638.71195], [0, 1188.66076, 355.72245], [0, 0, 1]], dtype=np.float32)

    # Define the distortion coefficients (replace with your own values)
    dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    output_video_path = video_file[:-4] + "_edit.mp4"  # Specify the desired output video path
    framerate = float(24)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame = (1280, 720)
    # Width then height
    output_video = cv2.VideoWriter(output_video_path, fourcc, framerate, (frame[0], frame[1]))


    while cap.isOpened():

        ret, frame = cap.read()
        if not ret:
            break


        # Detect markers in the frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # parameters = cv2.aruco.DetectorParameters()  # PC
        parameters = cv2.aruco.DetectorParameters_create()  # Laptop
        current_time = cap.get(cv2.CAP_PROP_POS_FRAMES) / cap.get(cv2.CAP_PROP_FPS)

        for idx, aruco_dict_str in enumerate(aruco_dicts):

            aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_dict_str])

            corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)



            if len(corners) > 0:
                for i, id in enumerate(ids):

                    # Estimate the pose of each marker
                    marker_size, pose = get_size_and_pose(aruco_dict_str, float(id), marker_info_by_dict)

                    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, dist_coeffs)

                    # Draw a bounding box around the marker
                    cv2.aruco.drawDetectedMarkers(frame, corners)
                    frame = cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_size)


                    marker_pos = np.array([pose.X, pose.Y, pose.Z])
                    marker_rot = np.array([pose.r, pose.p, pose.y])  # In Radians
                    R_marker = Rotation.from_euler('XYZ', marker_rot, degrees=False).as_matrix()

                    marker_pose = np.concatenate((R_marker, marker_pos.reshape(-1, 1)), axis=1)
                    marker_pose = np.vstack((marker_pose, [0, 0, 0, 1]))

                    # Calculate pose between markers and cameras
                    R, _ = cv2.Rodrigues(rvecs[i])
                    pose_mark_rel_cam = np.concatenate((R, tvecs[i].reshape(-1, 1)), axis=1)
                    pose_mark_rel_cam = np.vstack((pose_mark_rel_cam, [0, 0, 0, 1]))
                    pose_cam_rel_mark = np.linalg.inv(pose_mark_rel_cam)
                    #
                    # # Extract the translation and rotation components
                    # print(camera_pose*marker_pos)
                    pose_cam_world = marker_pose@pose_cam_rel_mark
                    pos_cam_world = pose_cam_world[:3,3]

                    rot_cam_world = np.deg2rad(cv2.RQDecomp3x3(pose_cam_world[:3, :3])[0])


                    R_remap = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
                    t_remap = np.concatenate((R_remap, np.array([[0],[0],[0]])), axis=1)
                    t_remap = np.vstack((t_remap, [0, 0, 0, 1]))

                    remap_pose = marker_pose  @ (t_remap @ pose_cam_rel_mark)

                    remap_rot = np.around(Rotation.from_matrix(remap_pose[:3,:3]).as_euler('XYZ', degrees=True))
                    remap_rot[2] = remap_rot[2] + 90
                    if remap_rot[2] > 180:
                        remap_rot[2] = remap_rot[2] - 360

                    # Remapping end ------------------------------
                    marker_name = aruco_dict_str + "_s" + str(int(marker_size*1000)) + "_id" + str(id)
                    lbl_marker_name = f"Marker ID: {marker_name}"
                    lbl_marker_pose = f"Marker Pos: {np.around(marker_pos, decimals=2)} Cam rot: {np.around(marker_rot, decimals=2)}"  # Print in Deg
                    lbl_marker_rel_cam = f"Marker relative Cam: {np.around(pose_mark_rel_cam[:3,3], decimals=2)} Cam rot: {np.around(Rotation.from_matrix(pose_mark_rel_cam[:3,:3]).as_euler('XYZ', degrees=True), decimals=2)}"
                    lbl_cam_rel_marker = f"Cam relative Marker: {np.around(pose_cam_rel_mark[:3,3], decimals=2)} Cam rot: {np.around(Rotation.from_matrix(pose_cam_rel_mark[:3,:3]).as_euler('XYZ', degrees=True), decimals=2)}"
                    lbl_cam_glob_pose = f"Global Cam Pos: {np.around(pos_cam_world, decimals=2)} Cam rot: {np.rad2deg(np.around(rot_cam_world, decimals=2))}"
                    lbl_remap = f"Remapped Cam Pos: {np.around(remap_pose[:3,3], decimals=2)} Cam rot: {remap_rot}"

                    # print("New Frame (all angles in deg")
                    # print(lbl_marker_pose)
                    # print(lbl_marker_rel_cam)
                    # print(lbl_cam_rel_marker)
                    # print(lbl_cam_glob_pose)
                    # print(lbl_remap)

                    # Display the tag ID and pose information
                    cv2.putText(frame, lbl_marker_name, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 35)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                    cv2.putText(frame, lbl_marker_pose, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                    cv2.putText(frame, lbl_remap, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                    # cv2.putText(frame, lbl_cam_glob_pose, (0, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                    # cv2.putText(frame, lbl_remap, (0, 25*(idx+1)*(i+1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)

                    marker_info = (aruco_dict_str, int(id), video_name)
                    file_handler = marker_files[marker_info]

                    write_pose_to_file(file_handler, remap_pose[:3,3], remap_rot, current_time)

            # Show the frame
            cv2.imshow('Pose Estimation', frame)
            output_video.write(frame)

        #

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    output_video.release()

def get_size_and_pose(dictionary, id, marker_info_by_dict):
    if dictionary in marker_info_by_dict:
        marker_info_list = marker_info_by_dict[dictionary]
        for marker_id, size, pose in marker_info_list:
            if marker_id == id:
                return size, pose
    return None, None

def create_marker_files(markers, file_dir, video_name, data_identifier):
    marker_files = {}
    for marker in markers:
        dictionary = marker.dictionary
        marker_id = marker.id
        file_name = f"marker_{dictionary}_{marker_id}_{video_name}_{data_identifier}.txt"
        file_path = os.path.join(file_dir, file_name)

        if os.path.exists(file_path):
            # If the file exists, clear its content by opening it in write mode with 'w'
            file_handler = open(file_path, "w")
        else:
            # If the file does not exist, create it by opening it in write mode with 'x'
            file_handler = open(file_path, "x")

        marker_files[(dictionary, marker_id, video_name)] = file_handler
    return marker_files

def write_pose_to_file(file_handler, position, orientation, current_time):
    pose_info = f"{position[0]},{position[1]},{position[2]},{orientation[0]},{orientation[1]},{orientation[2]},{current_time}\n"
    file_handler.write(pose_info)


def _ExtractMarkerCornersFromVideo(video_file, video_name, marker_info_by_dict, marker_files):

    print("[INFO] Extracting marker corners")

    cap = cv2.VideoCapture(video_file)
    aruco_dicts = list(marker_info_by_dict.keys())

    # Define the camera matrix (replace with your own values)
    camera_matrix = np.array([[1188.3078, 0, 638.71195], [0, 1188.66076, 355.72245], [0, 0, 1]], dtype=np.float32)

    # Define the distortion coefficients (replace with your own values)
    dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    framerate = float(24)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame = (1280, 720)



    while cap.isOpened():

        ret, frame = cap.read()
        if not ret:
            break

        # Detect markers in the frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # parameters = cv2.aruco.DetectorParameters()  # PC
        parameters = cv2.aruco.DetectorParameters_create()  # Laptop
        current_time = cap.get(cv2.CAP_PROP_POS_FRAMES) / cap.get(cv2.CAP_PROP_FPS)

        for idx, aruco_dict_str in enumerate(aruco_dicts):

            aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_dict_str])
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

            if len(corners) > 0:
                for i, id in enumerate(ids):

                    marker_size, pose = get_size_and_pose(aruco_dict_str, float(id), marker_info_by_dict)
                    marker_name = aruco_dict_str + "_s" + str(int(marker_size * 1000)) + "_id" + str(id)
                    marker_info = (aruco_dict_str, int(id), video_name)
                    file_handler = marker_files[marker_info]

                    write_corners_to_file(file_handler, corners[0][0], current_time)

            # Show the frame
            # cv2.imshow('Marker Area', frame)


        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    # cap.release()
    # cv2.destroyAllWindows()

def write_corners_to_file(file_handler, corners, current_time):
    pose_info = f"{corners[0]},{corners[1]},{corners[2]},{corners[3]},{current_time}\n"
    file_handler.write(pose_info)
