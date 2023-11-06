"""
From: https://github.com/niconielsen32/ComputerVision/blob/37b279fa44e28fe3ea859bc8f14f5353a6b93e54/cameraCalibration.py#L4
"""


import numpy as np
import cv2 as cv
import glob

# --------------------------------------- Properties ----------------------------

chessboardSize = (9, 6)
size_of_chessboard_squares_mm = 22.733

# Common resolutions 1920x1080; 1280x720
frameSize = (1280, 720)  # Img Resolution -Kahn Phone
# frameSize = (6000, 4000)  # Img Resolution -Canon

images = glob.glob('Canon_Vid_Sim/*.png')  # Image DIR and type

# ----------------------------------------------------------------------

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
# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)


# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1, 2)

objp = objp * size_of_chessboard_squares_mm


# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

i = 0
for image in images:
    print("Image: " + str(i) + "\t Dir: " + str(image))
    i=i+1

    img = cv.imread(image)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

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

img = cv.imread(images[0])
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


