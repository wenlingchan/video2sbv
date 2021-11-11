# video2sbv

Extract hardcoded subtitles from a video file and save as a SBV plain text file.
The SBV file may be uploaded to YouTube to supplement your video.

# Get started
```bash
sudo apt update
sudo apt install tesseract-ocr-chi-tra

git clone [URL of this repo]
cd video2sbc

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pillow pytesseract opencv-python-headless tqdm
```

# Run
```bash
python video2sbv.py path/to/video.mp4 path/to/subtitles.sbv
```
