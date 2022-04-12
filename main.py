import argparse
import datetime

import cv2
import numpy as np
from PIL import Image
import pytesseract
from tqdm import tqdm


NOISE_INTENSITY = 10  # max variation; in grey levels
SMOOTH_KERNEL_SIZE = 5
DIFF_PX_COUNT_THRES = 10
MIN_OCR_IMG_SIZE = 32  # pixels
CHAR_CONVERSIONS = {",": "，", ";": "；", ":": "：", "!": "！", "?": "？"}


def _crop_subtitle(frame, args):
    # Crop bottom strip
    frame_height = frame.shape[0]
    separator_px = round(frame_height * args["separator"])
    bottom_img = frame[separator_px:, :, :]
    grey_img = cv2.cvtColor(bottom_img, cv2.COLOR_BGR2GRAY)
    inverted_img = 255 - grey_img

    # Detect rectangle
    _, binary_img = cv2.threshold(inverted_img, NOISE_INTENSITY, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    
    max_rect = contours[0]
    max_rect_area = 0
    for contour in contours:
        rect = cv2.boundingRect(contour)
        rect_area = rect[2] * rect[3]
        if rect_area > max_rect_area:
            max_rect_area = rect_area
            max_rect = rect

    x, y, w, h = max_rect
    if w < MIN_OCR_IMG_SIZE or h < MIN_OCR_IMG_SIZE:
        return None

    x = x + 1  # shrink the rectangle to get rid of white edge pixels
    y = y + 1
    w = w - 2
    h = h - 2

    # Crop subtitle image
    subtitle_img = inverted_img[y:y+h, x:x+w]
    return subtitle_img


def _is_same_subtitle_img(last_subtitle_img, subtitle_img):
    char_width = (last_subtitle_img.shape[0] + subtitle_img.shape[0]) / 2  # approximate
    if abs(last_subtitle_img.shape[1] - subtitle_img.shape[1]) >= char_width / 2:
        return False
    
    resized_subtitle_img = cv2.resize(subtitle_img, (last_subtitle_img.shape[1], last_subtitle_img.shape[0]))
    diff = np.absolute(resized_subtitle_img.astype(np.int16) - last_subtitle_img.astype(np.int16)).astype(np.uint8)
    smoothed_diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, np.ones((SMOOTH_KERNEL_SIZE, SMOOTH_KERNEL_SIZE), np.uint8))
    diff_px_count = np.sum(smoothed_diff > NOISE_INTENSITY)
    
    if diff_px_count > DIFF_PX_COUNT_THRES:
        return False
    
    return True


def _ocr(img):
    img = Image.fromarray(img)
    text = pytesseract.image_to_string(img, lang=args["lang"])
    text = text.strip().replace(" ", "")
    for key in CHAR_CONVERSIONS:
        text = text.replace(key, CHAR_CONVERSIONS[key])

    return text


def _video2sbv(args):
    # Read video file
    video_cap = cv2.VideoCapture(args["video_file"])
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    num_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

    subtitles = []
    last_subtitle_img = None

    for i in tqdm(range(num_frames)):
        # Extract a frame
        ret, frame = video_cap.read()
        if not ret:
            break

        # Crop subtitle image
        subtitle_img = _crop_subtitle(frame, args)
        if subtitle_img is None:
            last_subtitle_img = None
            continue

        # Check if it is same as the last subtitle image
        if last_subtitle_img is not None:
            is_same_subtitle_img = _is_same_subtitle_img(last_subtitle_img, subtitle_img)
        else:
            is_same_subtitle_img = False
        last_subtitle_img = subtitle_img

        # OCR
        if not is_same_subtitle_img:
            text = _ocr(subtitle_img)

        # Calculate timestamps
        t_start = datetime.timedelta(milliseconds=i * (1000 / fps))
        t_end = datetime.timedelta(milliseconds=(i + 1) * (1000 / fps))
        t_start_str = "{}:{:02d}:{:02d}.{:03d}".format(
            t_start.seconds // 3600, t_start.seconds // 60, t_start.seconds % 60, t_start.microseconds // 1000)
        t_end_str = "{}:{:02d}:{:02d}.{:03d}".format(
            t_end.seconds // 3600, t_end.seconds // 60, t_end.seconds % 60, t_end.microseconds // 1000)

        # Store results
        if len(subtitles) > 0 and (is_same_subtitle_img or text == subtitles[-1]["text"]):
            subtitles[-1]["t_end"] = t_end_str
        else:
            subtitles.append({"t_start": t_start_str,
                              "t_end": t_end_str,
                              "text": text})
            print(f"Frame {i}: {text}")

    # Write as SBV file
    with open(args["sbv_file"], "w") as f:
        for subtitle in subtitles:
            f.write(subtitle["t_start"])
            f.write(",")
            f.write(subtitle["t_end"])
            f.write("\n")
            f.write(subtitle["text"])
            f.write("\n\n")


def _get_parser():
    parser = argparse.ArgumentParser(description="Video embedded subtitles to SBV")
    parser.add_argument("video_file", help="video file path")
    parser.add_argument("sbv_file", help="output SBV file path")
    parser.add_argument("--separator", type=float, default=0.87, help="position of the horizontal line separating the subtitles, in fraction of video height")
    parser.add_argument("--lang", default="chi_tra", help="language of the subtitles, default is chi_tra")
    return parser


if __name__ == "__main__":
    parser = _get_parser()
    args = vars(parser.parse_args())
    
    _video2sbv(args)