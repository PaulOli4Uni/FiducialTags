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
python3 Png_To_Obj.py -i "/home/paul/FiducialTags/Simulations/Verification/3Markers/3Markers.pdf" -l 1000 -h 500
"""

import numpy as np
import argparse
import cv2
import sys
import os

# height = 0.005
width = 0.005
white_img_tag = 255 * np.ones((100, 100, 1), dtype="uint8")


def SetupArguments(ap):
    ap.add_argument("-i", "--input_dir", type=str,
                    help="Path to folder where .png image is stored, obj file will be placed in this directory")
    ap.add_argument("-l", "--length", type=int, required=True,
                    help="Physical size of marker to generate in mm (pixels) [for square markers]")
    ap.add_argument("-ht", "--height", type=int, required=True,
                    help="Physical size of marker to generate in mm (pixels) [for square markers]")

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




if __name__ == '__main__':
    # Add file arguments
    ap = argparse.ArgumentParser()
    SetupArguments(ap)
    args = vars(ap.parse_args())

    input_img_dir = args["input_dir"]
    output_dir = os.path.dirname(input_img_dir)
    filename = os.path.splitext(os.path.basename(input_img_dir))[0]
    length = args["length"]
    height = args["height"]

    # Output Directory already made
    vertexes_str = CreateObjFileVerteces(length/1000, height/1000)
    # Create white png img in file
    cv2.imwrite(os.path.join(output_dir, "white.png"), white_img_tag)

    # --Create .obj and .mtl files
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