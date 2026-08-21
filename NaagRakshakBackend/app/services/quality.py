import cv2
import numpy as np
from PIL import Image

class ImageQualityAnalyzer:
    @staticmethod
    def analyze_quality(pil_image: Image.Image) -> float:
        # Convert PIL to OpenCV BGR numpy array
        img_np = np.array(pil_image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # 1. Laplacian Variance (Blur Metric)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Scale blur score: 0 to 500+ -> normalized [0.0, 1.0]
        blur_score = min(1.0, laplacian_var / 350.0)

        # 2. Contrast Analysis (Standard deviation of pixel intensities)
        contrast_std = np.std(gray)
        contrast_score = min(1.0, contrast_std / 75.0)

        # 3. Brightness/Exposure Check (Optimal mean around 80-180)
        brightness_mean = np.mean(gray)
        if 60 <= brightness_mean <= 200:
            exposure_score = 1.0
        else:
            exposure_score = max(0.2, 1.0 - abs(brightness_mean - 128) / 128.0)

        # Composite Quality Score Q in [0.0, 1.0]
        quality_score = (0.5 * blur_score) + (0.3 * contrast_score) + (0.2 * exposure_score)
        return float(np.round(quality_score, 3))
