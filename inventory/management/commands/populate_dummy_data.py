import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import (
    Activity,
    AdministrativeUnit,
    CalibrationCertificateImage,
    Car,
    CarClass,
    CarImage,
    CarInspectionRecord,
    CarLicenseRecord,
    CarModel,
    ContractType,
    Department,
    Division,
    Driver,
    Equipment,
    EquipmentImage,
    EquipmentInspectionRecord,
    EquipmentLicenseRecord,
    EquipmentModel,
    FireExtinguisherImage,
    FireExtinguisherInspectionRecord,
    FunctionalLocation,
    Location,
    Maintenance,
    Manufacturer,
    NotificationRecipient,
    Region,
    Room,
    Sector,
)


class Command(BaseCommand):
    """Management command to clear and repopulate the database with realistic Arabic dummy data."""

    help = 'Clear database and populate with fresh dummy data aligned with the latest models'

    CAR_TARGET_COUNT = 24
    EQUIPMENT_TARGET_COUNT = 16
    RANDOM_SEED = 42

    def __init__(self):
        super().__init__()
        base_dir = Path(settings.BASE_DIR)
        self.dummy_media_dir = base_dir / 'dummy_media'
        self.car_images_dir = self.dummy_media_dir / 'cars'
        self.equipment_images_dir = self.dummy_media_dir / 'equipments'
        self.certificates_dir = self.dummy_media_dir / 'certificates'
        self.car_excel_path = self.dummy_media_dir / 'سيارات المدينة.xlsx'
        self.equipment_excel_path = self.dummy_media_dir / 'نسخة من جدول المعدات.xlsx'

        self.cars_df = None
        self.equipment_df = None

        random.seed(self.RANDOM_SEED)

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-only',
            action='store_true',
            help='Only clear the database without repopulating records',
        )

    def handle(self, *args, **options):
        if options['clear_only']:
            self.clear_database()
            return

        self.stdout.write(self.style.WARNING('بدء تهيئة بيانات الاختبار...'))
        self._load_excel_data()

        with transaction.atomic():
            self.clear_database()
            context = self.create_lookup_tables()
            cars = self.populate_cars(context)
            equipment = self.populate_equipment(context)
            self.create_maintenance_records(cars, equipment)

        self.stdout.write(self.style.SUCCESS('تم إنشاء بيانات الاختبار بنجاح!'))

    # ---------------------------------------------------------------------
    # Data preparation helpers
    # ---------------------------------------------------------------------

    def _load_excel_data(self):
        """Read Excel files if they are available."""
        self.cars_df = self._read_excel(self.car_excel_path, limit=self.CAR_TARGET_COUNT * 2)
        self.equipment_df = self._read_excel(self.equipment_excel_path, limit=self.EQUIPMENT_TARGET_COUNT * 2)

    def _read_excel(self, path: Path, limit: int | None = None):
        """Safely read an Excel file and return a DataFrame (or None)."""
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'لم يتم العثور على الملف {path.name}، سيتم إنشاء بيانات افتراضية.'))
            return None

        try:
            df = pd.read_excel(path)
            if limit:
                df = df.head(limit)
            return df
        except Exception as exc:  # pylint: disable=broad-except
            self.stdout.write(self.style.ERROR(f'تعذّر قراءة الملف {path.name}: {exc}'))
            return None

    # ---------------------------------------------------------------------
    # Database management
    # ---------------------------------------------------------------------

    def clear_database(self):
        """Clear all data from inventory-related tables in a safe order."""
        self.stdout.write(self.style.WARNING('جاري تفريغ قاعدة البيانات...'))

        Maintenance.objects.all().delete()
        CalibrationCertificateImage.objects.all().delete()
        FireExtinguisherImage.objects.all().delete()
        EquipmentImage.objects.all().delete()
        CarImage.objects.all().delete()
        FireExtinguisherInspectionRecord.objects.all().delete()
        EquipmentInspectionRecord.objects.all().delete()
        EquipmentLicenseRecord.objects.all().delete()
        CarInspectionRecord.objects.all().delete()
        CarLicenseRecord.objects.all().delete()

        Equipment.objects.all().delete()
        Car.objects.all().delete()

        Activity.objects.all().delete()
        ContractType.objects.all().delete()
        NotificationRecipient.objects.all().delete()
        Region.objects.all().delete()
        Room.objects.all().delete()
        FunctionalLocation.objects.all().delete()
        Location.objects.all().delete()

        Department.objects.all().delete()
        Division.objects.all().delete()
        AdministrativeUnit.objects.all().delete()
        Sector.objects.all().delete()

        EquipmentModel.objects.all().delete()
        CarModel.objects.all().delete()
        Manufacturer.objects.all().delete()
        CarClass.objects.all().delete()
        Driver.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('تم تفريغ قاعدة البيانات بنجاح.'))

    # ---------------------------------------------------------------------
    # Lookup tables
    # ---------------------------------------------------------------------

    def create_lookup_tables(self):
        """Create lookup tables and return context objects for later use."""
        self.stdout.write(self.style.WARNING('إنشاء الجداول المرجعية...'))

        context: dict[str, list] = {}

        dummy_context = self._ensure_dummy_hierarchy()

        sectors_structure = [
            {
                'name': 'قطاع الخدمات',
                'units': [
                    {
                        'name': 'إدارة النقل',
                        'divisions': [
                            {'name': 'دائرة الأسطول', 'departments': ['قسم العمليات', 'قسم الجداول']},
                            {'name': 'دائرة اللوجستيات', 'departments': ['قسم الدعم الميداني']},
                        ],
                    },
                    {
                        'name': 'إدارة الصيانة',
                        'divisions': [
                            {'name': 'دائرة صيانة المركبات', 'departments': ['قسم الصيانة السريعة', 'قسم الصيانة الثقيلة']},
                        ],
                    },
                ],
            },
            {
                'name': 'قطاع التقنية والابتكار',
                'units': [
                    {
                        'name': 'إدارة تقنية المعلومات',
                        'divisions': [
                            {'name': 'دائرة الدعم الفني', 'departments': ['قسم أنظمة المركبات']},
                            {'name': 'دائرة تطوير الأنظمة', 'departments': ['قسم التطوير الميداني']},
                        ],
                    },
                ],
            },
            {
                'name': 'قطاع المالية',
                'units': [
                    {
                        'name': 'إدارة الميزانية',
                        'divisions': [
                            {'name': 'دائرة التخطيط المالي', 'departments': ['قسم العقود', 'قسم المتابعة المالية']},
                        ],
                    },
                ],
            },
        ]

        sectors = []
        administrative_units = []
        divisions = []
        departments = []

        for sector_data in sectors_structure:
            sector, _ = Sector.objects.get_or_create(name=sector_data['name'], defaults={'is_dummy': False})
            sectors.append(sector)

            for unit_data in sector_data['units']:
                admin_unit, created = AdministrativeUnit.objects.get_or_create(
                    name=unit_data['name'],
                    defaults={'sector': sector, 'is_dummy': False},
                )
                if not created and admin_unit.sector != sector:
                    admin_unit.sector = sector
                    admin_unit.is_dummy = False
                    admin_unit.save(update_fields=['sector', 'is_dummy'])
                administrative_units.append(admin_unit)

                for division_data in unit_data['divisions']:
                    division, created = Division.objects.get_or_create(
                        name=division_data['name'],
                        defaults={'administrative_unit': admin_unit, 'is_dummy': False},
                    )
                    if not created and division.administrative_unit != admin_unit:
                        division.administrative_unit = admin_unit
                        division.is_dummy = False
                        division.save(update_fields=['administrative_unit', 'is_dummy'])
                    divisions.append(division)

                    for department_name in division_data['departments']:
                        department, created = Department.objects.get_or_create(
                            name=department_name,
                            defaults={'division': division, 'is_dummy': False},
                        )
                        if not created:
                            needs_update = False
                            if department.division != division:
                                department.division = division
                                needs_update = True
                            if department.is_dummy:
                                department.is_dummy = False
                                needs_update = True
                            if needs_update:
                                department.save(update_fields=['division', 'is_dummy'])
                        departments.append(department)

        context['sectors'] = sectors
        context['administrative_units'] = administrative_units
        context['divisions'] = divisions
        context['departments'] = departments
        context['dummy'] = dummy_context

        # Car classes
        car_class_names = {'سيدان', 'دفع رباعي', 'حافلة صغيرة', 'شاحنة خفيفة'}
        car_class_names |= self._extract_unique_values(self.cars_df, ['Class', 'الفئة'])
        for name in car_class_names:
            CarClass.objects.get_or_create(name=name)
        context['car_classes'] = list(CarClass.objects.all())

        # Drivers
        driver_names = [
            'أحمد محمد', 'خالد عبدالله', 'محمد علي', 'عبدالرحمن حسن', 'سعد إبراهيم',
            'فهد سالم', 'عمر ناصر', 'يوسف أحمد', 'سلمان سعيد', 'تركي فهد',
        ]
        drivers = []
        for name in driver_names:
            driver, _ = Driver.objects.get_or_create(
                name=name,
                defaults={'license_number': f'LIC{random.randint(1000, 9999)}', 'phone': f'+966{random.randint(500000000, 599999999)}'},
            )
            drivers.append(driver)
        context['drivers'] = drivers

        # Manufacturers
        manufacturer_names = {
            'تويوتا', 'نيسان', 'هيونداي', 'مرسيدس', 'شيفروليه', 'كاتربيلر', 'كوماتسو', 'بوش'
        }
        manufacturer_names |= self._extract_unique_values(self.cars_df, ['Manufacturer', 'الشركة المصنعة'])
        manufacturer_names |= self._extract_unique_values(self.equipment_df, ['المصـــنع', 'الشركة المصنعة'])
        manufacturer_lookup = {}
        for name in manufacturer_names:
            manufacturer, _ = Manufacturer.objects.get_or_create(name=name)
            manufacturer_lookup[name] = manufacturer
        context['manufacturers'] = manufacturer_lookup

        # Car models
        car_model_seeds = [
            ('تويوتا', 'كامري', 2022),
            ('تويوتا', 'هايلكس', 2021),
            ('نيسان', 'باترول', 2020),
            ('هيونداي', 'سوناتا', 2023),
            ('شيفروليه', 'تاهو', 2022),
        ]
        for manufacturer_name, model_name, year in car_model_seeds:
            manufacturer = manufacturer_lookup.get(manufacturer_name)
            if manufacturer:
                self._get_or_update_car_model(model_name, manufacturer, year)
        if self.cars_df is not None:
            for _, row in self.cars_df.iterrows():
                manufacturer_name = self._clean_string(row.get('Manufacturer')) or self._clean_string(row.get('الشركة المصنعة'))
                model_name = self._clean_string(row.get('Model No')) or self._clean_string(row.get('الموديل'))
                if manufacturer_name and model_name:
                    manufacturer = manufacturer_lookup.get(manufacturer_name)
                    if not manufacturer:
                        manufacturer, _ = Manufacturer.objects.get_or_create(name=manufacturer_name)
                        manufacturer_lookup[manufacturer_name] = manufacturer
                    year = self._safe_int(row.get('Model Year'), random.randint(2017, 2024))
                    self._get_or_update_car_model(model_name, manufacturer, year)
        context['car_models'] = list(CarModel.objects.all())

        # Equipment models
        equipment_model_seeds = [
            ('كاتربيلر', 'موديل X100'),
            ('كوماتسو', 'موديل HB215'),
            ('بوش', 'موديل صناعي 500'),
            ('مرسيدس', 'مولد كهربائي'),
        ]
        for manufacturer_name, model_name in equipment_model_seeds:
            manufacturer = manufacturer_lookup.get(manufacturer_name)
            if manufacturer:
                self._get_or_update_equipment_model(model_name, manufacturer)
        if self.equipment_df is not None:
            for _, row in self.equipment_df.iterrows():
                manufacturer_name = self._clean_string(row.get('المصـــنع'))
                model_name = self._clean_string(row.get('الموديل'))
                if manufacturer_name and model_name:
                    manufacturer = manufacturer_lookup.get(manufacturer_name)
                    if not manufacturer:
                        manufacturer, _ = Manufacturer.objects.get_or_create(name=manufacturer_name)
                        manufacturer_lookup[manufacturer_name] = manufacturer
                    self._get_or_update_equipment_model(model_name, manufacturer)
        context['equipment_models'] = list(EquipmentModel.objects.all())

        # Functional locations
        functional_location_names = {
            'مستودع الرياض', 'ورشة جدة', 'محطة المنطقة الشرقية', 'مستودع الطائف'
        }
        functional_location_names |= self._extract_unique_values(self.cars_df, ['Functional Location', 'الموقع الوظيفي'])
        for name in functional_location_names:
            FunctionalLocation.objects.get_or_create(name=name)
        context['functional_locations'] = list(FunctionalLocation.objects.all())

        # Rooms
        room_seeds = [
            {'name': 'غرفة العمليات', 'building': 'المبنى الرئيسي', 'floor': '1'},
            {'name': 'غرفة المتابعة', 'building': 'مركز التحكم', 'floor': '2'},
            {'name': 'غرفة الصيانة', 'building': 'الورشة المركزية', 'floor': 'ط'},
        ]
        for room_data in room_seeds:
            Room.objects.get_or_create(
                name=room_data['name'],
                defaults={'building': room_data['building'], 'floor': room_data['floor']},
            )
        if self.cars_df is not None and 'Room' in self.cars_df.columns:
            for room_name in self._extract_unique_values(self.cars_df, ['Room']):
                Room.objects.get_or_create(
                    name=room_name,
                    defaults={'building': 'مبنى الخدمات', 'floor': str(random.randint(1, 4))},
                )
        context['rooms'] = list(Room.objects.all())

        # Locations (for equipment)
        location_names = {'مستودع المعدات الرئيسي', 'مستودع القطع الاحتياطية', 'ساحة التشغيل الشمالية'}
        location_names |= self._extract_unique_values(self.equipment_df, ['الموقع'])
        for name in location_names:
            Location.objects.get_or_create(name=name)
        context['locations'] = list(Location.objects.all())

        # Notification recipients
        recipient_names = {'عبدالله العتيبي', 'سلمان القحطاني', 'مها المطيري', 'نورة السبيعي'}
        recipient_names |= self._extract_unique_values(self.cars_df, ['مستلم الاشعار'])
        recipients = []
        for name in recipient_names:
            email_local = name.replace(' ', '.').replace('أ', 'a').replace('إ', 'i').replace('آ', 'a')
            recipient, _ = NotificationRecipient.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'{email_local.lower()}@example.com',
                    'phone': f'+966{random.randint(500000000, 599999999)}',
                },
            )
            recipients.append(recipient)
        context['notification_recipients'] = recipients

        # Contract types
        contract_names = {'شراء مباشر', 'إيجار طويل', 'إيجار قصير', 'عقد صيانة'}
        contract_names |= self._extract_unique_values(self.cars_df, ['العقد'])
        for name in contract_names:
            ContractType.objects.get_or_create(name=name)
        context['contract_types'] = list(ContractType.objects.all())

        # Activities
        activity_names = {'خدمة ميدانية', 'نقل الركاب', 'التوزيع', 'الدعم التقني'}
        activity_names |= self._extract_unique_values(self.cars_df, ['النشاط'])
        for name in activity_names:
            Activity.objects.get_or_create(name=name)
        context['activities'] = list(Activity.objects.all())

        # Regions
        region_names = ['المنطقة الوسطى', 'المنطقة الغربية', 'المنطقة الشرقية', 'المنطقة الشمالية', 'المنطقة الجنوبية']
        for name in region_names:
            Region.objects.get_or_create(name=name)
        context['regions'] = list(Region.objects.all())

        self.stdout.write(self.style.SUCCESS('تم إنشاء الجداول المرجعية بنجاح.'))
        return context

    def _ensure_dummy_hierarchy(self):
        """Ensure required dummy records exist and return them."""
        dummy_sector, _ = Sector.objects.get_or_create(name='غير محدد', defaults={'is_dummy': True})
        dummy_admin_unit, _ = AdministrativeUnit.objects.get_or_create(
            name='غير محدد',
            defaults={'sector': dummy_sector, 'is_dummy': True},
        )
        if dummy_admin_unit.sector != dummy_sector:
            dummy_admin_unit.sector = dummy_sector
            dummy_admin_unit.is_dummy = True
            dummy_admin_unit.save(update_fields=['sector', 'is_dummy'])

        dummy_division, _ = Division.objects.get_or_create(
            name='غير محدد',
            defaults={'administrative_unit': dummy_admin_unit, 'is_dummy': True},
        )
        if dummy_division.administrative_unit != dummy_admin_unit:
            dummy_division.administrative_unit = dummy_admin_unit
            dummy_division.is_dummy = True
            dummy_division.save(update_fields=['administrative_unit', 'is_dummy'])

        dummy_department, _ = Department.objects.get_or_create(
            name='غير محدد',
            defaults={'division': dummy_division, 'is_dummy': True},
        )
        if dummy_department.division != dummy_division:
            dummy_department.division = dummy_division
            dummy_department.is_dummy = True
            dummy_department.save(update_fields=['division', 'is_dummy'])

        return {
            'sector': dummy_sector,
            'administrative_unit': dummy_admin_unit,
            'division': dummy_division,
            'department': dummy_department,
        }

    # ---------------------------------------------------------------------
    # Data population
    # ---------------------------------------------------------------------

    def populate_cars(self, context):
        """Create car records with associated historical data."""
        self.stdout.write(self.style.WARNING('إضافة سجلات السيارات...'))

        car_records = self._build_car_records()
        if len(car_records) < self.CAR_TARGET_COUNT:
            car_records.extend(self._generate_fallback_car_data(self.CAR_TARGET_COUNT - len(car_records)))
        car_records = car_records[: self.CAR_TARGET_COUNT]

        drivers = context.get('drivers', [])
        car_classes = context.get('car_classes', [])
        car_models = context.get('car_models', [])
        functional_locations = context.get('functional_locations', [])
        rooms = context.get('rooms', [])
        notification_recipients = context.get('notification_recipients', [])
        contract_types = context.get('contract_types', [])
        activities = context.get('activities', [])
        regions = context.get('regions', [])
        departments = context.get('departments', [])

        created_cars = []

        for index, data in enumerate(car_records):
            try:
                department = self._select_random(departments) or context['dummy']['department']
                division = department.division if department else context['dummy']['division']
                administrative_unit = division.administrative_unit if division else context['dummy']['administrative_unit']
                sector = administrative_unit.sector if administrative_unit else context['dummy']['sector']

                fleet_no = self._generate_unique_value(Car, 'fleet_no', data['fleet_no'])
                plate_no_en = self._generate_unique_value(Car, 'plate_no_en', data['plate_no_en'])
                plate_no_ar = self._generate_unique_value(Car, 'plate_no_ar', data['plate_no_ar'])

                selected_model = self._select_random(car_models)
                manufacturer = selected_model.manufacturer if selected_model else self._select_random(list(context['manufacturers'].values()))

                car = Car.objects.create(
                    fleet_no=fleet_no,
                    plate_no_en=plate_no_en,
                    plate_no_ar=plate_no_ar,
                    administrative_unit=administrative_unit,
                    department_code=department,
                    driver_name=self._select_random(drivers),
                    car_class=self._select_random(car_classes),
                    manufacturer=manufacturer,
                    model=selected_model,
                    functional_location=self._select_random(functional_locations),
                    room=self._select_random(rooms),
                    notification_recipient=self._select_random(notification_recipients),
                    contract_type=self._select_random(contract_types),
                    activity=self._select_random(activities),
                    sector=sector,
                    department=department,
                    division=division,
                    ownership_type=self._map_ownership_type(data['ownership_type']),
                    status=self._select_random(['operational', 'new', 'defective', 'under_maintenance']),
                    location_description=data['location_description'],
                    address_details_1=data.get('address_details_1', ''),
                )

                image_path = self._select_random_car_image()
                if image_path and image_path.exists():
                    with image_path.open('rb') as image_file:
                        car.car_image.save(image_path.name, File(image_file), save=True)

                if regions:
                    car.visited_regions.set(random.sample(regions, k=min(len(regions), random.randint(1, 3))))

                license_start, license_end = self._generate_period(index, len(car_records))
                CarLicenseRecord.objects.create(car=car, start_date=license_start, end_date=license_end)

                inspection_start, inspection_end = self._generate_period(index, len(car_records), base_duration=320)
                CarInspectionRecord.objects.create(car=car, start_date=inspection_start, end_date=inspection_end)

                created_cars.append(car)
            except Exception as exc:  # pylint: disable=broad-except
                self.stdout.write(self.style.ERROR(f'تعذّر إنشاء سجل سيارة: {exc}'))

        self.stdout.write(self.style.SUCCESS(f'تم إنشاء {len(created_cars)} سيارة.'))
        return created_cars

    def populate_equipment(self, context):
        """Create equipment records with associated inspections and certificates."""
        self.stdout.write(self.style.WARNING('إضافة سجلات المعدات...'))

        equipment_records = self._build_equipment_records()
        if len(equipment_records) < self.EQUIPMENT_TARGET_COUNT:
            equipment_records.extend(self._generate_fallback_equipment_data(self.EQUIPMENT_TARGET_COUNT - len(equipment_records)))
        equipment_records = equipment_records[: self.EQUIPMENT_TARGET_COUNT]

        equipment_models = context.get('equipment_models', [])
        locations = context.get('locations', [])
        departments = context.get('departments', [])

        created_equipment = []

        for index, data in enumerate(equipment_records):
            try:
                department = self._select_random(departments) or context['dummy']['department']
                division = department.division if department else context['dummy']['division']
                administrative_unit = division.administrative_unit if division else context['dummy']['administrative_unit']
                sector = administrative_unit.sector if administrative_unit else context['dummy']['sector']

                door_no = self._generate_unique_value(Equipment, 'door_no', data['door_no'])
                plate_no = self._generate_unique_value(Equipment, 'plate_no', data['plate_no'])

                selected_model = self._select_random(equipment_models)
                manufacturer = selected_model.manufacturer if selected_model else self._select_random(list(context['manufacturers'].values()))

                equipment = Equipment.objects.create(
                    door_no=door_no,
                    plate_no=plate_no,
                    manufacture_year=data['manufacture_year'],
                    manufacturer=manufacturer,
                    model=selected_model,
                    location=self._select_random(locations),
                    sector=sector,
                    administrative_unit=administrative_unit,
                    department=department,
                    division=division,
                    status=self._map_equipment_status(data['status']),
                )

                image_path = self._select_random_equipment_image()
                if image_path and image_path.exists():
                    with image_path.open('rb') as image_file:
                        equipment.equipment_image.save(image_path.name, File(image_file), save=True)

                license_start, license_end = self._generate_period(index, len(equipment_records))
                EquipmentLicenseRecord.objects.create(equipment=equipment, start_date=license_start, end_date=license_end)

                inspection_start, inspection_end = self._generate_period(index, len(equipment_records), base_duration=280)
                EquipmentInspectionRecord.objects.create(equipment=equipment, start_date=inspection_start, end_date=inspection_end)

                extinguisher_inspection, extinguisher_expiry = self._generate_fire_extinguisher_period(index, len(equipment_records))
                FireExtinguisherInspectionRecord.objects.create(
                    equipment=equipment,
                    inspection_date=extinguisher_inspection,
                    expiry_date=extinguisher_expiry,
                )

                self._attach_calibration_certificates(equipment)

                created_equipment.append(equipment)
            except Exception as exc:  # pylint: disable=broad-except
                self.stdout.write(self.style.ERROR(f'تعذّر إنشاء سجل معدة: {exc}'))

        self.stdout.write(self.style.SUCCESS(f'تم إنشاء {len(created_equipment)} معدة.'))
        return created_equipment

    def create_maintenance_records(self, cars, equipment):
        """Create maintenance history for cars and equipment."""
        self.stdout.write(self.style.WARNING('إضافة سجلات الصيانة...'))

        descriptions_cars = ['تغيير الزيت', 'فحص المكابح', 'صيانة المحرك', 'فحص الإطارات', 'صيانة نظام التبريد']
        descriptions_equipment = ['فحص الهيدروليك', 'صيانة المحرك', 'فحص الأنظمة الكهربائية', 'تنظيف وفحص', 'معايرة الأجهزة']

        created_count = 0

        for car in cars:
            for _ in range(random.randint(2, 3)):
                maintenance_date = self._generate_random_date(2020, 2024)
                restoration_date = maintenance_date + timedelta(days=random.randint(1, 20))
                Maintenance.objects.create(
                    content_object=car,
                    maintenance_date=maintenance_date,
                    restoration_date=restoration_date,
                    cost=self._random_decimal(250, 4500),
                    description=f'صيانة دورية للسيارة {car.fleet_no} - {random.choice(descriptions_cars)}',
                )
                created_count += 1

        for equip in equipment:
            for _ in range(random.randint(1, 2)):
                maintenance_date = self._generate_random_date(2020, 2024)
                restoration_date = maintenance_date + timedelta(days=random.randint(1, 12))
                Maintenance.objects.create(
                    content_object=equip,
                    maintenance_date=maintenance_date,
                    restoration_date=restoration_date,
                    cost=self._random_decimal(600, 8500),
                    description=f'صيانة دورية للمعدة {equip.door_no} - {random.choice(descriptions_equipment)}',
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'تم إنشاء {created_count} سجل صيانة.'))

    # ---------------------------------------------------------------------
    # Data builders
    # ---------------------------------------------------------------------

    def _build_car_records(self):
        """Extract car data rows from Excel."""
        records = []
        if self.cars_df is None:
            return records

        for _, row in self.cars_df.iterrows():
            fleet_no = self._clean_string(row.get('Fleet No')) or f'FLEET{random.randint(1000, 9999)}'
            plate_no_en = self._clean_string(row.get('Plate No(EN)')) or f'EN{random.randint(1000, 9999)}'
            plate_no_ar = self._clean_string(row.get('Plate No(AR)')) or f'ع-{random.randint(1000, 9999)}'
            location_description = self._clean_string(row.get('Location Description')) or 'موقف المركبات الرئيسي'
            address_details = self._clean_string(row.get('Address Details 1')) or ''
            ownership_type = self._clean_string(row.get('Owned/Leased')) or 'owned'

            records.append(
                {
                    'fleet_no': fleet_no,
                    'plate_no_en': plate_no_en,
                    'plate_no_ar': plate_no_ar,
                    'location_description': location_description,
                    'address_details_1': address_details,
                    'ownership_type': ownership_type,
                }
            )
        return records

    def _build_equipment_records(self):
        """Extract equipment data rows from Excel."""
        records = []
        if self.equipment_df is None:
            return records

        for _, row in self.equipment_df.iterrows():
            door_no = self._clean_string(row.get('رقم الباب')) or f'DOOR{random.randint(1000, 9999)}'
            plate_no = self._clean_string(row.get('رقم اللوحة')) or f'PLATE{random.randint(1000, 9999)}'
            manufacture_year = self._safe_int(row.get('سنةالصنع'), random.randint(2015, 2024))
            status = self._clean_string(row.get('حاله المعدة')) or 'operational'

            records.append(
                {
                    'door_no': door_no,
                    'plate_no': plate_no,
                    'manufacture_year': manufacture_year,
                    'status': status,
                }
            )
        return records

    def _generate_fallback_car_data(self, count):
        """Generate fallback car data when Excel does not provide enough rows."""
        fallback = []
        prefixes = ['بلدية', 'خدمة', 'نقل', 'طوارئ']
        for idx in range(count):
            fallback.append(
                {
                    'fleet_no': f'FLEET-{idx + 1:03d}',
                    'plate_no_en': f'EN-{idx + 1:04d}',
                    'plate_no_ar': f'ع ج {1000 + idx}',
                    'location_description': f'موقف {random.choice(prefixes)} رقم {idx + 1}',
                    'address_details_1': 'حي العليا - الرياض',
                    'ownership_type': random.choice(['owned', 'leased', 'rental']),
                }
            )
        return fallback

    def _generate_fallback_equipment_data(self, count):
        """Generate fallback equipment data when Excel does not provide enough rows."""
        fallback = []
        categories = ['رافعة', 'مولد', 'مضخة', 'ضاغط']
        for idx in range(count):
            fallback.append(
                {
                    'door_no': f'DR-{idx + 101:03d}',
                    'plate_no': f'EQ-{idx + 1:04d}',
                    'manufacture_year': random.randint(2016, 2023),
                    'status': random.choice(['operational', 'new', 'under_maintenance']),
                }
            )
        return fallback

    # ---------------------------------------------------------------------
    # Utility helpers
    # ---------------------------------------------------------------------

    def _select_random(self, sequence):
        return random.choice(sequence) if sequence else None

    def _generate_random_date(self, start_year, end_year):
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        delta = (end_date - start_date).days
        return start_date + timedelta(days=random.randint(0, delta))

    def _generate_period(self, index, total, base_duration=365):
        """Generate start/end dates ensuring a mix of expired, near expiry, and active periods."""
        today = date.today()
        expired_threshold = max(1, total // 4)
        near_expiry_threshold = max(1, total // 4)

        if index < expired_threshold:
            end_date = today - timedelta(days=random.randint(1, 60))
        elif index < expired_threshold + near_expiry_threshold:
            end_date = today + timedelta(days=random.randint(5, 45))
        else:
            end_date = today + timedelta(days=random.randint(60, 180))

        start_date = end_date - timedelta(days=random.randint(base_duration - 120, base_duration))
        if start_date >= end_date:
            start_date = end_date - timedelta(days=180)
        return start_date, end_date

    def _generate_fire_extinguisher_period(self, index, total):
        today = date.today()
        if index % 3 == 0:
            expiry_date = today - timedelta(days=random.randint(5, 40))
        elif index % 3 == 1:
            expiry_date = today + timedelta(days=random.randint(10, 40))
        else:
            expiry_date = today + timedelta(days=random.randint(60, 160))
        inspection_date = expiry_date - timedelta(days=random.randint(200, 320))
        return inspection_date, expiry_date

    def _random_decimal(self, minimum, maximum):
        return Decimal(random.uniform(minimum, maximum)).quantize(Decimal('0.01'))

    def _generate_unique_value(self, model, field_name, base_value):
        """Ensure unique values for fields with unique constraints."""
        value = base_value
        counter = 1
        lookup = {field_name: value}
        while model.objects.filter(**lookup).exists():
            value = f'{base_value}-{counter}'
            lookup[field_name] = value
            counter += 1
        return value

    def _select_random_car_image(self):
        if not self.car_images_dir.exists():
            return None
        subfolders = [path for path in self.car_images_dir.iterdir() if path.is_dir()]
        if not subfolders:
            return None
        folder = random.choice(subfolders)
        images = [path for path in folder.iterdir() if path.suffix.lower() in {'.jpg', '.jpeg', '.png'}]
        return random.choice(images) if images else None

    def _select_random_equipment_image(self):
        if not self.equipment_images_dir.exists():
            return None
        images = [path for path in self.equipment_images_dir.iterdir() if path.suffix.lower() in {'.jpg', '.jpeg', '.png'}]
        return random.choice(images) if images else None

    def _attach_calibration_certificates(self, equipment):
        if not self.certificates_dir.exists():
            return
        certificate_files = [
            path for path in self.certificates_dir.iterdir() if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.pdf'}
        ]
        if not certificate_files:
            return
        for certificate_path in random.sample(certificate_files, k=min(len(certificate_files), random.randint(1, 2))):
            with certificate_path.open('rb') as certificate_file:
                CalibrationCertificateImage.objects.create(
                    equipment=equipment,
                    image=File(certificate_file, name=certificate_path.name),
                )

    def _get_or_update_car_model(self, name, manufacturer, year=None):
        """Create a car model or update its manufacturer/year if it already exists."""
        defaults = {'manufacturer': manufacturer}
        if year:
            defaults['year'] = year
        car_model, created = CarModel.objects.get_or_create(name=name, defaults=defaults)

        updates = {}
        if manufacturer and car_model.manufacturer_id != manufacturer.id:
            updates['manufacturer'] = manufacturer
        if year and (car_model.year or 0) != year:
            updates['year'] = year

        if updates:
            for field, value in updates.items():
                setattr(car_model, field, value)
            car_model.save(update_fields=list(updates.keys()))

        return car_model

    def _get_or_update_equipment_model(self, name, manufacturer):
        """Create an equipment model or update its manufacturer if needed."""
        equipment_model, created = EquipmentModel.objects.get_or_create(
            name=name,
            defaults={'manufacturer': manufacturer},
        )
        if manufacturer and equipment_model.manufacturer_id != manufacturer.id:
            equipment_model.manufacturer = manufacturer
            equipment_model.save(update_fields=['manufacturer'])
        return equipment_model

    def _extract_unique_values(self, dataframe, columns):
        values = set()
        if dataframe is None:
            return values
        for column in columns:
            if column in dataframe.columns:
                column_values = dataframe[column].dropna().astype(str).str.strip()
                values.update(value for value in column_values if value and value.lower() != 'nan')
        return values

    def _clean_string(self, value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip()
        return text if text and text.lower() != 'nan' else None

    def _safe_int(self, value, default=None):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _map_ownership_type(self, ownership_str):
        if not ownership_str:
            return 'owned'
        normalized = ownership_str.strip().lower()
        mapping = {
            'owned': 'owned',
            'مملوكة': 'owned',
            'مملوكة بالكامل': 'owned',
            'leased': 'leased_regular',
            'إيجار': 'leased_regular',
            'leased - regular': 'leased_regular',
            'leased_non_regular': 'leased_non_regular',
            'non regular': 'leased_non_regular',
            'leased - non regular': 'leased_non_regular',
            'rental': 'leased_non_regular',
            'leased_emp_24hrs': 'leased_emp_24hrs',
            'leased - emp 24hrs': 'leased_emp_24hrs',
            'emp 24hrs': 'leased_emp_24hrs',
        }
        return mapping.get(normalized, 'owned')

    def _map_equipment_status(self, status_str):
        if not status_str:
            return 'operational'
        normalized = status_str.strip().lower()
        mapping = {
            'عاملة': 'operational',
            'operational': 'operational',
            'جديدة': 'new',
            'new': 'new',
            'معطلة': 'defective',
            'defective': 'defective',
            'مكهنة': 'defective',
            'تحت الصيانة': 'under_maintenance',
            'under maintenance': 'under_maintenance',
            'under_maintenance': 'under_maintenance',
        }
        return mapping.get(normalized, 'operational')


