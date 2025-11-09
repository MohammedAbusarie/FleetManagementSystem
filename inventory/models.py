from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from .constants import CAR_STATUS_CHOICES, CAR_OWNERSHIP_CHOICES, EQUIPMENT_STATUS_CHOICES
from .managers import (
    CarManager, EquipmentManager, UserProfileManager, ModulePermissionManager,
    UserPermissionManager, LoginLogManager, ActionLogManager
)


# Base model for DDL tables
class BaseDDLModel(models.Model):
    """Base model for all dropdown list tables"""
    name = models.CharField(max_length=255, unique=True, verbose_name="الاسم")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


# DDL Tables
class AdministrativeUnit(BaseDDLModel):
    """Administrative Unit lookup table - الإدارة"""
    is_dummy = models.BooleanField(default=False, verbose_name="قيمة افتراضية")
    sector = models.ForeignKey(
        'Sector', on_delete=models.PROTECT, related_name='administrative_units',
        verbose_name="القطاع", null=True, blank=True
    )
    
    class Meta:
        verbose_name = "إدارة"
        verbose_name_plural = "الإدارات"

    @property
    def is_protected_default(self):
        """Check if this is the protected default 'غير محدد' record"""
        return self.is_dummy and self.name == 'غير محدد'

    def save(self, *args, **kwargs):
        """Prevent editing the protected default record"""
        if self.pk:
            try:
                old_instance = AdministrativeUnit.objects.get(pk=self.pk)
                if old_instance.is_protected_default:
                    if (
                        self.name != old_instance.name or
                        self.is_dummy != old_instance.is_dummy or
                        self.sector_id != old_instance.sector_id
                    ):
                        raise ValueError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
            except AdministrativeUnit.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the protected default record"""
        if self.is_protected_default:
            raise ValueError('لا يمكن حذف السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        super().delete(*args, **kwargs)


class Department(BaseDDLModel):
    """Department lookup table"""
    division = models.ForeignKey(
        'Division',
        on_delete=models.PROTECT,
        related_name='departments',
        verbose_name="الدائرة",
        null=True,
        blank=True
    )
    is_dummy = models.BooleanField(default=False, verbose_name="قيمة افتراضية")
    
    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"
    
    @property
    def is_protected_default(self):
        """Check if this is the protected default 'غير محدد' record"""
        return self.is_dummy and self.name == 'غير محدد'
    
    def save(self, *args, **kwargs):
        """Prevent editing the protected default record"""
        if self.pk:  # Only check on update, not creation
            try:
                old_instance = Department.objects.get(pk=self.pk)
                if old_instance.is_protected_default:
                    # Prevent name, is_dummy, and division changes
                    if (
                        self.name != old_instance.name
                        or self.is_dummy != old_instance.is_dummy
                        or self.division_id != old_instance.division_id
                    ):
                        raise ValueError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
            except Department.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the protected default record"""
        if self.is_protected_default:
            raise ValueError('لا يمكن حذف السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        super().delete(*args, **kwargs)

    @property
    def administrative_unit(self):
        """Return the administrative unit this department belongs to"""
        return self.division.administrative_unit if self.division else None

    @property
    def sector(self):
        """Return the sector this department belongs to"""
        admin_unit = self.administrative_unit
        return admin_unit.sector if admin_unit else None


class Driver(BaseDDLModel):
    """Driver lookup table"""
    license_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الرخصة")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")

    class Meta:
        verbose_name = "سائق"
        verbose_name_plural = "السائقين"


class CarClass(BaseDDLModel):
    """Car class lookup table"""
    class Meta:
        verbose_name = "فئة السيارة"
        verbose_name_plural = "فئات السيارات"


class Manufacturer(BaseDDLModel):
    """Manufacturer lookup table for both cars and equipment"""
    class Meta:
        verbose_name = "الشركة المصنعة"
        verbose_name_plural = "الشركات المصنعة"


class CarModel(BaseDDLModel):
    """Car model lookup table"""
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, related_name='car_models',
        verbose_name="الشركة المصنعة"
    )
    year = models.IntegerField(blank=True, null=True, verbose_name="السنة")

    class Meta:
        verbose_name = "موديل السيارة"
        verbose_name_plural = "موديلات السيارات"


