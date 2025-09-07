"""
Set up required MediaPipe model files for Glide.
"""

import os
import urllib.request
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def download_file(url: str, destination: str):
    """Download a file with progress indication"""
    logger.info(f"Downloading {os.path.basename(destination)}...")
    
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        sys.stdout.write(f'\rProgress: {percent:.1f}%')
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, destination, show_progress)
        sys.stdout.write('\n')  # New line after progress
        logger.info(f"✓ Downloaded to {destination}")
    except (urllib.error.URLError, OSError) as e:
        sys.stdout.write('\n')  # New line after progress
        logger.error(f"✗ Error downloading {url}: {e}")
        return False
    return True


def main():
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    # Model URLs
    models = [
        {
            "name": "Hand Landmarker",
            "url": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            "path": "models/hand_landmarker.task"
        },
        {
            "name": "Gesture Recognizer",
            "url": "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
            "path": "models/gesture_recognizer.task"
        }
    ]
    
    logger.info("Downloading MediaPipe Task models...\n")
    
    for model in models:
        if os.path.exists(model["path"]):
            logger.info(f"✓ {model['name']} already exists at {model['path']}")
        else:
            success = download_file(model["url"], model["path"])
            if not success:
                logger.error(f"Failed to download {model['name']}")
                sys.exit(1)
    
    logger.info("\nAll models downloaded successfully!")
    logger.info("\nYou can now run:")
    logger.info("  python main.py")


if __name__ == "__main__":
    main()