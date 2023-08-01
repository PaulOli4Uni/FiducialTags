# ChatGpt used to generate base

import cv2


def extract_frames(video_path, num_frames):
    # Open the video file
    video = cv2.VideoCapture(video_path)

    # Get total number of frames in the video
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate the step size to evenly sample frames
    step = max(total_frames // num_frames, 1)

    # Initialize variables
    frames = []
    frame_count = 0

    while frame_count < total_frames:
        # Read the current frame
        ret, frame = video.read()

        if ret:
            # Add the frame to the list
            frames.append(frame)

            # Skip frames based on the step size
            frame_count += step
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        else:
            break

    # Release the video capture object
    video.release()

    return frames


# Example usage:
video_path = 'Khan_Phone.mp4'
num_frames = 20

frame_list = extract_frames(video_path, num_frames)

# Access the extracted frames
for i, frame in enumerate(frame_list):
    cv2.imwrite(f"frame_{i}.png", frame)  # Save the frames as images