class EquipmentModel(BaseDDLModel):
    """Equipment model lookup table"""
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, related_name='equipment_models',
        verbose_name="الشركة المصنعة"
    )

    class Meta:
        verbose_name = "موديل المعدة"
        verbose_name_plural = "موديلات المعدات"


class FunctionalLocation(BaseDDLModel):
    """Functional location lookup table"""
    class Meta:
        verbose_name = "الموقع الوظيفي"
        verbose_name_plural = "المواقع الوظيفية"


class Room(BaseDDLModel):
    """Room lookup table"""
    building = models.CharField(max_length=255, blank=True, null=True, verbose_name="المبنى")
    floor = models.CharField(max_length=50, blank=True, null=True, verbose_name="الطابق")

    class Meta:
        verbose_name = "غرفة"
        verbose_name_plural = "الغرف"


class Location(BaseDDLModel):
    """Location lookup table for equipment"""
    class Meta:
        verbose_name = "موقع"
        verbose_name_plural = "المواقع"


class Sector(BaseDDLModel):
    """Sector lookup table"""
    is_dummy = models.BooleanField(default=False, verbose_name="قيمة افتراضية")
    
    class Meta:
        verbose_name = "قطاع"
        verbose_name_plural = "القطاعات"
    
    @property
    def is_protected_default(self):
        """Check if this is the protected default 'غير محدد' record"""
        return self.is_dummy and self.name == 'غير محدد'
    
    def save(self, *args, **kwargs):
        """Prevent editing the protected default record"""
        if self.pk:  # Only check on update, not creation
            try:
                old_instance = Sector.objects.get(pk=self.pk)
                if old_instance.is_protected_default:
                    # Prevent name, is_dummy changes
                    if self.name != old_instance.name or self.is_dummy != old_instance.is_dummy:
                        raise ValueError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
            except Sector.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the protected default record"""
        if self.is_protected_default:
            raise ValueError('لا يمكن حذف السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        super().delete(*args, **kwargs)


class NotificationRecipient(BaseDDLModel):
    """Notification recipient lookup table"""
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")

    class Meta:
        verbose_name = "مستلم الإشعار"
        verbose_name_plural = "مستلمي الإشعارات"


class ContractType(BaseDDLModel):
    """Contract type lookup table (e.g., Agency, Management Purchase)"""
    class Meta:
        verbose_name = "نوع العقد"
        verbose_name_plural = "أنواع العقود"


class Activity(BaseDDLModel):
    """Activity lookup table"""
    class Meta:
        verbose_name = "نشاط"
        verbose_name_plural = "الأنشطة"


class Region(BaseDDLModel):
    """Region lookup table for visited regions"""
    class Meta:
        verbose_name = "منطقة"
        verbose_name_plural = "المناطق"


class Division(BaseDDLModel):
    """Division lookup table - دائرة"""
    administrative_unit = models.ForeignKey(
        'AdministrativeUnit', on_delete=models.PROTECT, related_name='divisions',
        verbose_name="الإدارة", null=True, blank=True
    )
    is_dummy = models.BooleanField(default=False, verbose_name="قيمة افتراضية")
    
    class Meta:
        verbose_name = "دائرة"
        verbose_name_plural = "الدوائر"
    
    @property
    def is_protected_default(self):
        """Check if this is the protected default 'غير محدد' record"""
        return self.is_dummy and self.name == 'غير محدد'
    
    def save(self, *args, **kwargs):
        """Prevent editing the protected default record"""
        if self.pk:  # Only check on update, not creation
            try:
                old_instance = Division.objects.get(pk=self.pk)
                if old_instance.is_protected_default:
                    # Prevent name, is_dummy, and department changes
                    if (self.name != old_instance.name or 
                        self.is_dummy != old_instance.is_dummy or
                        self.administrative_unit_id != old_instance.administrative_unit_id):
                        raise ValueError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
            except Division.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the protected default record"""
        if self.is_protected_default:
            raise ValueError('لا يمكن حذف السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        super().delete(*args, **kwargs)


# Main Models
class Car(models.Model):
    """Car/Fleet model - جدول سيارات المدينة"""

    STATUS_CHOICES = CAR_STATUS_CHOICES
    OWNERSHIP_CHOICES = CAR_OWNERSHIP_CHOICES

    # Basic Information
    fleet_no = models.CharField(max_length=100, unique=True, verbose_name="رقم الأسطول")
    plate_no_en = models.CharField(max_length=100, unique=True, verbose_name="رقم اللوحة (الإنجليزية)")
    plate_no_ar = models.CharField(max_length=100, unique=True, verbose_name="رقم اللوحة (العربية)")

    # Foreign Keys to DDL tables
    administrative_unit = models.ForeignKey(
        AdministrativeUnit, on_delete=models.PROTECT, related_name='cars',
        verbose_name="الإدارة", null=True, blank=True
    )
    department_code = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='cars',
        verbose_name="رمز القسم", null=True, blank=True
    )
    driver_name = models.ForeignKey(
        Driver, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cars', verbose_name="اسم السائق"
    )
    car_class = models.ForeignKey(
        CarClass, on_delete=models.PROTECT, related_name='cars',
        verbose_name="فئة السيارة", null=True, blank=True
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, related_name='cars',
        verbose_name="الشركة المصنعة", null=True, blank=True
    )
    model = models.ForeignKey(
        CarModel, on_delete=models.PROTECT, related_name='cars',
        verbose_name="الموديل", null=True, blank=True
    )
    functional_location = models.ForeignKey(
        FunctionalLocation, on_delete=models.PROTECT, related_name='cars',
        verbose_name="الموقع الوظيفي", null=True, blank=True
    )
    room = models.ForeignKey(
        Room, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cars', verbose_name="الغرفة"
    )
    notification_recipient = models.ForeignKey(
        NotificationRecipient, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cars', verbose_name="مستلم الإشعار"
    )
    contract_type = models.ForeignKey(
        ContractType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cars', verbose_name="نوع العقد"
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cars', verbose_name="النشاط"
    )
    
    # Organizational Hierarchy
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name='cars_by_sector',
        verbose_name="القطاع", null=True, blank=True
    )
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='cars_by_department',
        verbose_name="القسم", null=True, blank=True
    )
    division = models.ForeignKey(
        'Division', on_delete=models.PROTECT, related_name='cars',
        verbose_name="الدائرة", null=True, blank=True
    )

    # Ownership
    ownership_type = models.CharField(
        max_length=50, choices=OWNERSHIP_CHOICES, default='owned',
        verbose_name="نوع الملكية"
    )

    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new', verbose_name="الحالة")

    # Location Details
    location_description = models.TextField(verbose_name="وصف الموقع")
    address_details_1 = models.TextField(blank=True, null=True, verbose_name="تفاصيل العنوان 1")

    # Dates - Removed old fields, now handled by historical records

    # Image
    car_image = models.ImageField(upload_to='cars/', blank=True, null=True, verbose_name="صورة السيارة")

    # Many-to-Many Relationships
    visited_regions = models.ManyToManyField(Region, blank=True, related_name='cars', verbose_name="المناطق المزارة")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add custom manager
    objects = CarManager()

    class Meta:
        verbose_name = "سيارة"
        verbose_name_plural = "السيارات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.fleet_no} - {self.plate_no_en}"

    @property
    def current_license_record(self):
        """Get the current license record"""
        return self.license_records.first()

    @property
    def current_inspection_record(self):
        """Get the current inspection record"""
        return self.inspection_records.first()

    @property
    def is_inspection_expired(self):
        """Check if inspection is expired"""
        current_record = self.current_inspection_record
        if not current_record or not current_record.end_date:
            return True
        return current_record.end_date < date.today()

    @property
    def days_until_inspection_expiry(self):
        """Days until inspection expires"""
        current_record = self.current_inspection_record
        if not current_record or not current_record.end_date:
            return None
        delta = current_record.end_date - date.today()
        return delta.days


