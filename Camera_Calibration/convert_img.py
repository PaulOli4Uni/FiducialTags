import os
import glob
from PIL import Image
import pyheif

def heic_to_png(heic_path, output_dir):
    # Open the HEIC file
    heif_file = pyheif.read(heic_path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )

    # Convert to PNG and save in the output directory
    base_name = os.path.basename(heic_path)
    output_path = os.path.join(output_dir, os.path.splitext(base_name)[0] + ".png")
    image.save(output_path, "PNG")

# Set the input and output directories
input_dir = "Iphone Cal"  # Replace with the directory path containing the .heic photos
output_dir = "Iphone_Cal_png"  # Replace with the directory path where the converted .png files will be saved

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get a list of all .heic files in the input directory
heic_files = glob.glob(os.path.join(input_dir, "*.heic"))

# Iterate through each .heic file and convert to .png
for heic_file in heic_files:
    heic_to_png(heic_file, output_dir)
    print(f"Converted: {heic_file}")

print("Conversion completed!")
