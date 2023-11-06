import cv2

def halve_fps(input_video, output_video):
    # Open the input video
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("Error: Could not open input video.")
        return

    # Get the original FPS and frame count
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate the new FPS (halved)
    new_fps = original_fps / 2.0

    # Get the video's width and height
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create VideoWriter for the output video with the 'mp4v' codec (common for .MP4)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' codec for .MP4
    out = cv2.VideoWriter(output_video, fourcc, new_fps, (width, height))

    # Set the new FPS as metadata
    out.set(cv2.CAP_PROP_FPS, new_fps)

    # Read and write frames while halving the frame rate
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % 2 == 0:
            out.write(frame)

        frame_number += 1

    # Release video objects
    cap.release()
    out.release()


if __name__ == "__main__":
    input_video = '/home/paul/Sim_Analysis/Verification/Dynamic_Tests/vid_Test2/a_edit.mp4'  # Replace with your input video file
    output_video = '/home/paul/Sim_Analysis/Verification/Dynamic_Tests/vid_Test2/a_edit_fps.mp4'

    halve_fps(input_video, output_video)
