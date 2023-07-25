from dataclasses import dataclass
from Simulations.Libraries.data_classes import dc_pose

dc_pose = dc_pose.pose

@dataclass()
class model:
    model_file: str
    pose: dc_pose