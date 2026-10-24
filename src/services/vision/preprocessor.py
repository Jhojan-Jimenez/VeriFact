import cv2
import numpy as np


class ImagePreprocessor:
    """Preprocesses receipt images for optimal OCR and barcode decoding."""

    @staticmethod
    def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
        """Decode raw image bytes into an OpenCV BGR numpy array."""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image from provided bytes.")
        return img

    @classmethod
    def preprocess_for_ocr(cls, image: np.ndarray) -> np.ndarray:
        """Apply grayscale, CLAHE contrast enhancement, and adaptive thresholding."""
        # 1. Convert to Grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 2. Resize if small or excessively large
        height, width = gray.shape[:2]
        if max(height, width) > 2400:
            scale = 2400 / max(height, width)
            gray = cv2.resize(gray, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
        elif max(height, width) < 800:
            scale = 800 / max(height, width)
            gray = cv2.resize(gray, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_CUBIC)

        # 3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 4. Slight Gaussian Blur to eliminate high-frequency noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # 5. Otsu's thresholding
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    @classmethod
    def deskew(cls, image: np.ndarray) -> np.ndarray:
        """Detect dominant orientation angle and deskew image."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        coords = np.column_stack(np.where(gray > 0))
        if len(coords) < 100:
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If angle is minimal, ignore
        if abs(angle) < 0.5 or abs(angle) > 45:
            return image

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated
