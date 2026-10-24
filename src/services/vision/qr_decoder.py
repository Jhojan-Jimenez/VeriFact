import cv2
import numpy as np


class QRDecoder:
    """Decodes QR codes using pyzbar or OpenCV QRCodeDetector fallback."""

    @classmethod
    def decode(cls, image: np.ndarray) -> list[str]:
        """Attempt to decode any 2D QR codes present in the image."""
        results: list[str] = []

        # 1. Try pyzbar if native library is available
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            decoded_objects = pyzbar_decode(image)
            for obj in decoded_objects:
                if obj.type == "QRCODE" and obj.data:
                    results.append(obj.data.decode("utf-8", errors="ignore"))
            if results:
                return results
        except Exception:
            # Fall back to OpenCV QRCodeDetector
            pass

        # 2. OpenCV QRCodeDetector (Pure OpenCV, no external libzbar dependency)
        try:
            detector = cv2.QRCodeDetector()
            # Try multi-detect first
            retval, decoded_info, _, _ = detector.detectAndDecodeMulti(image)
            if retval and any(decoded_info):
                return [info for info in decoded_info if info]

            # Try single QR detect
            data, _, _ = detector.detectAndDecode(image)
            if data:
                return [data]
        except Exception:
            pass

        return results
