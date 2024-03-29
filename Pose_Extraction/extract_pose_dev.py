import time

import cv2
import numpy as np
from scipy.spatial.transform import Rotation

# Load the video file
# video_file = 'vid_KahnPhone_cam_basic.mp4'
# video_file = 'vid_KahnPhone_rotation.mp4'
# video_file = 'vid_KahnPhone_rotate_displaced.mp4'

# video_file = 'vid_KahnPhone_new_cam_basic.mp4'
# video_file = 'lin.mp4'
video_file = 'rool_and_pitch.mp4'
# video_file = 'rotation_new_marker.mp4'
# video_file = 'rotation_new_marker_new.mp4'
video_file = 'fast.mp4'
video_file = 'mult_markers.mp4'
video_file = 'mult_dict.mp4'

cap = cv2.VideoCapture(video_file)

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

# Load the ArUco dictionary
# aruco_dicts = ["DICT_4X4_50", "DICT_5X5_50"]
aruco_dicts = ["DICT_5X5_50", "DICT_4X4_50"]
# aruco_dicts = [cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_dicts[0]]), cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_dicts[1]])]

# Define the marker size in meters
marker_size = 0.1

# Define the camera matrix (replace with your own values)
camera_matrix = np.array([[1188.3078, 0, 638.71195], [0, 1188.66076, 355.72245], [0, 0, 1]], dtype=np.float32)

# Define the distortion coefficients (replace with your own values)
dist_coeffs = np.zeros((4, 1), dtype=np.float32)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detect markers in the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    parameters = cv2.aruco.DetectorParameters()

    for idx, aruco_dict_str in enumerate(aruco_dicts):

        aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[aruco_dict_str])

        corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if len(corners) > 0:
            # Estimate the pose of each marker
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, dist_coeffs)

            for i, id in enumerate(ids):



                # Draw a bounding box around the marker
                cv2.aruco.drawDetectedMarkers(frame, corners)
                frame = cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_size)

                marker_pos = np.array([5, 7, 10])
                marker_rot = np.array([0, 0, 0])  # In Degrees
                R_marker = Rotation.from_euler('XYZ', marker_rot, degrees=True).as_matrix()

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

                lbl_marker_pose = f"Marker Id: {aruco_dict_str + str(id)}, Pose: {np.around(marker_pos, decimals=2)} Cam rot: {np.around(marker_rot, decimals=2)}"  # Print in Deg
                lbl_marker_rel_cam = f"Marker relative Cam: {np.around(pose_mark_rel_cam[:3,3], decimals=2)} Cam rot: {np.around(Rotation.from_matrix(pose_mark_rel_cam[:3,:3]).as_euler('XYZ', degrees=True), decimals=2)}"
                lbl_cam_rel_marker = f"Cam relative Marker: {np.around(pose_cam_rel_mark[:3,3], decimals=2)} Cam rot: {np.around(Rotation.from_matrix(pose_cam_rel_mark[:3,:3]).as_euler('XYZ', degrees=True), decimals=2)}"
                lbl_cam_glob_pose = f"Global Cam Pos: {np.around(pos_cam_world, decimals=2)} Cam rot: {np.rad2deg(np.around(rot_cam_world, decimals=2))}"
                lbl_remap = f"Remapped Cam Pos: {np.around(remap_pose[:3,3], decimals=2)} Cam rot: {remap_rot}"

                print("New Frame (all angles in deg")
                print(lbl_marker_pose)
                print(lbl_marker_rel_cam)
                print(lbl_cam_rel_marker)
                print(lbl_cam_glob_pose)
                print(lbl_remap)

                # Display the tag ID and pose information
                tag_id = ids[i][0]
                cv2.putText(frame, lbl_marker_pose, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                # cv2.putText(frame, lbl_cam_glob_pose, (0, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)
                cv2.putText(frame, lbl_remap, (0, 100*(idx+1)*(i+1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)

        # Show the frame
        cv2.imshow('Pose Estimation', frame)
        time.sleep(0.5)
    #

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