class Equipment(models.Model):
    """Equipment model - جدول المعدات"""

    STATUS_CHOICES = EQUIPMENT_STATUS_CHOICES

    # Basic Information
    door_no = models.CharField(max_length=100, unique=True, verbose_name="رقم الباب")
    plate_no = models.CharField(max_length=100, unique=True, verbose_name="رقم اللوحة")
    manufacture_year = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2030)],
        verbose_name="سنة التصنيع"
    )

    # Foreign Keys to DDL tables
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, related_name='equipment',
        verbose_name="الشركة المصنعة", null=True, blank=True
    )
    model = models.ForeignKey(
        EquipmentModel, on_delete=models.PROTECT, related_name='equipment',
        verbose_name="الموديل", null=True, blank=True
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='equipment',
        verbose_name="الموقع", null=True, blank=True
    )
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name='equipment',
        verbose_name="القطاع", null=True, blank=True
    )
    
    # Organizational Hierarchy
    administrative_unit = models.ForeignKey(
        AdministrativeUnit, on_delete=models.PROTECT, related_name='equipment_by_unit',
        verbose_name="الإدارة", null=True, blank=True
    )
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='equipment',
        verbose_name="القسم", null=True, blank=True
    )
    division = models.ForeignKey(
        'Division', on_delete=models.PROTECT, related_name='equipment',
        verbose_name="الدائرة", null=True, blank=True
    )

    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new', verbose_name="الحالة")

    # Dates - Removed old fields, now handled by historical records

    # Image
    equipment_image = models.ImageField(upload_to='equipment/', blank=True, null=True, verbose_name="صورة المعدة")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add custom manager
    objects = EquipmentManager()

    class Meta:
        verbose_name = "معدة"
        verbose_name_plural = "المعدات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.door_no} - {self.plate_no}"

    @property
    def primary_image(self):
        """Return the main image for the equipment, falling back to gallery images."""
        if self.equipment_image:
            return self.equipment_image

        prefetched_images = getattr(self, "_prefetched_objects_cache", {}).get("equipment_images")
        if prefetched_images:
            first_image = next((img for img in prefetched_images if getattr(img, "image", None)), None)
        else:
            first_image = self.equipment_images.order_by("-uploaded_at").first()

        return first_image.image if first_image else None

    @property
    def current_license_record(self):
        """Get the current license record"""
        return self.license_records.first()

    @property
    def current_inspection_record(self):
        """Get the current inspection record"""
        return self.inspection_records.first()

    @property
    def is_inspection_expired(self):
        """Check if inspection is expired"""
        current_record = self.current_inspection_record
        if not current_record or not current_record.end_date:
            return True
        return current_record.end_date < date.today()

    @property
    def days_until_inspection_expiry(self):
        """Days until inspection expires"""
        current_record = self.current_inspection_record
        if not current_record or not current_record.end_date:
            return None
        delta = current_record.end_date - date.today()
        return delta.days

    @property
    def current_fire_extinguisher_record(self):
        """Get the current fire extinguisher record"""
        return self.fire_extinguisher_records.first()

    @property
    def is_fire_extinguisher_expired(self):
        """Check if fire extinguisher is expired"""
        current_record = self.current_fire_extinguisher_record
        if not current_record or not current_record.expiry_date:
            return True
        return current_record.expiry_date < date.today()

    @property
    def days_until_fire_extinguisher_expiry(self):
        """Days until fire extinguisher expires"""
        current_record = self.current_fire_extinguisher_record
        if not current_record or not current_record.expiry_date:
            return None
        delta = current_record.expiry_date - date.today()
        return delta.days


