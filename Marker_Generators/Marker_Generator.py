"""
Code Sources:
 https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/
 https://grabcad.com/tutorials/create-an-obj-cube-with-your-favorite-images

File creates a SET of Aruco Markers
Properties:
-f --function: Task to be completed by program. Can be: CreatePng, CreateObj, PngToObj)
-o --output_dir: path to file where tags/images should be stored (for Obj make it the model directory)
-n --num: Number of ArUCo tags to generate, ranges from 0 -> M-1
-id --id: ID of ArUCo tag to generate (number of tags = 1)
-i --inputpath: Path to folder where .png images are stored (when converting from png to obj)
-s --size: Size of marker in mm (pixels) (for square markers)
-t --type: Type of Marker to generate (see dictionary below for marker types) NxN_M
	N -> Bits
	M -> Unique ID's to generate

Marker images will always be of type .png
Gazebo Markers will always be of type .obj with additional .mtl file

File Structure for Gazebo Tag Models (objects), each object will have its own file:
output_dir: (model directory provided by user)
|-->MarkerType1 (Will automatically generate folder based on selected dictionary, and size)
|	|-->Img
|	|	|->ImgX.png
|	|	|->ImgY.png
|	|-->Marker_ID_X
|		|->Marker_ID_X.png
|		|->white.png
|		|->Marker_ID_X.obj
|		|->Marker_ID_X.mtl
|	|-->Marker_ID_Y
|		|->Marker_ID_Y.png
|		|->white.png
|		|->Marker_ID_Y.obj
|		|->Marker_ID_Y.mtl
|-->MarkerType2

Marker Dim:

        /-------/|  ------ ^
       /       / |  height |
      /_______/  |  ------ v
     |       |  /
     |       | /  width
     |-------|/
      length

Example of terminal message to generate a set of the first marker type
python3 Marker_Generator.py -f "CreateObj"  -o "FileLocation" -n 10 -t "DICT_4X4_50" -s 1000
python3 Marker_Generator.py -f "CreateObj"  -o "/home/stb21753492/FiducialTags/Simulations/Markers" -n 10 -t "DICT_4X4_50" -s 1000
python3 Marker_Generator.py -f "CreateObj"  -o "/home/paul/FiducialTags/Simulations/Markers" -n 10 -t "DICT_4X4_50" -s 1000
"""

import numpy as np
import argparse
import cv2
import sys
import os

# height = 0.005
width = 0.005


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

Function_DICT = {
    "CreatePng": 1,
    "CreateObj": 2,
    "PngToObj": 3
}

white_img_tag = 255 * np.ones((100, 100, 1), dtype="uint8")


def SetupArguments(ap):
    ap.add_argument("-f", "--function", required=True,
                    help="Task to be completed by file. Can be: \n CreatePng \n CreateObj \n PngToObj")
    ap.add_argument("-o", "--output_dir",
                    help="Path to file where ArUCo tags shuould be stored")
    ap.add_argument("-n", "--num", type=int, required=True,
                    help="Number of ArUCo tags to generate")
    ap.add_argument("-id", "--id", type=int,
                    help="ID of ArUCo tag to generate (if number of tags = 1)")
    ap.add_argument("-i", "--input_dir", type=str,
                    help="Path to folder where .png images are stored (when converting from png to obj")
    ap.add_argument("-s", "--size", type=int, required=True,
                    help="Physical size of marker to generate in mm (pixels) [for square markers]")
    ap.add_argument("-t", "--type", type=str, required=True,
                    default="DICT_ARUCO_ORIGINAL",
                    help="Type of ArUCo tag to generate")


def CheckTagDictionaryExists(TagType):
    # verify that the supplied ArUCo tag exists and is supported by OpenCV
    if ARUCO_DICT.get(TagType, None) is None:
        print("[INFO] ArUCo tag of '{}' is not supported".format(
            args["type"]))
        sys.exit(0)


def CheckTagNumberToGenerate(num, id):
    if num <= 0:
        print("[ERR] Number of tags to generate must be larger than 0")
        sys.exit(0)
    elif num == 1:  # Only 1 Tag to generate, get tag id
        # check tag id has been given
        if args["id"] is None:
            print("[ERR] ID must be provided when generating 1 tag")
            sys.exit(0)
        print("[INFO] Only 1 tag to be generated, ID = " + str(id))

