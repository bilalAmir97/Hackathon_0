"""Image Validator for Facebook & Instagram MCP Server.

Validates image files for Facebook and Instagram posting requirements:
- Format validation (JPEG, PNG, GIF)
- Size validation (file size limits)
- Dimension validation (min/max width/height)
- Aspect ratio validation (Instagram only)
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image


class ImageValidator:
    """Validates images for Facebook and Instagram posting."""

    # Facebook image requirements
    FACEBOOK_MAX_SIZE_MB = 4
    FACEBOOK_MIN_WIDTH = 200
    FACEBOOK_MIN_HEIGHT = 200
    FACEBOOK_RECOMMENDED_MAX_WIDTH = 2048
    FACEBOOK_RECOMMENDED_MAX_HEIGHT = 2048
    FACEBOOK_FORMATS = {'JPEG', 'PNG', 'GIF'}

    # Instagram image requirements
    INSTAGRAM_MAX_SIZE_MB = 8
    INSTAGRAM_MIN_WIDTH = 320
    INSTAGRAM_MIN_ASPECT_RATIO = 0.8  # 4:5
    INSTAGRAM_MAX_ASPECT_RATIO = 1.91  # 1.91:1
    INSTAGRAM_FORMATS = {'JPEG', 'PNG'}  # GIF not supported for static posts

    def __init__(self, facebook_max_size_mb: Optional[float] = None,
                 instagram_max_size_mb: Optional[float] = None):
        """
        Initialize ImageValidator.

        Args:
            facebook_max_size_mb: Override default Facebook max size (MB)
            instagram_max_size_mb: Override default Instagram max size (MB)
        """
        self.facebook_max_size_mb = facebook_max_size_mb or self.FACEBOOK_MAX_SIZE_MB
        self.instagram_max_size_mb = instagram_max_size_mb or self.INSTAGRAM_MAX_SIZE_MB

    def get_image_info(self, image_path: str) -> Dict[str, any]:
        """
        Get image information without validation.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image info (format, size, width, height, aspect_ratio)

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If file is not a valid image
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {image_path}")

        # Get file size in MB
        file_size_mb = path.stat().st_size / (1024 * 1024)

        try:
            with Image.open(path) as img:
                width, height = img.size
                format_name = img.format
                aspect_ratio = width / height if height > 0 else 0

                return {
                    'path': str(path.absolute()),
                    'format': format_name,
                    'size_mb': round(file_size_mb, 2),
                    'width': width,
                    'height': height,
                    'aspect_ratio': round(aspect_ratio, 2)
                }
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

    def calculate_aspect_ratio(self, width: int, height: int) -> float:
        """
        Calculate aspect ratio from width and height.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Aspect ratio (width/height)
        """
        if height == 0:
            return 0.0
        return width / height

    def validate_facebook_image(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image for Facebook posting.

        Requirements:
        - Format: JPEG, PNG, or GIF
        - Max size: 4MB (configurable)
        - Min dimensions: 200x200px
        - Recommended max: 2048x2048px (warning only)

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        try:
            info = self.get_image_info(image_path)
        except (FileNotFoundError, ValueError) as e:
            return False, str(e)

        # Validate format
        if info['format'] not in self.FACEBOOK_FORMATS:
            return False, (
                f"Invalid format '{info['format']}'. "
                f"Facebook supports: {', '.join(self.FACEBOOK_FORMATS)}"
            )

        # Validate file size
        if info['size_mb'] > self.facebook_max_size_mb:
            return False, (
                f"File size {info['size_mb']}MB exceeds "
                f"Facebook limit of {self.facebook_max_size_mb}MB"
            )

        # Validate minimum dimensions
        if info['width'] < self.FACEBOOK_MIN_WIDTH or info['height'] < self.FACEBOOK_MIN_HEIGHT:
            return False, (
                f"Image dimensions {info['width']}x{info['height']}px are below "
                f"minimum {self.FACEBOOK_MIN_WIDTH}x{self.FACEBOOK_MIN_HEIGHT}px"
            )

        # Check recommended max dimensions (warning only, not blocking)
        if (info['width'] > self.FACEBOOK_RECOMMENDED_MAX_WIDTH or
                info['height'] > self.FACEBOOK_RECOMMENDED_MAX_HEIGHT):
            # Note: This is a recommendation, not a hard limit
            # We return True but could log a warning
            pass

        return True, None

    def validate_instagram_image(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image for Instagram posting.

        Requirements:
        - Format: JPEG or PNG (no GIF)
        - Max size: 8MB (configurable)
        - Min width: 320px
        - Aspect ratio: 4:5 (0.8) to 1.91:1

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """
        try:
            info = self.get_image_info(image_path)
        except (FileNotFoundError, ValueError) as e:
            return False, str(e)

        # Validate format
        if info['format'] not in self.INSTAGRAM_FORMATS:
            return False, (
                f"Invalid format '{info['format']}'. "
                f"Instagram supports: {', '.join(self.INSTAGRAM_FORMATS)}"
            )

        # Validate file size
        if info['size_mb'] > self.instagram_max_size_mb:
            return False, (
                f"File size {info['size_mb']}MB exceeds "
                f"Instagram limit of {self.instagram_max_size_mb}MB"
            )

        # Validate minimum width
        if info['width'] < self.INSTAGRAM_MIN_WIDTH:
            return False, (
                f"Image width {info['width']}px is below "
                f"minimum {self.INSTAGRAM_MIN_WIDTH}px"
            )

        # Validate aspect ratio
        aspect_ratio = info['aspect_ratio']
        if aspect_ratio < self.INSTAGRAM_MIN_ASPECT_RATIO:
            return False, (
                f"Aspect ratio {aspect_ratio} is below minimum "
                f"{self.INSTAGRAM_MIN_ASPECT_RATIO} (4:5 portrait)"
            )

        if aspect_ratio > self.INSTAGRAM_MAX_ASPECT_RATIO:
            return False, (
                f"Aspect ratio {aspect_ratio} exceeds maximum "
                f"{self.INSTAGRAM_MAX_ASPECT_RATIO} (1.91:1 landscape)"
            )

        return True, None
