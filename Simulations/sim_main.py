"""
Standard used in this library.
xx_file -> refers to the variable file. Thus -> Extension is included
xx_name -> Refers to the name of the file (variable). Thus -> NO Extension in the name
xx_file_path -> refers to the full path to the file
"""
import sys
import os
from Libraries import import_excel, simulation, video_analysis

# ------------ MAIN ------------
if __name__ == '__main__':

    test_path = os.path.dirname(os.path.abspath(__file__))
    # test_path = "/home/stb21753492/FiducialTags/Simulations"

    filename = test_path + "/Tests/z_cutoff_distance.xlsx"

    success_import, main_config, tests_config = import_excel.Import_Excel(filename)

    if not success_import:
        sys.exit()

    print("------------------ \n[INFO] Starting Simulations \n------------------ ")
    # simulation.RunSim(main_config, tests_config)

    print("------------------ \n [INFO] Extracting Pose from Video  \n------------------")
    video_analysis.AnalyseVideo(main_config, tests_config)




