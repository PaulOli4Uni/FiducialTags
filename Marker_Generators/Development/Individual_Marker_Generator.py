
"""
Code Base: https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/

File creates an Individual Aruco Marker
Properties:
-t --type: Type of Marker to generate (see dictionary below for marker types) NxN_M
	N -> Bits
	M -> Unique ID's to generate
-i --id: Marker ID, ranges from 0 -> M-1
-s --size: Size of marker in mm (pixels)
-v --view: Boolean to view generated marker (True by default)
-o --output: Path to output image containing ArUCo tag

Example of terminal message to generate the first marker type (Marker ID of 1). Marker will not be displayed
python3 Individual_Marker_Generator.py -o "MarkerName.png" -i 0 -t "DICT_4X4_50" -s 200 -v 'False'

Following website can also be used:
https://chev.me/arucogen/
"""

import numpy as np
import argparse
import cv2
import sys
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
                help="Path to output image containing ArUCo tag")
ap.add_argument("-i", "--id", type=int, required=True,
                help="ID of ArUCo tag to generate")
ap.add_argument("-s", "--size", type=int, required=True,
                help="Physical size of marker to generate in mm (pixels)") # Defualt size value is 300 (if none provided)
ap.add_argument("-t", "--type", type=str,
                default="DICT_ARUCO_ORIGINAL",
                help="type of ArUCo tag to generate")
ap.add_argument("-v", "--view", choices=('True','False'),
                default="True",
                help="Show generated marker")


args = vars(ap.parse_args())

# verify that the supplied ArUCo tag exists and is supported by OpenCV
if ARUCO_DICT.get(args["type"], None) is None:
    print("[INFO] ArUCo tag of '{}' is not supported".format(
        args["type"]))
    sys.exit(0)
# load the ArUCo dictionary
arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[args["type"]])
# allocate memory for the output ArUCo tag and then draw the ArUCo
# tag on the output image
print("[INFO] generating ArUCo tag type '{}' with ID '{}'".format(
    args["type"], args["id"]))
tag = np.zeros((args["size"], args["size"], 1), dtype="uint8")

# Parameters : MarkerDictionary, ID, Size, Image, Border bits size
cv2.aruco.generateImageMarker(arucoDict, args["id"], args["size"], tag, 1)
# write the generated ArUCo tag to disk and then display it to our screen

# Check that file extention has been given. If not, or extention is wrong -> .png is added automatically
if not (Path(args["output"]).is_file() and (Path(args["output"]).suffix == '.mp3' or '.png')):
	args["output"] = args["output"] + ".png"


cv2.imwrite(args["output"], tag)

if strtobool(args["view"]):
	cv2.imshow("ArUCo Tag", tag)
	cv2.waitKey(0)



