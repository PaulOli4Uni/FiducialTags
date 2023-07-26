"""
Standard used in this library.
xx_file -> refers to the variable file. Thus -> Extension is included
xx_name -> Refers to the name of the file (variable). Thus -> NO Extension in the name
"""

import sys
import os
from Libraries import import_excel, simulation

# ------------ MAIN ------------
if __name__ == '__main__':

    test_path = os.path.dirname(os.path.abspath(__file__))

    filename = test_path + "/Tests/Test.xlsx"

    success_import, main_config, tests_config = import_excel.Import_Excel(filename)

    if not success_import:
        sys.exit()

    print("[INFO] Starting Simulations")
    simulation.RunSim(main_config, tests_config)
