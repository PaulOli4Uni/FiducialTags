from robodk.robolink import *  # API to communicate with RoboDK
from robodk.robomath import *  # Robot toolbox
from robodk.robofileio import *

# Start communication with RoboDK
RDK = Robolink()

# Define the robot
ROBOT = RDK.ItemUserPick('Select a robot', ITEM_TYPE_ROBOT)
if not ROBOT.Valid():
    raise Exception('No robot selected or available')

# Specify the path to the CSV file
# csv_file = r'path_to_your_csv_file.csv'
# csv_file = r'C:\Users\paulo\OneDrive - Stellenbosch University\Masters\Thesis\3.Sim\Sim Verification\MovementFiles\test1.csv'
# csv_file = r'/home/paul/Downloads/test1.csv'
# csv_file = r'/home/paul/Sim_Analysis/Verification/MovMatrix.csv'
# csv_file = r'/home/paul/FiducialTags/Simulations/Verification/Kuka_Files/CSV_Files_for_Test/MovMatrix_10.csv'
# csv_file = r'/home/paul/FiducialTags/Simulations/Verification/Kuka_Files/CSV_Files_for_Test/Mov_Dynamic.csv'
csv_file = r'/home/paul/FiducialTags/Simulations/Verification/Kuka_Files/CSV_Files_for_Test/Mov_Dynamic_many.csv'

# csv_file = r'/test1.csv'

# Specify file codec
codec = 'utf-8'


initial_pose = ROBOT.Pose()
print(Mat(initial_pose))
target_ref = ROBOT.Pose()
pos_ref = target_ref.Pos()

# Load CSV data as a list of poses
def load_targets(strfile):
    csvdata = LoadList(strfile, ',', codec)
    poses = []
    for i in range(0, len(csvdata)):
        x, y, z, rx, ry, rz = csvdata[i][0:6]
        poses.append((x, y, z, rx, ry, rz))  # Store as a tuple

    return poses

# Move the robot to the poses from the CSV file
def move_robot_to_poses(strfile):
    poses = load_targets(strfile)

    # Set the robot's reference frame and tool frame
    ROBOT.setPoseFrame(ROBOT.PoseFrame())
    ROBOT.setPoseTool(ROBOT.PoseTool())
    # ROBOT.setG
    # Move the robot to the home position
    # ROBOT.MoveJ(ROBOT.JointsHome())

    # Move the robot to each pose from the CSV
    target_i = Mat(target_ref)
    for pose in poses:
        x, y, z, rx, ry, rz = pose  # Unpack the tuple
        # pose_matrix = transl(x, y, z) * rotz(rx * pi / 180) * roty(ry * pi / 180) * rotx(rx * pi / 180)
        # target_i = Offset(target_i, x,y,z,rx,ry,rz)
        target_i = RelTool(target_i, x, y, z, rx, ry, rz)

        # ROBOT.Pause(100000)
        # ROBOT.MoveJ(target_i)
        ROBOT.MoveL(target_i)

    ROBOT.MoveL(initial_pose)

# Run the script to move the robot to the poses from the CSV file
move_robot_to_poses(csv_file)
