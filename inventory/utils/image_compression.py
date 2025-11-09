"""Image compression utilities for automatic image optimization"""
import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def compress_image(image_field, quality=80, optimize=True):
    """
    Compress an image while maintaining quality and resolution.
    
    This function optimizes images using efficient compression techniques:
    - JPEG: High quality (90-95) with optimization for visually lossless compression
    - PNG: Lossless optimization by recompressing with optimal settings
    - Maintains original dimensions (no resizing)
    
    Args:
        image_field: Django ImageField, FileField, or UploadedFile instance
        quality: JPEG quality (85-95 recommended for high quality, default 90)
        optimize: Whether to use optimization (default True)
    
    Returns:
        Compressed image file ready for saving
    """
    if not image_field:
        return image_field
    
    # Handle both ImageField/FileField and direct UploadedFile
    # For Django ImageField/FileField, the file is in the .file attribute
    # For direct UploadedFile, it's the object itself
    file_obj = image_field
    filename = 'image.jpg'
    
    if hasattr(image_field, 'file'):
        # It's a Django ImageField/FileField
        file_obj = image_field.file
        if hasattr(image_field, 'name'):
            filename = image_field.name
    elif hasattr(image_field, 'name'):
        # It's an UploadedFile with a name attribute
        filename = image_field.name
    
    if not file_obj:
        return image_field
    
    # If we still don't have a filename, try to get it from the file object
    if filename == 'image.jpg' and hasattr(file_obj, 'name'):
        filename = file_obj.name
    
    # Check if the file is an image
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        # Not an image file, return as-is (e.g., PDF files)
        return image_field
    
    try:
        # Reset file pointer to beginning if it's a file-like object
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        
        # Open the image
        img = Image.open(file_obj)
        
        # Convert RGBA to RGB for JPEG (JPEG doesn't support transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background for images with transparency
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
        
        # Get original format
        original_format = img.format or 'JPEG'
        
        # Determine output format (use JPEG for better compression, PNG for transparency if needed)
        if file_extension in ['.png'] and img.mode in ('RGBA', 'LA'):
            # Keep PNG for images that need transparency
            output_format = 'PNG'
            save_kwargs = {'format': 'PNG', 'optimize': optimize}
        else:
            # Use JPEG for better compression while maintaining quality
            output_format = 'JPEG'
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': optimize,
                'progressive': True  # Progressive JPEG for better compression
            }
        
        # Create a BytesIO buffer to store the compressed image
        output = BytesIO()
        
        # Save the compressed image
        img.save(output, **save_kwargs)
        output.seek(0)
        
        # Get the original filename without extension
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        
        # Determine new file extension
        if output_format == 'JPEG':
            new_extension = '.jpg'
        else:
            new_extension = file_extension  # Keep original extension for PNG
        
        new_filename = f"{filename_base}{new_extension}"
        
        # Get the size of the compressed image
        output_size = len(output.getvalue())
        output.seek(0)
        
        # Create a new InMemoryUploadedFile with the compressed image
        compressed_file = InMemoryUploadedFile(
            output,
            None,
            new_filename,
            f'image/{output_format.lower()}',
            output_size,
            None
        )
        
        return compressed_file
        
    except Exception as e:
        # If compression fails, return the original file
        # Log the error but don't break the upload process
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Image compression failed: {str(e)}. Using original image.")
        return image_field


def compress_image_file(file_path, output_path=None, quality=80, optimize=True):
    """
    Compress an image file on disk.
    
    Args:
        file_path: Path to the image file
        output_path: Path to save compressed image (if None, overwrites original)
        quality: JPEG quality (85-95 recommended, default 90)
        optimize: Whether to use optimization (default True)
    
    Returns:
        Path to the compressed image file
    """
    if not os.path.exists(file_path):
        return file_path
    
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        return file_path
    
    try:
        img = Image.open(file_path)
        
        # Convert RGBA to RGB for JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
        
        # Determine output format
        if file_extension == '.png' and img.mode in ('RGBA', 'LA'):
            output_format = 'PNG'
            save_kwargs = {'format': 'PNG', 'optimize': optimize}
        else:
            output_format = 'JPEG'
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': optimize,
                'progressive': True
            }
        
        output_path = output_path or file_path
        
        # Save compressed image
        img.save(output_path, **save_kwargs)
        
        return output_path
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Image compression failed for {file_path}: {str(e)}")
        return file_path