# Todo: check that number of tags to generate is <= dictionary max

def CheckOutputDir(output_dir):
    CHECK_FOLDER = os.path.isdir(output_dir)
    # If folder doesn't exist, then create it.
    if not CHECK_FOLDER:
        print("[INFO] output_dir folder does not exist, creating directory: \'" + output_dir + "\'")
        os.makedirs(output_dir)


def CreatePng(marker_type, num, marker_id, size, output_dir):
    # load the ArUCo dictionary
    arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT[marker_type])

    for i in range(num):
        if num == 1:  # If only 1 marker, generate spesific id (loop wil only run once)
            i = marker_id
        # allocate memory for the output_dir ArUCo tag and then draw the ArUCo tag on the output_dir image
        print("[INFO] Generating ArUCo tag image. Ttype '{}' with ID '{}'".format(marker_type, i))
        tag = np.zeros((size, size, 1), dtype="uint8")

        # Parameters : MarkerDictionary, ID, Size, Image, Border bits size
        # cv2.aruco.generateImageMarker(arucoDict, i, size, tag, 1) # OLD PC
        cv2.aruco.drawMarker(arucoDict, i, size, tag, 1) # NEW PC
        filename = output_dir + "/" + marker_type + "_s" + str(size) + "_id" + str(i) + ".png"
        cv2.imwrite(filename, tag)

    print("[INFO] All tag images have been created")


def CreateObjFileVerteces(size):
    str_file = ""
    length = size
    height = size

    # vertices = [
    #     (-length / 2, -width / 2, -height / 2),  # Vertex 0
    #     (length / 2, -width / 2, -height / 2),  # Vertex 1
    #     (length / 2, width / 2, -height / 2),  # Vertex 2
    #     (-length / 2, width / 2, -height / 2),  # Vertex 3
    #     (-length / 2, -width / 2, height / 2),  # Vertex 4
    #     (length / 2, -width / 2, height / 2),  # Vertex 5
    #     (length / 2, width / 2, height / 2),  # Vertex 6
    #     (-length / 2, width / 2, height / 2)  # Vertex 7
    # ]

    vertices = [
        (-length / 2, -height / 2, -width / 2),  # Vertex 0
        (length / 2, -height / 2, -width / 2),  # Vertex 1
        (length / 2, height / 2, -width / 2),  # Vertex 2
        (-length / 2, height / 2, -width / 2),  # Vertex 3
        (-length / 2, -height / 2, width / 2),  # Vertex 4
        (length / 2, -height / 2, width / 2),  # Vertex 5
        (length / 2, height / 2, width / 2),  # Vertex 6
        (-length / 2, height / 2, width / 2)  # Vertex 7
    ]

    for i in range(len(vertices)):
        str_file = str_file + "v " + str(vertices[i][0]) + " " + str(vertices[i][1]) + " " + str(vertices[i][2]) + "\n"

    return str_file


def CreateObj(marker_type, num, marker_id, size, output_dir):
    # Create location for all folders of dictionary type
    dictionary_dir = os.path.join(output_dir, marker_type + "_s" + str(size))
    os.makedirs(dictionary_dir)
    # Create all Png files for dictionary type in an Img folder
    png_files_dir = os.path.join(dictionary_dir, "Img")
    os.makedirs(png_files_dir)
    CreatePng(marker_type, num, marker_id, size, png_files_dir)
    # Size given in mm -> need to convert to m
    vertexes_str = CreateObjFileVerteces(size/1000)

    for i in range(num):
        if num == 1:  # If only 1 marker, generate specific id (loop wil only run once)
            i = marker_id

        print("[INFO] Generating ArUCo tag model. Type '{}' with ID '{}'".format(marker_type, i))
        # Filename of marker (foldername + idn) (same for folder, .png, and .obj)
        filename = marker_type + "_s" + str(size) + "_id" + str(i)
        marker_model_dir = os.path.join(dictionary_dir, filename)
        os.makedirs(marker_model_dir)

        # Copy image over to folder
        cmd = "cp -r " + os.path.join(dictionary_dir, "Img", filename + ".png ") + " " + marker_model_dir
        os.system(cmd)
        # Create white png img in file
        cv2.imwrite(os.path.join(marker_model_dir, "white.png"), white_img_tag)

        # --Create .obj and .mtl files
        # -Create .obj file
        f = open(os.path.join(marker_model_dir, filename + ".obj"), "w")
        f.write(CreateObjFileString(filename, vertexes_str))
        f.close()
        # -Create .mtl file
        f = open(os.path.join(marker_model_dir, filename + ".mtl"), "w")
        f.write(CreateMtlString(filename))
        f.close()
        # -Create .sdf file
        f = open(os.path.join(marker_model_dir, filename + ".sdf"), "w")
        f.write(CreateSDFFileString(filename))
        f.close()