class CalibrationCertificateImage(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='calibration_certificates',
        verbose_name="المعدة"
    )
    image = models.FileField(
        upload_to='calibration_certificates/', verbose_name="شهادة المعايرة"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name="تاريخ الرفع"
    )

    class Meta:
        verbose_name = "شهادة معايرة"
        verbose_name_plural = "شهادات المعايرة"

    def __str__(self):
        return f"Certificate for {self.equipment.door_no}"

    @property
    def is_image(self):
        """Check if the uploaded file is an image"""
        if not self.image:
            return False
        file_extension = self.image.name.lower().split('.')[-1] if '.' in self.image.name else ''
        return file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

    @property
    def is_pdf(self):
        """Check if the uploaded file is a PDF"""
        if not self.image:
            return False
        file_extension = self.image.name.lower().split('.')[-1] if '.' in self.image.name else ''
        return file_extension == 'pdf'

    @property
    def file_type(self):
        """Return the file type for display purposes"""
        if self.is_image:
            return 'image'
        elif self.is_pdf:
            return 'pdf'
        else:
            return 'unknown'


class CarImage(models.Model):
    """Model to store multiple car images"""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='car_images', verbose_name="السيارة")
    image = models.ImageField(upload_to='cars/', verbose_name="صورة السيارة")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "صورة سيارة"
        verbose_name_plural = "صور السيارات"

    def __str__(self):
        return f"Image for {self.car.fleet_no}"


