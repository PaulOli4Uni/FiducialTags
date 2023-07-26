import os

def FilePathToMarker(main_files_path, marker_file):
    marker_name = marker_file[:-4]  # Drops extension from string
    marker_name_no_id = marker_name.rsplit('_', 1)[0]  # Removes _idXX portion of name
    path_to_marker_file = os.path.join(main_files_path, "Markers", marker_name_no_id, marker_name, marker_file)
    return path_to_marker_file

def FilePathToModel(main_files_path, model_file):
    path_to_model_file = os.path.join(main_files_path, "Models", model_file[:-4], model_file)
    return path_to_model_file