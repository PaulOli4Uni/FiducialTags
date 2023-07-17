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


# Example usage:
calibration_matrix = np.array([[1172.64836, 0, 376.929322], [0, 1174.7356, 633.099808], [0, 0, 1]])  # Example calibration matrix
image_resolution = (1280, 720)  # Example image resolution

# horizontal_fov, vertical_fov = calculate_fov(calibration_matrix, image_resolution)
# print("Horizontal FOV:", horizontal_fov, "degrees")
# print("Vertical FOV:", vertical_fov, "degrees")

# Prepare
w, h = 1280, 720
fx, fy = 1173.43804, 1171.39498

# Go
fov_x = np.rad2deg(2 * np.arctan2(w, 2 * fx))
fov_y = np.rad2deg(2 * np.arctan2(h, 2 * fy))

print("Field of View (degrees):")
print(f"  {fov_x = :.1f}\N{DEGREE SIGN}")
print(f"  {fov_y = :.1f}\N{DEGREE SIGN}")

print("\n FoV for .SDF file")
print(f" fov_x = {fov_x*np.pi/180} rad")
print(f" fov_y = {fov_y*np.pi/180} rad")