class EquipmentImage(models.Model):
    """Model to store multiple equipment images"""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='equipment_images',
        verbose_name="المعدة"
    )
    image = models.ImageField(upload_to='equipment/', verbose_name="صورة المعدة")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "صورة معدة"
        verbose_name_plural = "صور المعدات"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Image for {self.equipment.door_no}"


class CarLicenseRecord(models.Model):
    """Car License Record model - سجل رخصة السيارة"""

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='license_records', verbose_name="السيارة")
    start_date = models.DateField(verbose_name="تاريخ بداية الرخصة")
    end_date = models.DateField(verbose_name="تاريخ انتهاء الرخصة")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "سجل رخصة سيارة"
        verbose_name_plural = "سجلات رخص السيارات"
        ordering = ['-start_date']

    def __str__(self):
        return f"License for {self.car.fleet_no} ({self.start_date} - {self.end_date})"


class CarInspectionRecord(models.Model):
    """Car Inspection Record model - سجل فحص السيارة السنوي"""

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='inspection_records', verbose_name="السيارة")
    start_date = models.DateField(verbose_name="تاريخ بداية الفحص")
    end_date = models.DateField(verbose_name="تاريخ انتهاء الفحص")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "سجل فحص سيارة"
        verbose_name_plural = "سجلات فحص السيارات"
        ordering = ['-start_date']

    def __str__(self):
        return f"Inspection for {self.car.fleet_no} ({self.start_date} - {self.end_date})"


class EquipmentLicenseRecord(models.Model):
    """Equipment License Record model - سجل رخصة المعدة"""

    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='license_records',
        verbose_name="المعدة"
    )
    start_date = models.DateField(verbose_name="تاريخ بداية رخصة المعدة")
    end_date = models.DateField(verbose_name="تاريخ انتهاء رخصة المعدة")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "سجل رخصة معدة"
        verbose_name_plural = "سجلات رخص المعدات"
        ordering = ['-start_date']

    def __str__(self):
        return f"License for {self.equipment.door_no} ({self.start_date} - {self.end_date})"


class EquipmentInspectionRecord(models.Model):
    """Equipment Inspection Record model - سجل فحص المعدة السنوي"""

    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='inspection_records',
        verbose_name="المعدة"
    )
    start_date = models.DateField(verbose_name="تاريخ بداية الفحص السنوي")
    end_date = models.DateField(verbose_name="تاريخ انتهاء الفحص السنوي")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "سجل فحص معدة"
        verbose_name_plural = "سجلات فحص المعدات"
        ordering = ['-start_date']

    def __str__(self):
        return f"Inspection for {self.equipment.door_no} ({self.start_date} - {self.end_date})"


class FireExtinguisherInspectionRecord(models.Model):
    """Fire Extinguisher Inspection Record model - سجل فحص طفاية الحريق"""

    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='fire_extinguisher_records',
        verbose_name="المعدة"
    )
    inspection_date = models.DateField(verbose_name="تاريخ الفحص الدوري لطفاية الحريق")
    expiry_date = models.DateField(verbose_name="تاريخ انتهاء طفاية الحريق")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "سجل فحص طفاية حريق"
        verbose_name_plural = "سجلات فحص طفايات الحريق"
        ordering = ['-inspection_date']

    def __str__(self):
        return (f"Fire Extinguisher Inspection for {self.equipment.door_no} "
                f"({self.inspection_date} - {self.expiry_date})")


class FireExtinguisherImage(models.Model):
    """Model to store multiple fire extinguisher images"""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name='fire_extinguisher_images',
        verbose_name="المعدة"
    )
    image = models.ImageField(upload_to='fire_extinguishers/', verbose_name="صورة طفاية الحريق")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "صورة طفاية حريق"
        verbose_name_plural = "صور طفايات الحريق"

    def __str__(self):
        return f"Fire Extinguisher Image for {self.equipment.door_no}"


# =============================================================================
# RBAC SYSTEM MODELS - Phase 1 Implementation
# =============================================================================

