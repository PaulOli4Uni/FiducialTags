import os

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import glob

"""
disp_img -> Boolean to print values of image as well as show image.
"""
decimal = 4   # n decimal to round print and return value

def extract_aruco_pose(image_path, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img):
    # Load the image
    image = cv2.imread(image_path)

    # Initialize the ArUco detector
    parameters = cv2.aruco.DetectorParameters_create()
    aruco_dict = cv2.aruco.Dictionary_get(dictionary)

    # Detect ArUco markers in the image
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, aruco_dict, parameters=parameters)

    if ids is not None and target_marker_id in ids:
        # Find the index of the target marker
        target_marker_index = np.where(ids == target_marker_id)[0][0]

        # Estimate the pose of the target marker
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers([corners[target_marker_index]], marker_length,
                                                              camera_matrix, dist_coeffs)

        # Draw the detected ArUco marker and its axes
        cv2.aruco.drawAxis(image, camera_matrix, dist_coeffs, rvecs[0], tvecs[0], marker_length)
        cv2.aruco.drawDetectedMarkers(image, corners)

        R, _ = cv2.Rodrigues(rvecs)
        pose_mark_rel_cam = np.concatenate((R, tvecs.reshape(-1, 1)), axis=1)
        pose_mark_rel_cam = np.vstack((pose_mark_rel_cam, [0, 0, 0, 1]))
        # pose_cam_rel_mark = np.linalg.inv(pose_mark_rel_cam)

        # print(f"Position: {np.around(pose_mark_rel_cam[:3, 3], decimals=decimal)} Rotation: {np.around(Rotation.from_matrix(pose_mark_rel_cam[:3, :3]).as_euler('XYZ', degrees=True), decimals=decimal)}")
        # print(f"Position: {np.around(pose_cam_rel_mark[:3, 3], decimals=decimal)} Rotation: {np.around(Rotation.from_matrix(pose_cam_rel_mark[:3, :3]).as_euler('XYZ', degrees=True), decimals=decimal)}")
        # print(tvecs)

        rot_mat_seq = 'xyz'
        if (disp_img):
            print(f"Position: {np.around(pose_mark_rel_cam[:3, 3], decimals=decimal)} Rotation: {np.around(Rotation.from_matrix(pose_mark_rel_cam[:3, :3]).as_euler(rot_mat_seq, degrees=True), decimals=decimal)}")
            # Display the image with the detected marker and its axes
            display_resized_image(image)
            cv2.waitKey(1)

        return np.concatenate([np.around(pose_mark_rel_cam[:3, 3], decimals=decimal),
                               np.around(Rotation.from_matrix(pose_mark_rel_cam[:3, :3]).as_euler(rot_mat_seq, degrees=True),
                                         decimals=decimal)])
    else:
        if (disp_img):
            print(f"Marker with ID {target_marker_id} not found in the image.")
        return False
def display_resized_image(image):
    # Get the original image dimensions
    height, width = image.shape[:2]

    # Determine the desired width and height for resizing
    desired_width = width // 5
    desired_height = height // 5

    # Resize the image while maintaining the aspect ratio
    if width > height:
        new_width = desired_width
        new_height = int(desired_width * (height / width))
    else:
        new_height = desired_height
        new_width = int(desired_height * (width / height))

    resized_image = cv2.resize(image, (new_width, new_height))

    # Display the resized image
    cv2.imshow("Resized Image", resized_image)
    cv2.waitKey(1)
def compare_arrays(arr1, arr2, value):
    # Compare the values at indexes 3, 4, and 5. Takes into account the wraparound at 180 degrees to -180
    diff = np.abs((arr1[3:6] - arr2[3:6] + 180) % 360 - 180)

    # Check if any of the differences are greater than 20
    return np.any(diff > value)
def number_in_list(number, num_list):
    return number in num_list

