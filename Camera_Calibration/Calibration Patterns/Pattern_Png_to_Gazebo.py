"""
Code Sources:
 https://pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/
 https://grabcad.com/tutorials/create-an-obj-cube-with-your-favorite-images

File creates a SET of Aruco Markers
Properties:
-o --output_dir: path to file where tags/images should be stored (for Obj make it the model directory)
-i --input_image: Path to .png image file
Following two is mainly used when setting up calibration patters (objects that are not square):
-l --length: Width of marker to generate in mm (pixels) [does not work if size is given]
-ht --height: Height of marker to generate in mm (pixels) [does not work if size is given]

output_dir: (model directory provided by user)
|-->output_dir (Will automatically generate folder based on selected dictionary, and size)
	|->input_image.png
	|->white.png
	|->Calibration_Pattern.obj
	|->Caldibration_Pattern.mtl

Marker Dim:

        /-------/|  ------ ^
       /       / |  height |
      /_______/  |  ------ v
     |       |  /
     |       | /  width
     |-------|/
      length

Example of terminal message to generate a set of the first marker type
python3 Pattern_Png_to_Gazebo.py -i "pattern.png" -o "Patten_Gz" -l 297 -ht 210

"""

import numpy as np
import argparse
import cv2
import os

width = 0.005 # Thin for most applications
white_img_tag = 255 * np.ones((100, 100, 1), dtype="uint8")


def SetupArguments(ap):
    ap.add_argument("-o", "--output_dir",
                    help="Path to file where ArUCo tags shuould be stored")
    ap.add_argument("-i", "--input_img", type=str,
                    help="Path to folder where .png images are stored (when converting from png to obj")
    ap.add_argument("-l", "--length", type=int,
                    help="Width of marker to generate in mm (pixels) [does not work if size is given]")
    ap.add_argument("-ht", "--height", type=int,
                    help="Height of marker to generate in mm (pixels) [does not work if size is given]")


def CheckOutputDir(output_dir):
    CHECK_FOLDER = os.path.isdir(output_dir)
    # If folder doesn't exist, then create it.
    if not CHECK_FOLDER:
        print("[INFO] output_dir folder does not exist, creating directory: \'" + output_dir + "\'")
        os.makedirs(output_dir)

def CreateObjFileVerteces(length, height):
    str_file = ""

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


def CreateObj(input_img_dir, output_dir, length, height):

    # Size given in mm -> need to convert to m
    vertexes_str = CreateObjFileVerteces(length/1000, height/1000)

    # Copy image over to folder
    cmd = "cp -r " + input_img_dir + " " + output_dir
    os.system(cmd)
    # Create white png img in file
    cv2.imwrite(os.path.join(output_dir, "white.png"), white_img_tag)

    # --Create .obj and .mtl files
    filename = "calibration_pattern"
    # -Create .obj file
    f = open(os.path.join(output_dir, filename + ".obj"), "w")
    f.write(CreateObjFileString(filename, vertexes_str))
    f.close()
    # -Create .mtl file
    f = open(os.path.join(output_dir, filename + ".mtl"), "w")
    f.write(CreateMtlString(filename))
    f.close()
    # -Create .sdf file
    f = open(os.path.join(output_dir, filename + ".sdf"), "w")
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
                <pose>0 0 0 0 0 0</pose>
                    <visual name="{filename}_Visual">
                        <pose>0 0 {2.5*width} 0 0 0</pose>
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


if __name__ == '__main__':
    # Add file arugments
    ap = argparse.ArgumentParser()
    SetupArguments(ap)
    args = vars(ap.parse_args())

    CheckOutputDir(args["output_dir"])
    ## Create Pattern
    CreateObj(args["input_img"], args["output_dir"], args["length"], args["height"])
