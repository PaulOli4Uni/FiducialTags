from dataclasses import dataclass
from typing import List


@dataclass()
class CamPosition:
    X: float
    Y: float
    Z: float
    r: float
    p: float
    y: float


@dataclass()
class CameraProperties:
    topic_name: str
    pose: CamPosition
    horizontal_fov: float
    img_width: int
    img_height: int
    clip_near: float
    clip_far: float
    lens_type: str
    cutoff_angle: float
    framerate: int


class CameraLoader:
    def __init__(self, file_location: str):
        self.file_location = file_location
        self.camera_properties: List[CameraProperties] = []

    def load_properties(self):
        with open(self.file_location, 'r') as file:
            lines = file.readlines()

        camera_chunks = self._split_camera_chunks(lines)
        for chunk in camera_chunks:
            properties = {}
            for line in chunk:
                if line.startswith('pose'):
                    # Parse pose properties separately
                    pose_values = line.strip().split(' ')[1:]
                    properties['pose_X'] = float(pose_values[0])
                    properties['pose_Y'] = float(pose_values[1])
                    properties['pose_Z'] = float(pose_values[2])
                    properties['pose_r'] = float(pose_values[3])
                    properties['pose_p'] = float(pose_values[4])
                    properties['pose_y'] = float(pose_values[5])
                else:
                    key, value = line.strip().split(':')
                    properties[key.strip()] = value.strip()

            try:
                self._validate_property_types(properties)
                self.camera_properties.append(
                    CameraProperties(
                        topic_name=properties['topic_name'],
                        pose=CamPosition(
                            X=float(properties['pose_X']),
                            Y=float(properties['pose_Y']),
                            Z=float(properties['pose_Z']),
                            r=float(properties['pose_r']),
                            p=float(properties['pose_p']),
                            y=float(properties['pose_y']),
                        ),
                        horizontal_fov=float(properties['horizontal_fov']),
                        img_width=int(properties['img_width']),
                        img_height=int(properties['img_height']),
                        clip_near=float(properties['clip_near']),
                        clip_far=float(properties['clip_far']),
                        lens_type=properties['lens_type'],
                        cutoff_angle=float(properties['cutoff_angle']),
                        framerate=int(properties['framerate'])
                    )
                )
            except ValueError as e:
                print(f"Error: Incorrect data type in property: {str(e)}")
                return False
        return True


    def _split_camera_chunks(self, lines):
        camera_chunks = []
        chunk = []
        for line in lines:
            if line.strip() == '':
                if chunk:
                    camera_chunks.append(chunk)
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            camera_chunks.append(chunk)
        return camera_chunks

    def _validate_property_types(self, properties):
        for key, value in properties.items():
            if key.startswith('pose_'):
                # Skip pose properties, as they have different data types
                continue

            if key == 'topic_name':
                if not isinstance(value, str):
                    raise ValueError(f"Invalid data type for 'topic_name': expected str, found {type(value)}")
            elif key == 'lens_type':
                if not isinstance(value, str):
                    raise ValueError(f"Invalid data type for 'lens_type': expected str, found {type(value)}")
            else:
                try:
                    float(value)  # Check if the value can be converted to float
                except ValueError:
                    raise ValueError(f"Invalid data type for '{key}': expected float, found {type(value)}")

    def get_all_topic_names(self) -> List[str]:
        return [cam_property.topic_name for cam_property in self.camera_properties]

    def get_camera_properties(self, topic_name: str) -> CameraProperties:
        for cam_property in self.camera_properties:
            if cam_property.topic_name == topic_name:
                return cam_property

        raise ValueError(f"No camera properties found for topic_name '{topic_name}'")

    def get_num_cameras(self) -> int:
        return len(self.camera_properties)