#  Function to check all images in the folder. Returns an error if img is missing or duplicate found
def Check_All_Images(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img):

    images = glob.glob(img_dir + '*' + img_ext)  # Image DIR and type

    start_img = 611 # Normal start is 1
    start_img = (start_img // 7) * 7
    # exception_list = [65,66,109,110,115,116,126,127,132,133,134,135] #  10
    # exception_list = [225] # 9
    exception_list = []
    """
    Exemptions for different libraries. Ideal libraries: 2, 7, 1
    Canon Img:
        - 1: exception_list = [65]
        - 3: exception_list = [431]
        - 6: exception_list = [205]
        - 7: exception_list = [39, 128]
        - 8: exception_list = [65, 135, 158]
        - 10: exception_list = [88]
    Simulated Img:
        - 1: 
    """

    img_sequence = 0
    error_found = False

    for i in range(len(images) - start_img):
        current_img = i + start_img + 1
        print(f"Analysing img: {current_img}")

        dir = img_dir + str(current_img) + img_ext
        new_pose = extract_aruco_pose(dir, dictionary, marker_length, camera_matrix, dist_coeffs,
                                      target_marker_id, disp_img)

        if img_sequence == 0:  # First Run through.
            img_sequence = 1  # Next img in sequence will be img 2
        elif img_sequence == 1:
            if compare_arrays(prev_pose, new_pose, 20):
                print("Init Centre Missed")
                error_found = True
        elif img_sequence == 2:
            if not new_pose[4] < prev_pose[4] - 15:
                print("Rot Left Back Missed")
                error_found = True
        elif img_sequence == 3:
            if not new_pose[4] > prev_pose[4] + 40:
                print("Rot Right Back Missed")
                error_found = True
        elif img_sequence == 4:
            if not new_pose[4] < prev_pose[4] - 15:
                print("Mid Centre Missed")
                error_found = True
        elif img_sequence == 5:
            if not new_pose[5] > prev_pose[5] + 20:
                print("Rot Anti-Clock Missed")
                error_found = True
        elif img_sequence == 6:
            if not new_pose[5] < prev_pose[5] - 50:
                print("Rot Clock Missed")
                error_found = True
        elif img_sequence == 7:
            if not new_pose[5] > prev_pose[5] + 20:
                print("Fin Centre Missed")
                error_found = True
            img_sequence = 0  # Reset sequence

        if number_in_list(current_img, exception_list):
            print("Image Exempted for test")
            error_found = False

        if error_found:
            break

        img_sequence = img_sequence + 1
        prev_pose = new_pose
def Store_Img_Poses(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img):
    # Return file with pose extracted from markers
    images = glob.glob(img_dir + '*' + img_ext)  # Image DIR and type

    # Open the text file for writing (will create the file if it doesn't exist)
    filename = f"{img_dir}ID{target_marker_id}.txt"
    with open(filename, "w") as file:
        for i in range(len(images)):
            img_num = i+1
            print(f"Storing Pose Img{img_num}")
            dir = img_dir + str(img_num) + img_ext
            new_pose = extract_aruco_pose(dir, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id,
                                          disp_img)

            # Append the new_pose vector to the file
            file.write(" ".join(map(str, new_pose)) + "\n")

def Store_ALL_Img_Poses(main_img_dir, img_ext, dictionary, marker_lengths, camera_matrix, dist_coeffs, target_marker_ids, disp_img):

    for i in range(10):
        img_folder = i+1
        print(f"Working on Image Foler: {img_folder}")
        img_dir = f'{main_img_dir}/{img_folder}/'
        for j, target_marker_id in enumerate(target_marker_ids):
            print(f"ID:{target_marker_id}")
            Store_Img_Poses(img_dir, img_ext, dictionary, marker_lengths[j], camera_matrix, dist_coeffs, target_marker_id, disp_img)

if __name__ == "__main__":

    frameSize = (6000, 4000)
    dictionary = cv2.aruco.DICT_4X4_50  # Change this to the desired ArUco dictionary

    """
    =====================================================================
    --------------------  Real Images  ------------------ 
    """
    # Define the camera calibration matrix and distortion coefficients
    # REAL LIFE CANON Paramaters
    camera_matrix = np.array([[5163.89688, 0, 2962.82638],
                              [0, 5167.8757, 1953.23275],
                              [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.array([-0.593814060, -0.944836279, 0.000386026987, 0.000229657933, 4.02247968], dtype=np.float32)
    marker_length = 0.05  # Change this to the actual marker size in meters
    target_marker_id = 0
    # Change this to the ID of the marker you want to detect
    disp_img = False

    # --Check All Photos
    # img_dir = '/home/paul/Sim_Analysis/Verification/Phys_Test_Images/1/'
    # img_ext = '.JPG'
    # Check_All_Images(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)

    # --Extract Pose -> Single Image
    img_dir = '/home/paul/Sim_Analysis/Verification/Phys_Test_Images/Init_Pos_Img_OG_Names/1.JPG'
    a = extract_aruco_pose(img_dir, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)
    print(a)
    # --Extract Pose and Store -> Single folder
    # img_dir = "/home/paul/Sim_Analysis/Verification/Phys Test Images/Init_Pos_Img/"
    # img_ext = '.JPG'
    # Store_Img_Poses(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)

    # --Extract Pose and Store -> Multiple Folders
    # main_img_dir = '/home/paul/Sim_Analysis/Verification/Phys_Test_Images'
    # img_ext = '.JPG'
    # target_marker_ids = [0, 1, 2]
    # marker_lengths = [0.05, 0.05, 0.1]
    # Store_ALL_Img_Poses(main_img_dir, img_ext, dictionary, marker_lengths, camera_matrix, dist_coeffs, target_marker_ids, disp_img)

    """
    =====================================================================
    --------------------  Simulated Images  ------------------ 
    """
    # SIM CAMERA CANON Parameters
    camera_matrix = np.array([[float('5.15857116e+03'), 0, float('3.00643545e+03')],
                              [0, float('5.15993280e+03'), float('2.00218961e+03')],
                              [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.array([float('-4.88179779e-04'), float('-7.65892118e-03'),  float('7.22588876e-05'), float('4.54385455e-05'), float('2.54934851e-02')], dtype=np.float32)

    marker_length = 0.1  # Change this to the actual marker size in meters
    target_marker_id = 2  # Change this to the ID of the marker you want to detect
    disp_img = False

    # --Check All Photos
    # img_dir = '/home/paul/Sim_Analysis/Verification/Sim_Test_Images/1/1.png'
    # Check_All_Images(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)

    # --Extract Pose -> Single Image
    # img_dir = "/home/paul/Sim_Analysis/Verification/Sim_Test_Images/6/6.png"
    # a = extract_aruco_pose(img_dir, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)
    # print(a)

    # --Extract Pose and Store -> Single folder
    # img_dir = "/home/paul/Sim_Analysis/Verification/Sim_Test_Images/1/"
    # img_ext = '.png'
    # Store_Img_Poses(img_dir, img_ext, dictionary, marker_length, camera_matrix, dist_coeffs, target_marker_id, disp_img)

    # --Extract Pose and Store -> Multiple Folders
    # main_img_dir = "/home/paul/Sim_Analysis/Verification/Sim_Test_Images"
    # img_ext = '.png'
    # target_marker_ids = [0, 1, 2]
    # marker_lengths = [0.05, 0.05, 0.1]
    # Store_ALL_Img_Poses(main_img_dir, img_ext, dictionary, marker_lengths, camera_matrix, dist_coeffs, target_marker_ids, disp_img)



