from dataclasses import dataclass
from Simulations.Libraries.data_classes import dc_camera, dc_marker, dc_model

dc_camera = dc_camera.camera
dc_marker = dc_marker.marker
dc_model = dc_model.model

@dataclass()
class test_config_data:
    test_name: str
    movement_file: str
    video_file: bool
    gz_pose_file: bool
    vid_pose_file: bool
    cameras: [dc_camera]
    markers: [dc_marker]
    lights: []  # todo: Add lights data class
    models: [dc_model]
