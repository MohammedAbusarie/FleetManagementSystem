"""Django signals for automatic image compression and file cleanup"""
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.files.uploadedfile import UploadedFile
from .models import (
    Car, Equipment, CarImage, EquipmentImage, 
    FireExtinguisherImage, CalibrationCertificateImage
)
from .utils.image_compression import compress_image


def _should_compress_file(file_field):
    """Check if a file field should be compressed (only new uploads, not existing files)"""
    if not file_field:
        return False
    
    # Check if it's an UploadedFile (new file being uploaded)
    if isinstance(file_field, UploadedFile):
        return True
    
    # Check if it's a field with a file attribute that's an UploadedFile
    if hasattr(file_field, 'file'):
        file_obj = file_field.file
        if file_obj and isinstance(file_obj, UploadedFile):
            return True
    
    # Check if it's a field descriptor (ImageField/FileField) with an UploadedFile
    # This happens when the field hasn't been saved yet
    if hasattr(file_field, 'read'):
        # It's a file-like object
        return True
    
    return False


@receiver(pre_save, sender=Car)
def compress_car_main_image(sender, instance, **kwargs):
    """Automatically compress car main image before saving"""
    if _should_compress_file(instance.car_image):
        instance.car_image = compress_image(instance.car_image)


@receiver(pre_save, sender=Equipment)
def compress_equipment_main_image(sender, instance, **kwargs):
    """Automatically compress equipment main image before saving"""
    if _should_compress_file(instance.equipment_image):
        instance.equipment_image = compress_image(instance.equipment_image)


@receiver(pre_save, sender=CarImage)
def compress_car_image(sender, instance, **kwargs):
    """Automatically compress car images before saving"""
    if _should_compress_file(instance.image):
        instance.image = compress_image(instance.image)


@receiver(pre_save, sender=EquipmentImage)
def compress_equipment_image(sender, instance, **kwargs):
    """Automatically compress equipment images before saving"""
    if _should_compress_file(instance.image):
        instance.image = compress_image(instance.image)


@receiver(pre_save, sender=FireExtinguisherImage)
def compress_fire_extinguisher_image(sender, instance, **kwargs):
    """Automatically compress fire extinguisher images before saving"""
    if _should_compress_file(instance.image):
        instance.image = compress_image(instance.image)


@receiver(pre_save, sender=CalibrationCertificateImage)
def compress_calibration_certificate_image(sender, instance, **kwargs):
    """Automatically compress calibration certificate images before saving (only if it's an image)"""
    if _should_compress_file(instance.image):
        # Only compress if it's an image file (not PDF)
        file_extension = instance.image.name.lower().split('.')[-1] if '.' in instance.image.name else ''
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            instance.image = compress_image(instance.image)


def _delete_file_safely(file_field):
    """Delete file from storage if it exists."""
    if not file_field:
        return
    storage = getattr(file_field, 'storage', None)
    file_name = getattr(file_field, 'name', '')
    if storage and file_name:
        try:
            if storage.exists(file_name):
                storage.delete(file_name)
        except Exception:
            # Swallow exceptions to avoid breaking delete flow
            pass


@receiver(post_delete, sender=CarImage)
def delete_car_image_file(sender, instance, **kwargs):
    """Remove car image file from storage after record deletion."""
    _delete_file_safely(instance.image)


@receiver(post_delete, sender=Car)
def delete_car_main_image(sender, instance, **kwargs):
    """Remove main car image file from storage after car deletion."""
    _delete_file_safely(instance.car_image)


@receiver(post_delete, sender=EquipmentImage)
def delete_equipment_image_file(sender, instance, **kwargs):
    """Remove equipment gallery image file from storage after record deletion."""
    _delete_file_safely(instance.image)


@receiver(post_delete, sender=CalibrationCertificateImage)
def delete_calibration_certificate_file(sender, instance, **kwargs):
    """Remove calibration certificate file from storage after record deletion."""
    _delete_file_safely(instance.image)


@receiver(post_delete, sender=FireExtinguisherImage)
def delete_fire_extinguisher_image_file(sender, instance, **kwargs):
    """Remove fire extinguisher image file from storage after record deletion."""
    _delete_file_safely(instance.image)


@receiver(post_delete, sender=Equipment)
def delete_equipment_main_image(sender, instance, **kwargs):
    """Remove main equipment image file and related files from storage after equipment deletion."""
    _delete_file_safely(instance.equipment_image)