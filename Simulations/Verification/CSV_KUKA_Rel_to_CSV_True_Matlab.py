import numpy as np
from robodk.robolink import *  # API to communicate with RoboDK
from robodk.robomath import *  # Robot toolbox
from robodk.robofileio import *



# csv_file = r'/home/paul/FiducialTags/Simulations/Verification/Kuka_Files/CSV_Files_for_Test/Mov_Dynamic.csv'
# filename = '/home/paul/Sim_Analysis/Verification/Dynamic_Tests/vid_Test1/pose_csv.csv'
# time_mult = 5
csv_file = r'/home/paul/FiducialTags/Simulations/Verification/Kuka_Files/CSV_Files_for_Test/Mov_Dynamic_Many.csv'
filename = '/home/paul/Sim_Analysis/Verification/Dynamic_Tests/vid_Test2/pose_csv.csv'
time_mult = 5.47

# initial_pose = xyzrpw_2_pose([0,0,0,9,-3,-3])
initial_pose = xyzrpw_2_pose([0,0,0,9,-7,-2])


# initial_pose = xyzrpw_2_pose([0,0,0,0,0,0])
gazebo_offset = [0.008+0.02, -0.004-0.025, +0.826+0.06, 0, 0, 0]  # Example offset

# Load CSV data as a list of poses
def load_targets(strfile):
    codec = 'utf-8'
    csvdata = LoadList(strfile, ',', codec)
    poses = []
    for i in range(0, len(csvdata)):
        x, y, z, rx, ry, rz = csvdata[i][0:6]
        poses.append((x, y, z, rx, ry, rz))  # Store as a tuple

    return poses

# Move the robot to the poses from the CSV file
def calc_true_poses(strfile):

    poses = load_targets(strfile)

    target_i = Mat(initial_pose)
    rot_i = xyzrpw_2_pose([0,0,0,0,0,0])
    # mapped_poses = [pose_2_xyzrpw(target_i)]  # Initial pose
    mapped_poses = [pose_2_xyzrpw(rot_i)]  # Initial pose

    for pose in poses:
        x, y, z, rx, ry, rz = pose  # Unpack the tuple


        xx, yy, zz, rrx, rry, rrz = pose_2_xyzrpw(rot_i)
        rrx = rrx + rx
        rry = rry + ry
        rrz = rrz + rz
        rot_i = xyzrpw_2_pose([x,y,z,rrx,rry,rrz]) # X,Y,Z dont matter for rot_i

        target_i = RelTool(target_i, x, y, z, rx, ry, rz)
        nx, ny, nz, a, b, c = pose_2_xyzrpw(target_i)
        pose_to_map = xyzrpw_2_pose([nx,ny,nz,rrx,rry,rrz])
        mapped_poses.append(pose_2_xyzrpw(pose_to_map))  # Calculate absolute pose
        # mapped_poses.append(pose_2_xyzrpw(target_i))  # Calculate absolute pose
        # print(pose_2_xyzrpw(target_i))
        # print(pose_2_xyzrpw(pose_to_map))

    # Convert the list of poses to a numpy matrix
    pose_matrix = np.array(mapped_poses)
    return pose_matrix


def process_poses(marker_pose_data, small_time_interval=0.22):
    # Convert the X, Y, Z from mm to m by dividing by 1000
    marker_pose_data[:, :3] = marker_pose_data[:, :3] / 1000
    # Number of poses
    n_poses = marker_pose_data.shape[0]
    # marker_pose_data[:, :2] = marker_pose_data[:, 1::-1]  # Swap X and Y
    # Initialize the output array with twice the number of rows for duplicating poses and 7 columns
    preprocessed_data = np.zeros((n_poses, 7))  # 7th column for time
    preprocessed_data[:, 0] = marker_pose_data[:, 1]
    preprocessed_data[:, 1] = marker_pose_data[:, 0]
    preprocessed_data[:, 2] = -marker_pose_data[:, 2]
    preprocessed_data[:, 3] = marker_pose_data[:, 4]
    preprocessed_data[:, 4] = marker_pose_data[:, 3]
    preprocessed_data[:, 5] = -marker_pose_data[:, 5]

    processed_data = np.zeros((n_poses*2, 7))  # 7th column for time
    #
    # # Perform the axis remapping with sign change for columns 3 and 6
    # # Assuming the incoming matrix has columns [X, Y, Z, Rx, Ry, Rz]
    for i in range(n_poses):
        processed_data[2*i, :] = preprocessed_data[i, :]
        processed_data[(2*i)+1, :] = preprocessed_data[i, :]
    # processed_data = preprocessed_data
    # # Calculate distances and times, and duplicate poses with small_time_interval
    # # for i in range(0, n_poses * 2, 2): #

    # Calculate distances and times, and duplicate poses with small_time_interval
    for i in range(0, n_poses * 2, 2):
        if i > 0:  # Skip the first pose since it does not have a predecessor
            # Calculate Euclidean distance between consecutive original positions
            distance = np.linalg.norm(processed_data[i, :3] - processed_data[i - 2, :3])
            processed_data[i, 6] = distance*time_mult  # Set the time to the distance for demonstration
            print((distance))
        # Copy the original pose to the next row with a small interval
        processed_data[i + 1, :6] = processed_data[i, :6]
        processed_data[i + 1, 6] = small_time_interval

    # for i in range(0, n_poses):
    #     if i > 0:  # Skip the first pose since it does not have a predecessor
    #         # Calculate Euclidean distance between consecutive original positions
    #         distance = np.linalg.norm(processed_data[i, :3] - processed_data[i - 1, :3])
    #         # Compute the time assuming constant speed or other criteria
    #         # For now, we use distance for illustration
    #         processed_data[i, 6] = distance*time_mult

        # Copy the original pose to the next row with a small interval

    # # Remove the first and last row
    processed_data = processed_data[1:-1]

    # Handle the time for the first pose if needed
    processed_data[0, 6] = 0
    print(processed_data)
    return processed_data


def add_offset_to_poses(processed_data, offset_vector):
    # Ensure the offset_vector is a NumPy array for broadcasting
    offset_vector = np.array(offset_vector)

    # Check if the offset vector has 6 elements
    if offset_vector.shape[0] != 6:
        raise ValueError("Offset vector must have 6 elements.")

    # Add the offset to all rows, excluding the last column (time)
    processed_data_with_offset = processed_data.copy()
    processed_data_with_offset[:, :-1] += offset_vector

    return processed_data_with_offset


def save_to_csv(data, filename):
    # Save the data to a CSV file without headers
    np.savetxt(filename, data, delimiter=',', fmt='%f')  # '%f' can be adjusted if needed for formatting


# Run the script to move the robot to the poses from the CSV file
true_poses_matrix = calc_true_poses(csv_file)
processed_data = process_poses(true_poses_matrix)
processed_data_with_offset = add_offset_to_poses(processed_data, gazebo_offset)
save_to_csv(processed_data_with_offset, filename)

# print(processed_data_with_offset)