from dataclasses import dataclass
from Simulations.Libraries.data_classes import dc_pose
from Simulations.Libraries import camera_properties

dc_pose = dc_pose.pose

@dataclass()
class camera:
    camera_file: str
    pose: dc_pose
    config: camera_properties