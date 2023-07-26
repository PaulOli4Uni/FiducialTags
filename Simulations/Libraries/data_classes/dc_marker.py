from dataclasses import dataclass
from Simulations.Libraries.data_classes import dc_pose

dc_pose = dc_pose.pose

@dataclass()
class marker:
    marker_file: str
    pose: dc_pose
    dictionary: str #String of Dict (not aruco.getpredefineddict ...)
    id: int
    size: float # in m (meters)
