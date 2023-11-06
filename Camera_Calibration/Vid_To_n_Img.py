import cv2
import os
import numpy as np

# Function to extract frames
def extract_frames(video_path, num_images, output_folder):
    # Make sure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Capture the video
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print("Error: Could not open video.")
        return

    # Get video properties
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    print(f"Total frames: {total_frames}, FPS: {fps}, Duration: {duration}s")

    # Calculate interval between frames to be captured
    interval = total_frames // num_images

    # Extract frames
    for i in range(num_images):
        # Set video to specific frame
        video.set(cv2.CAP_PROP_POS_FRAMES, i * interval)

        # Read the frame
        success, frame = video.read()
        if not success:
            print(f"Error: Could not read frame {i}.")
            break

        # Save frame as PNG image
        cv2.imwrite(os.path.join(output_folder, f"frame_{i:03d}.png"), frame)

    # Release the video capture object
    video.release()
    print("Extraction complete.")

# Parameters
video_path = '/home/paul/FiducialTags/Camera_Calibration/Canon_Video/Cal.MP4'  # Replace with your video path
num_images = 45  # Number of images to extract
output_folder = '/home/paul/FiducialTags/Camera_Calibration/Canon_Video'  # Output folder to save images

# Run the function
extract_frames(video_path, num_images, output_folder)
