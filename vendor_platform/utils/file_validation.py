from django.core.exceptions import ValidationError
import os
from PIL import Image

class FileSizeValidator:
    def __init__(self, limit_mb=5):
        self.limit_mb = limit_mb
        self.limit_bytes = limit_mb * 1024 * 1024
        
    def __call__(self, value):
        if value.size > self.limit_bytes:
            raise ValidationError(f'File size must be under {self.limit_mb}MB.')
            
class ImageDimensionValidator:
    def __init__(self, max_width=None, max_height=None):
        self.max_width = max_width
        self.max_height = max_height
        
    def __call__(self, value):
        try:
            with Image.open(value) as img:
                width, height = img.size
                
                if self.max_width and width > self.max_width:
                    raise ValidationError(f'Image width must be at most {self.max_width}px.')
                    
                if self.max_height and height > self.max_height:
                    raise ValidationError(f'Image height must be at most {self.max_height}px.')
                    
        except (IOError, AttributeError):
            # Can't open the image or not an image
            pass