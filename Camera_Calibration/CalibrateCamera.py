"""
From: https://github.com/niconielsen32/ComputerVision/blob/37b279fa44e28fe3ea859bc8f14f5353a6b93e54/cameraCalibration.py#L4
"""


import numpy as np
import cv2 as cv
import glob
import pyheif
from PIL import Image
# from Pillow import PIL
# import Pillow

# def heic_to_cv_image(heic_path):
#     heif_file = pyheif.read(heic_path)
#     image = Image.frombytes(
#         heif_file.mode,
#         heif_file.size,
#         heif_file.data,
#         "raw",
#         heif_file.mode,
#         heif_file.stride,
#     )
#     image = image.convert("RGB")  # Convert to RGB mode for OpenCV compatibility
#     image.show()
#     cv_image = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)  # Convert PIL image to OpenCV format
#     # cv_image = np.array(image)  # Convert PIL image to numpy array
#     # cv_image = cv_image[:, :, ::-1]  # Convert RGB to BGR format
#     print(cv_image)
#     cv.imshow(cv_image)
#     return cv_image

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

################ FIND CHESSBOARD CORNERS - OBJECT POINTS AND IMAGE POINTS #############################

chessboardSize = (9, 6)

# 1440, 1080
frameSize = (3024, 4032)

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)


# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1, 2)

size_of_chessboard_squares_mm = 23
objp = objp * size_of_chessboard_squares_mm


# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.


images = glob.glob('Iphone_Cal_png/*.png')
i = 0
for image in images:
    print(i)
    print(image)
    i=i+1
    # # Check if image format is .heic
    # # if image.split('.')[-1] == 'heic':
    # #     # heif_file = pyheif.read(image, convert_hdr_to_8bit=False)
    # #     # print(heif_file)
    # #     # if heif_file.has_alpha:
    # #     #     heif_file.convert_to("BGRA;16")
    # #     # else:
    # #     #     heif_file.convert_to("BGR;16")
    # #     # heif_file[0].convert_to("BGRA;16" if heif_file[0].has_alpha else "BGR;16")
    # #     # np_array = np.asarray(heif_file[0])
    # #     # pil_img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride)
    # #     # pil_img =
    # #     img = cv.cvtColor(np_array, cv.COLOR_RGB2BGR)
    # # else:  # assume "normal" image that pillow can open
    # #     # img = Image.open(image)
    # #     img = cv.imread(image)
    #
    # img = heic_to_cv_image(image)
    # # print(img)

    img = cv.imread(image)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # cv.imshow(gray)
    # cv.waitKey(1000)
    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, chessboardSize, None)

    # If found, add object points, image points (after refining them)
    print()
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
print("ret")
print(ret)

print("Cam Mat")
print(cameraMatrix)

print("Dist")
print(dist)

print("rvecs")
print(rvecs)

print("tvecs")
print(tvecs)

############## UNDISTORTION #####################################################

img = cv.imread('Iphone_Cal_png/cali5.png')
h,  w = img.shape[:2]
newCameraMatrix, roi = cv.getOptimalNewCameraMatrix(cameraMatrix, dist, (w,h), 1, (w,h))



# Undistort
dst = cv.undistort(img, cameraMatrix, dist, None, newCameraMatrix)

# crop the image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]
cv.imwrite('caliResult1.png', dst)



# Undistort with Remapping
mapx, mapy = cv.initUndistortRectifyMap(cameraMatrix, dist, None, newCameraMatrix, (w,h), 5)
dst = cv.remap(img, mapx, mapy, cv.INTER_LINEAR)

# crop the image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]
cv.imwrite('caliResult2.png', dst)




# Reprojection Error
mean_error = 0

for i in range(len(objpoints)):
    imgpoints2, _ = cv.projectPoints(objpoints[i], rvecs[i], tvecs[i], cameraMatrix, dist)
    error = cv.norm(imgpoints[i], imgpoints2, cv.NORM_L2)/len(imgpoints2)
    mean_error += error

print( "total error: {}".format(mean_error/len(objpoints)) )


