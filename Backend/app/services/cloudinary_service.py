from typing import Optional, Dict, Any, Tuple
import os
import uuid
from pathlib import Path
from app.config import settings
from app.core.logging import logger

class CloudinaryService:
    def __init__(self):
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self._configured = False
        self._init_cloudinary()

    def _init_cloudinary(self):
        if self.cloud_name and self.api_key and self.api_secret:
            try:
                import cloudinary
                cloudinary.config(
                    cloud_name=self.cloud_name,
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    secure=True
                )
                self._configured = True
                logger.info("Cloudinary configured successfully")
            except Exception as e:
                logger.warning(f"Failed to configure Cloudinary: {e}")
                self._configured = False
        else:
            self._configured = False

    @property
    def is_configured(self) -> bool:
        return self._configured

    def upload_image_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        folder: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Upload raw image bytes to Cloudinary with local storage fallback.
        
        Returns:
            Tuple[str, Optional[str]]: (secure_url, public_id)
        """
        target_folder = folder or settings.CLOUDINARY_FOLDER
        
        # 1. Try Cloudinary if configured
        if self.is_configured:
            try:
                import cloudinary.uploader
                upload_result = cloudinary.uploader.upload(
                    image_bytes,
                    folder=target_folder,
                    resource_type="image",
                    public_id=f"{Path(filename).stem}_{uuid.uuid4().hex[:8]}"
                )
                secure_url = upload_result.get("secure_url") or upload_result.get("url")
                public_id = upload_result.get("public_id")
                return secure_url, public_id
            except Exception as e:
                logger.warning(f"Cloudinary image upload failed ({e}). Saving to local storage.")

        # 2. Local storage fallback
        images_dir = Path(settings.STORAGE_DIR) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        local_path = images_dir / unique_name
        local_path.write_bytes(image_bytes)
        
        # Return URL pointing to FastAPI static storage mount
        local_url = f"/api/storage/images/{unique_name}"
        return local_url, None

    def upload_file(
        self,
        file_path: str,
        folder: Optional[str] = None,
        resource_type: str = "raw"
    ) -> Tuple[str, Optional[str]]:
        """Upload file to Cloudinary with local fallback."""
        target_folder = folder or f"{settings.CLOUDINARY_FOLDER}/documents"

        if self.is_configured:
            try:
                import cloudinary.uploader
                upload_result = cloudinary.uploader.upload(
                    file_path,
                    folder=target_folder,
                    resource_type=resource_type
                )
                secure_url = upload_result.get("secure_url") or upload_result.get("url")
                public_id = upload_result.get("public_id")
                return secure_url, public_id
            except Exception as e:
                logger.warning(f"Cloudinary file upload failed ({e}). Falling back to local URL.")

        filename = Path(file_path).name
        local_url = f"/api/storage/documents/{filename}"
        return local_url, None

cloudinary_service = CloudinaryService()
