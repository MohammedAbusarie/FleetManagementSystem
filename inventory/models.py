from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, date
from .constants import CAR_STATUS_CHOICES, CAR_OWNERSHIP_CHOICES, EQUIPMENT_STATUS_CHOICES
from .managers import CarManager, EquipmentManager


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
    class Meta:
        verbose_name = "إدارة"
        verbose_name_plural = "الإدارات"


class Department(BaseDDLModel):
    """Department lookup table"""
    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"


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
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='car_models', verbose_name="الشركة المصنعة")
    year = models.IntegerField(blank=True, null=True, verbose_name="السنة")
    
    class Meta:
        verbose_name = "موديل السيارة"
        verbose_name_plural = "موديلات السيارات"


class EquipmentModel(BaseDDLModel):
    """Equipment model lookup table"""
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='equipment_models', verbose_name="الشركة المصنعة")
    
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
    class Meta:
        verbose_name = "قطاع"
        verbose_name_plural = "القطاعات"


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
    administrative_unit = models.ForeignKey(AdministrativeUnit, on_delete=models.PROTECT, related_name='cars', verbose_name="الإدارة", null=True, blank=True)
    department_code = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='cars', verbose_name="رمز القسم", null=True, blank=True)
    driver_name = models.ForeignKey(Driver, on_delete=models.PROTECT, null=True, blank=True, related_name='cars', verbose_name="اسم السائق")
    car_class = models.ForeignKey(CarClass, on_delete=models.PROTECT, related_name='cars', verbose_name="فئة السيارة", null=True, blank=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='cars', verbose_name="الشركة المصنعة", null=True, blank=True)
    model = models.ForeignKey(CarModel, on_delete=models.PROTECT, related_name='cars', verbose_name="الموديل", null=True, blank=True)
    functional_location = models.ForeignKey(FunctionalLocation, on_delete=models.PROTECT, related_name='cars', verbose_name="الموقع الوظيفي", null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True, blank=True, related_name='cars', verbose_name="الغرفة")
    notification_recipient = models.ForeignKey(NotificationRecipient, on_delete=models.PROTECT, null=True, blank=True, related_name='cars', verbose_name="مستلم الإشعار")
    contract_type = models.ForeignKey(ContractType, on_delete=models.PROTECT, null=True, blank=True, related_name='cars', verbose_name="نوع العقد")
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, null=True, blank=True, related_name='cars', verbose_name="النشاط")
    
    # Ownership
    ownership_type = models.CharField(max_length=50, choices=OWNERSHIP_CHOICES, default='owned', verbose_name="نوع الملكية")
    
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
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='equipment', verbose_name="الشركة المصنعة", null=True, blank=True)
    model = models.ForeignKey(EquipmentModel, on_delete=models.PROTECT, related_name='equipment', verbose_name="الموديل", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='equipment', verbose_name="الموقع", null=True, blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='equipment', verbose_name="القطاع", null=True, blank=True)
    
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


class CalibrationCertificateImage(models.Model):
    """Model to store multiple calibration certificate files (images and PDFs) for equipment"""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='calibration_certificates', verbose_name="المعدة")
    image = models.FileField(upload_to='calibration_certificates/', verbose_name="شهادة المعايرة")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    
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
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='equipment_images', verbose_name="المعدة")
    image = models.ImageField(upload_to='equipment/', verbose_name="صورة المعدة")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    
    class Meta:
        verbose_name = "صورة معدة"
        verbose_name_plural = "صور المعدات"
    
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
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='license_records', verbose_name="المعدة")
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
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='inspection_records', verbose_name="المعدة")
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

