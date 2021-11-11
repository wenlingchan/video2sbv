import argparse
import datetime

import cv2
from PIL import Image
import pytesseract
from tqdm import tqdm


CHAR_CONVERSIONS = {",": "，", ";": "；", ":": "：", "!": "！", "?": "？"}


def _video2sbv(args):
    # Read video file
    video_cap = cv2.VideoCapture(args["video_file"])
    fps = video_cap.get(cv2.CAP_PROP_FPS)
    num_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

    subtitles = []

    for i in tqdm(range(num_frames)):
        # Extract a frame
        ret, frame = video_cap.read()
        if not ret:
            break

        # Crop subtitle image
        frame_height = frame.shape[0]
        separator_px = round(frame_height * args["separator"])
        subtitle_img = frame[separator_px:, :, :]

        # Threshold white text
        subtitle_img = cv2.inRange(subtitle_img, (245, 245, 245), (255, 255, 255))

        # OCR
        subtitle_img = Image.fromarray(subtitle_img)
        text = pytesseract.image_to_string(subtitle_img, lang=args["lang"])
        text = text.strip().replace(" ", "")
        for key in CHAR_CONVERSIONS:
            text = text.replace(key, CHAR_CONVERSIONS[key])

        if len(text) == 0:
            continue

        # Calculate timestamps
        t_start = datetime.timedelta(milliseconds=i * (1000 / fps))
        t_end = datetime.timedelta(milliseconds=(i + 1) * (1000 / fps))
        t_start_str = "{}:{:02d}:{:02d}.{:03d}".format(
            t_start.seconds // 3600, t_start.seconds // 60, t_start.seconds, t_start.microseconds // 1000)
        t_end_str = "{}:{:02d}:{:02d}.{:03d}".format(
            t_end.seconds // 3600, t_end.seconds // 60, t_end.seconds, t_end.microseconds // 1000)

        # Store result
        if len(subtitles) > 0 and subtitles[-1]["text"] == text:
            subtitles[-1]["t_end"] = t_end_str
        else:
            subtitles.append({"t_start": t_start_str,
                              "t_end": t_end_str,
                              "text": text})

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
    parser.add_argument("video_file", help="Video file path")
    parser.add_argument("sbv_file", help="Output SBV file path")
    parser.add_argument("--separator", type=float, default=0.87, help="Position of the horizontal line separating the subtitles, in fraction of video height")
    parser.add_argument("--lang", default="chi_tra", help="Language of the subtitles")
    return parser


if __name__ == "__main__":
    parser = _get_parser()
    args = vars(parser.parse_args())
    
    _video2sbv(args)
