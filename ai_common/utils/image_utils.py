"""Image processing utilities"""

import base64
import io
import logging
from typing import Union, Optional
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class ImageUtils:
    """Utilities for image processing and conversion"""
    
    @staticmethod
    def image_to_base64(image_path: Union[str, Path]) -> str:
        """
        Convert image file to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error converting image to base64: {str(e)}")
    
    @staticmethod
    def base64_to_image(base64_string: str) -> 'Image.Image':
        """
        Convert base64 string to PIL Image
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            PIL Image object
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
            
        try:
            image_data = base64.b64decode(base64_string)
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"Error converting base64 to image: {str(e)}")
    
    @staticmethod
    def pil_to_base64(pil_image: 'Image.Image', format: str = 'PNG') -> str:
        """
        Convert PIL Image to base64 string
        
        Args:
            pil_image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Base64 encoded string
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
            
        try:
            buffer = io.BytesIO()
            pil_image.save(buffer, format=format)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error converting PIL image to base64: {str(e)}")
    
    @staticmethod
    def pil_to_numpy(pil_image: 'Image.Image') -> 'np.ndarray':
        """
        Convert PIL Image to numpy array
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            Numpy array representation
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy not available")
            
        try:
            return np.array(pil_image)
        except Exception as e:
            raise ValueError(f"Error converting PIL image to numpy: {str(e)}")
    
    @staticmethod
    def numpy_to_pil(np_array: 'np.ndarray') -> 'Image.Image':
        """
        Convert numpy array to PIL Image
        
        Args:
            np_array: Numpy array representation of image
            
        Returns:
            PIL Image object
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy not available")
            
        try:
            return Image.fromarray(np_array)
        except Exception as e:
            raise ValueError(f"Error converting numpy array to PIL image: {str(e)}")
    
    @staticmethod
    def pil_to_cv2(pil_image: 'Image.Image') -> 'np.ndarray':
        """
        Convert PIL Image to OpenCV format (BGR)
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            OpenCV image array (BGR format)
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV not available")
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy not available")
            
        try:
            # Convert PIL to RGB numpy array
            rgb_array = np.array(pil_image.convert('RGB'))
            # Convert RGB to BGR for OpenCV
            return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"Error converting PIL image to OpenCV format: {str(e)}")
    
    @staticmethod
    def cv2_to_pil(cv2_image: 'np.ndarray') -> 'Image.Image':
        """
        Convert OpenCV image (BGR) to PIL Image
        
        Args:
            cv2_image: OpenCV image array (BGR format)
            
        Returns:
            PIL Image object
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV not available")
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy not available")
            
        try:
            # Convert BGR to RGB
            rgb_array = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_array)
        except Exception as e:
            raise ValueError(f"Error converting OpenCV image to PIL format: {str(e)}")
    
    @staticmethod
    def save_image(image: Union['Image.Image', 'np.ndarray'], 
                   output_path: Union[str, Path], 
                   format: Optional[str] = None,
                   logger: Optional[logging.Logger] = None) -> None:
        """
        Save image to file
        
        Args:
            image: PIL Image or numpy array
            output_path: Path to save the image
            format: Image format (auto-detected if None)
            logger: Optional logger instance
        """
        log = logger or logging.getLogger(__name__)
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(image, np.ndarray):
                if not PIL_AVAILABLE:
                    raise ImportError("PIL/Pillow not available")
                image = Image.fromarray(image)
            
            if format is None:
                # Auto-detect format from file extension
                format = output_path.suffix.upper().lstrip('.')
                if format == 'JPG':
                    format = 'JPEG'
            
            image.save(output_path, format=format)
            log.info(f"Image saved to: {output_path}")
            
        except Exception as e:
            log.error(f"Error saving image to {output_path}: {str(e)}")
            raise
    
    @staticmethod
    def resize_image(image: 'Image.Image', 
                     size: tuple, 
                     resample: int = None) -> 'Image.Image':
        """
        Resize PIL Image
        
        Args:
            image: PIL Image object
            size: Target size as (width, height)
            resample: Resampling algorithm
            
        Returns:
            Resized PIL Image
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow not available")
            
        try:
            if resample is None:
                resample = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
            return image.resize(size, resample=resample)
        except Exception as e:
            raise ValueError(f"Error resizing image: {str(e)}")
    
    @staticmethod
    def validate_image_format(image_path: Union[str, Path]) -> bool:
        """
        Validate if file is a valid image format
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if valid image, False otherwise
        """
        if not PIL_AVAILABLE:
            return False
            
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