class UserProfile(models.Model):
    """Extended user profile for RBAC system"""

    USER_TYPE_CHOICES = [
        ('super_admin', 'مدير عام'),
        ('admin', 'مدير'),
        ('normal', 'مستخدم عادي'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="المستخدم")
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='normal',
        verbose_name="نوع المستخدم"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name="أنشأ بواسطة"
    )
    permissions_json = models.JSONField(default=dict, blank=True, verbose_name="الصلاحيات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # Custom manager
    objects = UserProfileManager()

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

    def get_user_type(self):
        """Get user type with fallback to current system"""
        if self.user_type:
            return self.user_type
        # Fallback to current system: check if user is in Admin group or is superuser
        if self.user.groups.filter(name='Admin').exists() or self.user.is_superuser:
            return 'admin'
        return 'normal'

    def is_super_admin(self):
        """Check if user is super admin"""
        return self.get_user_type() == 'super_admin' or self.user.is_superuser

    def is_admin_user(self):
        """Check if user is admin (including super admin)"""
        user_type = self.get_user_type()
        return user_type in ['super_admin', 'admin']


class ModulePermission(models.Model):
    """Module permissions for CRUD operations"""

    MODULE_CHOICES = [
        ('cars', 'السيارات'),
        ('equipment', 'المعدات'),
        ('generic_tables', 'الجداول العامة'),
    ]

    PERMISSION_CHOICES = [
        ('create', 'إنشاء'),
        ('read', 'قراءة'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
    ]

    module_name = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        verbose_name="اسم الوحدة"
    )
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        verbose_name="نوع الصلاحية"
    )
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    # Custom manager
    objects = ModulePermissionManager()

    class Meta:
        verbose_name = "صلاحية الوحدة"
        verbose_name_plural = "صلاحيات الوحدات"
        unique_together = ['module_name', 'permission_type']
        ordering = ['module_name', 'permission_type']

    def __str__(self):
        return f"{self.get_module_name_display()} - {self.get_permission_type_display()}"


class UserPermission(models.Model):
    """User-specific module permissions"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='custom_user_permissions',
        verbose_name="المستخدم"
    )
    module_permission = models.ForeignKey(ModulePermission, on_delete=models.CASCADE, verbose_name="صلاحية الوحدة")
    granted = models.BooleanField(default=False, verbose_name="ممنوح")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # Custom manager
    objects = UserPermissionManager()

    class Meta:
        verbose_name = "صلاحية المستخدم"
        verbose_name_plural = "صلاحيات المستخدمين"
        unique_together = ['user', 'module_permission']
        ordering = ['user', 'module_permission']

    def __str__(self):
        status = "ممنوح" if self.granted else "غير ممنوح"
        return f"{self.user.username} - {self.module_permission} ({status})"


class LoginLog(models.Model):
    """Login history tracking"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs', verbose_name="المستخدم")
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="وقت تسجيل الدخول")
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    user_agent = models.TextField(verbose_name="متصفح المستخدم")
    success = models.BooleanField(default=True, verbose_name="نجح")
    logout_time = models.DateTimeField(null=True, blank=True, verbose_name="وقت تسجيل الخروج")

    # Custom manager
    objects = LoginLogManager()

    class Meta:
        verbose_name = "سجل تسجيل الدخول"
        verbose_name_plural = "سجلات تسجيل الدخول"
        ordering = ['-login_time']

    def __str__(self):
        status = "نجح" if self.success else "فشل"
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')} ({status})"


class ActionLog(models.Model):
    """System action logging"""

    ACTION_CHOICES = [
        ('create', 'إنشاء'),
        ('read', 'قراءة'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('permission_change', 'تغيير صلاحية'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='action_logs', verbose_name="المستخدم")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="نوع العملية")
    module_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="اسم الوحدة")
    object_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="معرف الكائن")
    description = models.TextField(verbose_name="الوصف")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")

    # Custom manager
    objects = ActionLogManager()

    class Meta:
        verbose_name = "سجل العملية"
        verbose_name_plural = "سجلات العمليات"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Maintenance(models.Model):
    """Maintenance model - جدول الصيانة (linked to both Car and Equipment)"""

    # Generic Foreign Key to link to either Car or Equipment
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="نوع المحتوى")
    object_id = models.PositiveIntegerField(verbose_name="معرف الكائن")
    content_object = GenericForeignKey('content_type', 'object_id')

    # Maintenance Details
    maintenance_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الصيانة")
    restoration_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الإصلاح")
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="التكلفة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "صيانة"
        verbose_name_plural = "سجلات الصيانة"
        ordering = ['-maintenance_date']

    def __str__(self):
        return f"Maintenance on {self.maintenance_date} for {self.content_object}"
