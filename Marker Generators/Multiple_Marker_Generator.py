"""
File creates a SET of Aruco Markers
Properties:
-t --type: Type of Marker to generate (see dictionary below for marker types) NxN_M
	N -> Bits
	M -> Unique ID's to generate
-n --num: Number of ArUCo tags to generate, ranges from 0 -> M-1
-s --size: Size of marker in mm (pixels)
-o --output: path to file containing ALL ArUCo tags

Example of terminal message to generate a set of the first marker type
python3 Multiple_Marker_Generator.py -o "FileLocation" -n 10 -t "DICT_4X4_50" -s 200
"""

import numpy as np
import argparse
import cv2
import sys
import os
from pathlib import Path
from distutils.util import strtobool

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


# Use a breakpoint in the code line below to debug your script.
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", required=True,
                help="Path to file containing ALL ArUCo tags")
ap.add_argument("-n", "--num", type=int, required=True,
                help="Number of ArUCo tags to generate")
ap.add_argument("-s", "--size", type=int, required=True,
                help="Physical size of marker to generate in mm (pixels)") # Defualt size value is 300 (if none provided)
ap.add_argument("-t", "--type", type=str,
                default="DICT_ARUCO_ORIGINAL",
                help="Type of ArUCo tag to generate")

args = vars(ap.parse_args())

## Checks
# verify that the supplied ArUCo tag exists and is supported by OpenCV
if ARUCO_DICT.get(args["type"], None) is None:
    print("[INFO] ArUCo tag of '{}' is not supported".format(
        args["type"]))
    sys.exit(0)

# Todo: check that number of tags to generate is <= dictionary max (and > 0)
#if args["num"] >>


MYDIR = args["output"]
CHECK_FOLDER = os.path.isdir(MYDIR)
# If folder doesn't exist, then create it.
if not CHECK_FOLDER:
    os.makedirs(MYDIR)

# load the ArUCo dictionary
arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[args["type"]])

for i in range(args["num"]):
	# allocate memory for the output ArUCo tag and then draw the ArUCo
	# tag on the output image
	print("[INFO] generating ArUCo tag type '{}' with ID '{}'".format(
		args["type"], i))
	tag = np.zeros((args["size"], args["size"], 1), dtype="uint8")

	# Parameters : MarkerDictionary, ID, Size, Image, Border bits size
	cv2.aruco.generateImageMarker(arucoDict, i, args["size"], tag, 1)
	filename = MYDIR +"/" + args["type"] + "_id_" + str(i) + ".png"
	cv2.imwrite(filename, tag)

print("All tags have been created")


