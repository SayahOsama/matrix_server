from flask import Flask, request, jsonify

import sys
from PIL import Image
import json

app = Flask(__name__)

# this script does the following:
# if the gif's dimentions are bigger than 32x32 then the gif will be compressed, but the size relation of the dimentions will be preserved.
# if the the gif's dimentions are smaller than 32x32 then it will not be resized, the gif will be centered.

# gamma corrects each RGB value in the frame
def gamma_correct_frame(frame):
    for i in range(len(frame)):
        frame[i] = [gamma8[frame[i][0]], gamma8[frame[i][1]], gamma8[frame[i][2]]]
    return frame


# goes over all the frames and compares the frame[i] and frame[i-1] and returns frame[i] with all the identical colors with frame[i-1] deleted.
def compress_frames(frames):
    length = len(frames)
    compressed_frames = []
    for i in range(length - 1, 0, -1):
        frame = delete_indetical_colors(frames[i - 1], frames[i])
        compressed_frames.append(frame)
    compressed_frames.append(frames[0])
    compressed_frames.reverse()
    return compressed_frames


# check if the color is in the colors list.
def colors_exists(color):
    for i in range(len(colors)):
        if (colors[i] == color):
            return True
    return False


# return index of the color in the colors list.
def mapped_colors(color):
    for i in range(len(colors)):
        if (colors[i] == color):
            return i


# in every index where the two frames have the same color, put -1 in frame.
def delete_indetical_colors(prev_frame, frame):
    for i in range(len(frame)):
        if (frame[i] == prev_frame[i]):
            frame[i] = -1
    return frame


# replace every interval that has the same colors as neighbours with [color,start_index,length] such as color is the index of color in the colors list,
# start_index is the start index of the interval and length is the number of neighbours with identical colors in the interval.
def compress_identical_pixel_colors(frame):
    res_frame = []
    if len(frame) > 0 and frame[0] != -1:
        length = 1
        start_index = 0
        curr_color = frame[0]
        colors.append(frame[0])
    else:
        length = 0
        start_index = 0
        curr_color = []
    for i in range(1, len(frame)):
        if (frame[i] == -1):
            if (length > 0):
                res_frame.append([mapped_colors(curr_color), start_index, length])
            length = 0
            continue
        if not colors_exists(frame[i]):
            colors.append(frame[i])

        if (length == 0):
            start_index = i
            length = 1
            curr_color = frame[i]
        else:
            if (frame[i] == curr_color):
                length = length + 1
            else:
                res_frame.append([mapped_colors(curr_color), start_index, length])
                length = 1
                curr_color = frame[i]
                start_index = i
    if (length > 0):
        res_frame.append([mapped_colors(curr_color), start_index, length])
    return res_frame


# calls compress_frames(frames) and then calls compress_identical_pixel_colors for each frame and returns.
def compress_gif(frames):
    compressed_frames = compress_frames(frames)
    for i in range(len(compressed_frames)):
        compressed_frames[i] = compress_identical_pixel_colors(compressed_frames[i])
    return compressed_frames


# resize the gif to 32x32 if its bigger. and then compress the frames of the gif and create a json with all the relevant data for the gif.
def convert_image_to_json(im, size):
    # Open image file
    # im = Image.open(input_file_path)
    # If it is 'GIF', then the file is a GIF
    gif = False
    if im.format == 'GIF':
        gif = True
    frame_num = None
    resized_frames = []
    if gif:
        frame_num = im.n_frames
    else:
        frame_num = 1

    # Iterate over each frame in the input GIF
    for frame in range(frame_num):
        im.seek(frame)  # Go to the current frame
        current_frame = im.copy()  # Create a copy of the current frame
        current_frame = current_frame.quantize(64)
        current_frame.thumbnail(size, Image.LANCZOS)  # Resize the frame to the specified size
        height = current_frame.height
        width = current_frame.width
        resized_frames.append(current_frame)  # Add the resized frame to the list

    frame = []
    frames = []
    gif_json = {}

    gif_json["width"] = width
    gif_json["height"] = height
    frame_num = min(12, len(resized_frames))
    gif_json["frames"] = frame_num

    # Iterate through frames and pixels, top row first
    for z in range(frame_num):
        # Convert to RGB

        rgb_im = resized_frames[z].convert('RGB')
        i = 0

        for y in range(height):
            for x in range(width):

                # Get RGB values of each pixel
                r, g, b = rgb_im.getpixel((x, y))
                if (i < NUM_LEDS):
                    frame.append([r, g, b])
                    i += 1

        frames.append(gamma_correct_frame(frame))
        # frames.append(frame)
        frame = []

    compressed_frames = compress_gif(frames)
    frame_sizes = []
    for i in range(len(compressed_frames)):
        frame_sizes.append(len(compressed_frames[i]))
    gif_json["colors"] = len(colors)
    gif_json["colors_palette"] = colors
    gif_json["frame_sizes"] = frame_sizes
    gif_json["animation"] = compressed_frames
    return gif_json


# size = 32,32
NUM_LEDS = 1024
colors = []
height = None
width = None
gamma8 = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
    2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
    5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10,
    10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
    17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
    25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
    37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
    51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
    69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
    90, 92, 93, 95, 96, 98, 99, 101, 102, 104, 105, 107, 109, 110, 112, 114,
    115, 117, 119, 120, 122, 124, 126, 127, 129, 131, 133, 135, 137, 138, 140, 142,
    144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 167, 169, 171, 173, 175,
    177, 180, 182, 184, 186, 189, 191, 193, 196, 198, 200, 203, 205, 208, 210, 213,
    215, 218, 220, 223, 225, 228, 231, 233, 236, 239, 241, 244, 247, 249, 252, 255]



@app.route('/process', methods=['POST'])
def process_image():
    colors = []
    height = None
    width = None
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']  # Access the file
    size1 = request.form['size1']  # Access size1
    size2 = request.form['size2']  # Access size2

    try:
        size = (int(size1), int(size2))
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid size values"}), 400

    try:
        image = Image.open(file)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to process image: {str(e)}"}), 400

    res = convert_image_to_json(image, size)

    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
