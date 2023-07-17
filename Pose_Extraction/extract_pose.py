import time

import cv2
import numpy as np
from scipy.spatial.transform import Rotation

# Load the video file
video_file = 'vid_KahnPhone_cam_basic.mp4'
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
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

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
    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if len(corners) > 0:
        # Estimate the pose of each marker
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, dist_coeffs)

        for i in range(len(ids)):
            # Draw a bounding box around the marker
            cv2.aruco.drawDetectedMarkers(frame, corners)
            # cv2.aruco.drawAxis(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_size)

            frame = cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_size)
            # cv2.aruco.drawAxis(frame, matrix_coefficients, distortion_coefficients, rvec, tvec, 0.01)

            # Calculate the rotation matrix
            R, _ = cv2.Rodrigues(rvecs[i])
            r = Rotation.from_matrix(R)

            # print(R)
            print(tvecs[i])
            marker_pos = np.zeros((3,1))
            marker_rot = np.zeros((3,1))

            cam_pos = tvecs[i].transpose() + R@marker_pos
            cam_pos = cam_pos.transpose()
            cam_rot = r.as_euler('xyz') + marker_rot.transpose()

            #c = np.concatenate((a, b.reshape(-1, 1)), axis=1)
            #c = np.vstack((c, [0, 0, 0, 1]))

            Ex = np.concatenate((R, tvecs[i].reshape(-1, 1)), axis=1)
            marker_pose = np.vstack((Ex, [0, 0, 0, 1]))
            # print(cam_rot)

            # # Calculate the camera pose relative to the marker
            # marker_pose = np.hstack((R, tvecs[i]))
            # marker_pose = np.vstack((marker_pose, [0, 0, 0, 1]))
            camera_pose = np.linalg.inv(marker_pose)
            #
            # # Extract the translation and rotation components
            translation = camera_pose[:3, 3]
            rotation = cv2.Rodrigues(camera_pose[:3, :3])[0]
            print("Translation from linalg")
            print(translation)


            # Display the tag ID and pose information
            tag_id = ids[i][0]
            # label = f"Tag ID: {tag_id}, Pose: T={translation}, R={rotation}"
            label = f"Tag ID: {tag_id}, Pose: T={marker_pos}, R={marker_rot}"
            cv2.putText(frame, label, (int(corners[i][0][0][0]), int(corners[i][0][0][1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)

            label = f"Cam Pos: {cam_pos} Cam rot: {cam_rot}"
            cv2.putText(frame, label, (0, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 125, 125), 1, cv2.LINE_AA)

    # Show the frame
    cv2.imshow('Pose Estimation', frame)
    time.sleep(1)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
