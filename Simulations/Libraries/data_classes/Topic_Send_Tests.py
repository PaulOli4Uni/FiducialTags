import time
import subprocess
import os
import select

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation
import shutil

from Simulations.Libraries import directory_mappings
from Simulations.Libraries.data_classes import dc_pose
dc_pose = dc_pose.pose


def Topic_Send():
    test_name = 'test'
    model_name = 'test1_3Markers'
    pose_msg = '-6.938893903907228e-18,-0.06000000000000015,1.0,0.0,0.0,-30.0,0.255555555555555555'



    wait_cmd = f"gz topic -e -t /model/{model_name}/pos_contr"
    pose_cmd = f"gz topic -t /model/{model_name}/pos_contr -m gz.msgs.StringMsg -p \'data:\"{pose_msg}\"\'"
    print(pose_cmd)
    process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE)

    movement_command_not_received = True
    # while movement_command_not_received:
    #     print("While Loop")
    #     # subprocess.run(pose_cmd, shell=True, capture_output=False, text=True)
    #
    #     output = process.stdout.readline()
    #     print("dd")
    #     print(output)
    #     print(process.poll())
    #     # print("This is output: " + str(output))
    #     # If value received, break from while
    #     if process.poll() is not None:
    #         print('1')
    #         break
    #     if output:
    #         print('2')
    #         process.terminate()
    #         movement_command_not_received = False



    scan_process = subprocess.Popen(wait_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    poll_obj = select.poll()
    poll_obj.register(scan_process.stdout, select.POLLIN)
    while (movement_command_not_received):


        subprocess.run(pose_cmd, shell=True, capture_output=False, text=True)


        poll_result = poll_obj.poll(0)
        if poll_result:
            line = scan_process.stdout.readline()
            print(line)
            movement_command_not_received = False



Topic_Send()