import cv2
import numpy as np


def calculate_fov(calibration_matrix, image_resolution):
    fx = calibration_matrix[0, 0]  # Focal length in the x-direction
    fy = calibration_matrix[1, 1]  # Focal length in the y-direction
    width = image_resolution[0]  # Image width in pixels
    height = image_resolution[1]  # Image height in pixels

    fov_x, fov_y, _, _ = cv2.calibrationMatrixValues(calibration_matrix, (width, height), width, height)

    horizontal_fov = fov_x * (180 / np.pi)  # Horizontal FOV in degrees
    vertical_fov = fov_y * (180 / np.pi)  # Vertical FOV in degrees

    return horizontal_fov, vertical_fov


# Example usage KhanPhone:
calibration_matrix = np.array([[1172.64836, 0, 376.929322], [0, 1174.7356, 633.099808], [0, 0, 1]])  # Khan Phone
image_resolution = (1280, 720)  # Example image resolution

# Canon - NORMAL (IMG)
calibration_matrix = np.array([[5163.89688, 0, 2962.82638], [0, 5167.8757, 1953.23275], [0, 0, 1]])  # Canon Calibration
image_resolution = (6000, 4000)
sensor_size = (22.3,14.9) #  mm Around (not direct measurement)

# Canon - VIDEO
# calibration_matrix = np.array([[float('1.25440763e+03'), 0, float('5.94402907e+02')],
#                               [0, float('1.25476819e+03'), float('3.87369665e+02')],
#                               [0, 0, 1]], dtype=np.float32)
# image_resolution = (1280, 720)
# sensor_size = (24,36) #  mm Around (not direct measurement)



# horizontal_fov, vertical_fov = calculate_fov(calibration_matrix, image_resolution)
# print("Horizontal FOV:", horizontal_fov, "degrees")
# print("Vertical FOV:", vertical_fov, "degrees")

# Prepare
w, h = image_resolution[0], image_resolution[1]
fx, fy = calibration_matrix[0,0], calibration_matrix[1,1]

# Go
fov_x = np.rad2deg(2 * np.arctan2(w, 2 * fx))
fov_y = np.rad2deg(2 * np.arctan2(h, 2 * fy))

print("Field of View (degrees):")
print(f"  {fov_x = :.1f}\N{DEGREE SIGN}")
print(f"  {fov_y = :.1f}\N{DEGREE SIGN}")

print("\n FoV for .SDF file")
print(f" fov_x = {fov_x*np.pi/180} rad")
print(f" fov_y = {fov_y*np.pi/180} rad")

# Focal length
focal_x = sensor_size[0]*fx/w
print((f"Focal length x = {focal_x} mm"))
focal_y = sensor_size[1]*fy/h
print((f"More Accurate ->  Focal length y = {focal_y} mm"))