def CreateObjFileString(filename, vertexes_str):
    # Strings containing file information. Obj file requires info in header
    obj_file_str = f"""mtllib {filename}.mtl
o Mesh 
{vertexes_str}
vn 0 -1 0.5 
vn 0 1 0.5
vn -1 0 0.5
vn 1 0 0
vn 0 0 1
vn 0 0 -1
vt 0 0
vt 1 0
vt 0 1
vt 1 1

usemtl CubeOther
f 1/1/1 2/2/1 6/4/1
f 1/1/1 6/4/1 5/3/1
usemtl CubeOther
f 3/1/2 4/2/2 8/4/2
f 3/1/2 8/4/2 7/3/2
usemtl CubeOther
f 4/1/3 1/2/3 5/4/3
f 4/1/3 5/4/3 8/3/3
usemtl CubeOther
f 2/1/4 3/2/4 7/4/4
f 2/1/4 7/4/4 6/3/4
usemtl CubeTop
f 5/1/5 6/2/5 7/4/5
f 5/1/5 7/4/5 8/3/5
usemtl CubeOther
f 4/1/6 3/2/6 2/4/6
f 4/1/6 2/4/6 1/3/6"""
    return obj_file_str

def CreateMtlString(filename):

    mtl_file_str = f"""newmtl CubeTop
Kd 1 1 1
Ns 96.0784
d 1
illum 1
Ka 0 0 0
Ks 0 0 0
map_Kd {filename}.png

newmtl CubeOther
Kd 1 1 1
Ns 96.0784
d 1
illum 1
Ka 0 0 0
Ks 0 0 0
map_Kd white.png"""
    return mtl_file_str

def CreateSDFFileString(filename):
    sdf_file_str = f"""<?xml version="1.0" ?>
        <sdf version="1.5">
        <model name="{filename}">
              <link name="Main">
                <pose>0 0 0 0 0 -1.570796327</pose>
                    <visual name="{filename}_Visual">
                        <pose>0 0 {2*width} 0 0 0</pose>
                        <geometry>
                            <mesh>
                                <scale>1 1 1</scale>
                                <uri>{filename}.obj</uri>
                            </mesh>
                        </geometry>
                    </visual>
                    <gravity>1</gravity>
                    <velocity_decay/>
                    <self_collide>0</self_collide>
              </link>
          </model></sdf>"""

    return sdf_file_str


def PngToObj():
    pass


if __name__ == '__main__':
    # Add file arugments
    ap = argparse.ArgumentParser()
    SetupArguments(ap)
    args = vars(ap.parse_args())

    ## Perform Checks
    # Ensure correct function is provided
    match (Function_DICT.get(args["function"], None)):
        case None:
            print("[ERR] Incorrect function provided: \'" + str(args["function"]) + "\' not a valid option")
            sys.exit(0)
        case 1:
            print("[INFO] Function \'CreatePng\' selected")
            CheckTagDictionaryExists(args["type"])
            CheckTagNumberToGenerate(args["num"], args["id"])
        case 2:
            print("[INFO] Function \'CreateObj\' selected")
            CheckTagDictionaryExists(args["type"])
            CheckTagNumberToGenerate(args["num"], args["id"])
        case 3:
            print("[INFO] Function \'PngToObj\' selected")
            # todo: Check input png file exists

    CheckOutputDir(args["output_dir"])

    ## Create Img/Markers
    match (Function_DICT.get(args["function"], None)):
        case 1:
            CreatePng(args["type"], args["num"], args["id"], args["size"], args["output_dir"])
        case 2:
            CreateObj(args["type"], args["num"], args["id"], args["size"], args["output_dir"])
        case 3:
            print("[INFO] Function \'PngToObj\' selected")
            PngToObj()
