"""
From: https://github.com/niconielsen32/ComputerVision/blob/37b279fa44e28fe3ea859bc8f14f5353a6b93e54/cameraCalibration.py#L4
"""
"""
Do the Following: (for each set of focal lengths, 18mm 35mm, 70mm)
    
    - Callibrate the camera with captured images
        -Return Cal Matrix
        -Return Dist Coeff
        -Return Focal_Length 
        -Return resolution
        -Return sensor_size
        -Return fov
        -Return UPA
    
    -Change resolution of calibration images to 1280x720; 1080x720; 480x360
        Repeat Process
        
"""
from PIL import Image
import numpy as np
import cv2 as cv
import glob
import os

# --------------------------------------- Properties ----------------------------

chessboardSize = (9, 6)
size_of_chessboard_squares_mm = 22.733

# ----------------------------------------------------------------------
################ FIND CHESSBOARD CORNERS - OBJECT POINTS AND IMAGE POINTS #############################
# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1, 2)
objp = objp * size_of_chessboard_squares_mm

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

    resized_image = cv.resize(image, (new_width, new_height))

    # Display the resized image
    cv.imshow("Resized Image", resized_image)
    cv.waitKey(1000)
def Calibrate_Camera(images, frameSize):
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    for i, image in enumerate(images):
        # print("Image: " + str(i) + "\t Dir: " + str(image))


        img = cv.imread(image)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, chessboardSize, None)

        # If found, add object points, image points (after refining them)
        if ret == True:

            objpoints.append(objp)
            corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners)

            # Draw and display the corners
            cv.drawChessboardCorners(img, chessboardSize, corners2, ret)
            # imS = cv.resize(img, (540,960))  # Resize image
            # cv.imshow("img", imS)
            # cv.imshow('img', img)
            # cv.waitKey(1000)
            display_resized_image(img)

    cv.destroyAllWindows()
    ############## CALIBRATION #######################################################

    ret, cameraMatrix, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, frameSize, None, None)
    # print("ret")
    # print(ret)

    print("Cam Mat")
    print(cameraMatrix)

    print("Dist")
    print(dist)

    # print("rvecs")
    # print(rvecs)

    # print("tvecs")
    # print(tvecs)

    return cameraMatrix, dist, ret, rvecs, tvecs


def Resize_Images(images, output_resolution, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for image_path in images:
        with Image.open(image_path) as img:
            # Calculate the target size maintaining the aspect ratio
            original_aspect = img.width / img.height
            target_aspect = output_resolution[0] / output_resolution[1]

            if original_aspect > target_aspect:
                # Original is wider than target aspect
                target_width = output_resolution[0]
                target_height = round(target_width / original_aspect)
            else:
                # Original is taller than target aspect
                target_height = output_resolution[1]
                target_width = round(target_height * original_aspect)

            # Resize the image
            img = img.resize((target_width, target_height), Image.ANTIALIAS)

            # Save to output directory
            base_name = os.path.basename(image_path)
            img.save(os.path.join(output_dir, base_name))

def Calc_FocalLength(beta,framesize,sensorsize):
    focallength = np.array([beta[0]*sensorsize[0]/framesize[0],beta[1]*sensorsize[1]/framesize[1]])
    print(f"FocalLength: {focallength}")
    return focallength

def Calc_SensorSize(beta,framesize, focallength):
    sensorSize = np.array( [framesize[0]*focallength/beta[0], framesize[1]*focallength/beta[1]] )
    print(f"SensorSize: {sensorSize}")
    return sensorSize

def Calc_fov(beta, framesize):
    fov = np.array([2*np.arctan2(framesize[0], 2 * beta[0]), 2*np.arctan2(framesize[1], 2 * beta[1])])
    print(f"fov: {fov}")
    return fov

def Calc_UPA(fov, framesize):
    UPA = 4*np.tan(fov[0]/(framesize[0]*2))*np.tan(fov[1]/(framesize[1]*2))
    print(f"UPA: {UPA}")
    return UPA
def Return_BetaFromCalibrationMatrix(calibration_matrix):
    beta = np.array([calibration_matrix[0,0], calibration_matrix[1,1]])
    print(f"beta: {beta}")
    return beta

def Print_CamProperties(calibration_matrix, dist_coeff, framesize, fov):
    cam_properties = f"""
topic_name: cam_basic
pose: 0 0 0 0 0 0
calibration_matrix: {','.join(map(str, calibration_matrix.flatten()))}
distortion_coeff: {','.join(map(str, dist_coeff.flatten()))}
horizontal_fov: {fov[0]}
img_width: {framesize[0]}
img_height: {framesize[1]}
clip_near: 0.1
clip_far: 50
lens_type: stereographic
cutoff_angle: 1.5707963267948966
framerate: 25"""
    print(cam_properties)

def Print_Distortion(dis_coeff):
    dis_string = f"""
<distortion>
<k1>{dis_coeff[0,0]}</k1>
<k2>{dis_coeff[0,1]}</k2>
<k3>{dis_coeff[0,2]}</k3>
<p1>{dis_coeff[0,3]}</p1>
<p2>{dis_coeff[0,4]}</p2>
<center>0.5 0.5</center>
</distortion>"""
    print(dis_string)

def Print_fovDeg(fov):
    print(f"fov [degrees]: {np.rad2deg(fov[0])},{np.rad2deg(fov[1])}")
# images = glob.glob('Canon_Vid_Sim/*.png')  # Image DIR and type

# Calibrate First Camera
frameSize = (6000, 4000)  # Img Resolution -Canon
sensorSize = (22.3,14.9)
focallength = 18
main_img_dir = 'f18'
extension = '.JPG'

print("Calibrating Initial Image Dir")

images = glob.glob(os.path.join(main_img_dir, '*'+extension))
calibration_matrix, dist, ret, tvecs, rvecs = Calibrate_Camera(images, frameSize)
beta = Return_BetaFromCalibrationMatrix(calibration_matrix)
fov = Calc_fov(beta, frameSize)
Calc_SensorSize(beta, frameSize, focallength)
Calc_FocalLength(beta,frameSize,sensorSize)
Calc_UPA(fov, frameSize)
Print_CamProperties(calibration_matrix, dist, frameSize, fov)
print('\n')
Print_Distortion(dist)

## Repeat Process for Other Cameras
resolutions = [(1080,720),(480,360)]
for frameSize in resolutions:
    res_name = ','.join(str(item) for item in frameSize)
    output_file = os.path.join(main_img_dir, res_name)
    print(f"\nResizing to resolution {frameSize}")
    Resize_Images(images, frameSize, output_file)

    # Read new images
    new_images = glob.glob(os.path.join(output_file, '*'+extension))
    print("Calibration Values")
    calibration_matrix, dist, ret, tvecs, rvecs = Calibrate_Camera(new_images, frameSize)

    beta = Return_BetaFromCalibrationMatrix(calibration_matrix)
    fov = Calc_fov(beta, frameSize)
    Print_fovDeg(fov)
    sensorSize = Calc_SensorSize(beta, frameSize, focallength)
    Calc_FocalLength(beta, frameSize, sensorSize)
    Calc_UPA(fov, frameSize)
    Print_CamProperties(calibration_matrix, dist, frameSize, fov)
    print("\n")
    Print_Distortion(dist)
    print("\n")

