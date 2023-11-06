from dataclasses import dataclass
from Simulations.Libraries.data_classes import dc_pose
import numpy as np

CamPosition = dc_pose.pose

@dataclass()
class CameraProperties:
    topic_name: str
    pose: CamPosition
    calibration_matrix: np.array
    distortion_coeff: np.array
    horizontal_fov: float
    img_width: int
    img_height: int
    clip_near: float
    clip_far: float
    lens_type: str
    cutoff_angle: float
    framerate: int
