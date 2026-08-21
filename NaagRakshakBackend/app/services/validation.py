import io
from PIL import Image
from fastapi import HTTPException, status
from app.config import settings

# Enforce PIL Decompression Bomb Defense
Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS

ALLOWED_MAGIC_BYTES = [
    b'\xff\xd8\xff',          # JPEG
    b'\x89PNG\r\n\x1a\n',     # PNG
    b'RIFF'                   # WEBP (starts with RIFF...WEBP)
]

class ImageValidationService:
    @staticmethod
    def validate_image_stream(file_bytes: bytes) -> Image.Image:
        # 1. Check Payload Size Cap
        if len(file_bytes) > settings.MAX_PAYLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image size exceeds maximum allowed limit of {settings.MAX_PAYLOAD_BYTES / (1024*1024):.0f}MB."
            )

        if len(file_bytes) < 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file size is too small (minimum 1KB required)."
            )

        # 2. Magic Byte Check
        header = file_bytes[:12]
        is_valid_format = False
        if header.startswith(b'\xff\xd8\xff') or header.startswith(b'\x89PNG') or (header.startswith(b'RIFF') and b'WEBP' in header):
            is_valid_format = True

        if not is_valid_format:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported image format. Allowed formats: JPEG, PNG, WEBP."
            )

        # 3. Readability & Resolution Verification
        try:
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            width, height = pil_img.size

            if width < settings.MIN_IMAGE_RES or height < settings.MIN_IMAGE_RES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image resolution too low ({width}x{height}). Minimum required resolution is {settings.MIN_IMAGE_RES}x{settings.MIN_IMAGE_RES}."
                )

            return pil_img
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or invalid image buffer: {str(e)}"
            )
