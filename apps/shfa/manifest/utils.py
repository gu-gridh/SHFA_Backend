from typing import Dict, List, Optional
import logging
from iiif_prezi3 import Manifest

logger = logging.getLogger(__name__)

def validate_iiif_manifest(manifest_dict: Dict) -> bool:
    """Validate IIIF manifest structure using iiif-prezi3."""
    try:
        # Try to create a Manifest object from the dictionary
        Manifest(**manifest_dict)
        return True
    except Exception as e:
        logger.error(f"IIIF manifest validation failed: {str(e)}")
        return False

def build_iiif_url(base_url: str, file_path: str) -> str:
    """Build proper IIIF URL from components."""
    if file_path.startswith('http'):
        return file_path
    
    return f"{base_url.rstrip('/')}/{file_path.lstrip('/')}"

def sanitize_manifest_data(data: Dict) -> Dict:
    """Clean and sanitize manifest data."""
    cleaned_data = {}
    
    for key, value in data.items():
        if value is not None and value != "":
            if isinstance(value, dict):
                cleaned_value = sanitize_manifest_data(value)
                if cleaned_value:
                    cleaned_data[key] = cleaned_value
            elif isinstance(value, list):
                cleaned_list = [v for v in value if v is not None and v != ""]
                if cleaned_list:
                    cleaned_data[key] = cleaned_list
            else:
                cleaned_data[key] = value
    
    return cleaned_data

def get_image_dimensions(image) -> tuple:
    """Get image dimensions with fallbacks."""
    width = getattr(image, 'width', None) or 1000
    height = getattr(image, 'height', None) or 800
    return width, height

def get_thumbnail(image) -> Optional[str]:
    """Get thumbnail URL for an image."""
    if hasattr(image, 'thumbnail'):
        return image.thumbnail.url if image.thumbnail else None
    elif hasattr(image, 'image'):
        return image.image.url if image.image else None
    return None