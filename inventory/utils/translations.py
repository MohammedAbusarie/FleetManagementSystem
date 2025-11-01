"""Centralized translation utilities - consolidates all Arabic translations"""

# Model translations (consolidates from translation_utils, error_handlers, templatetags)
MODEL_TRANSLATIONS = {
    'Car': 'سيارة',
    'Equipment': 'معدة',
    'Maintenance': 'صيانة',
    'CalibrationCertificateImage': 'شهادة معايرة',
    'AdministrativeUnit': 'إدارة',
    'Department': 'قسم',
    'Driver': 'سائق',
    'CarClass': 'فئة السيارة',
    'Manufacturer': 'شركة مصنعة',
    'CarModel': 'موديل سيارة',
    'EquipmentModel': 'موديل معدة',
    'FunctionalLocation': 'موقع وظيفي',
    'Room': 'غرفة',
    'Location': 'موقع',
    'Sector': 'قطاع',
    'Division': 'دائرة',
    'NotificationRecipient': 'مستلم إشعار',
    'ContractType': 'نوع عقد',
    'Activity': 'نشاط',
    'Region': 'منطقة',
}

# Verbose (plural) translations
MODEL_TRANSLATIONS_PLURAL = {
    'AdministrativeUnit': 'الإدارات',
    'Department': 'الأقسام',
    'Driver': 'السائقين',
    'CarClass': 'فئات السيارات',
    'Manufacturer': 'الشركات المصنعة',
    'CarModel': 'موديلات السيارات',
    'EquipmentModel': 'موديلات المعدات',
    'FunctionalLocation': 'المواقع الوظيفية',
    'Room': 'الغرف',
    'Location': 'المواقع',
    'Sector': 'القطاعات',
    'Division': 'الدوائر',
    'NotificationRecipient': 'مستلمي الإشعارات',
    'ContractType': 'أنواع العقود',
    'Activity': 'الأنشطة',
    'Region': 'المناطق',
    'Car': 'السيارات',
    'Equipment': 'المعدات',
    'Maintenance': 'سجلات الصيانة',
    'CalibrationCertificateImage': 'شهادات المعايرة',
}

# Operation translations
OPERATION_TRANSLATIONS = {
    'create': 'إنشاء',
    'update': 'تحديث',
    'delete': 'حذف',
    'add': 'إضافة',
    'edit': 'تعديل',
    'view': 'عرض',
    'list': 'قائمة',
    'detail': 'تفاصيل',
    'search': 'بحث',
    'save': 'حفظ',
    'cancel': 'إلغاء',
}

# Message templates
MESSAGE_TEMPLATES = {
    'create_success': 'تم {operation} {model} بنجاح!',
    'update_success': 'تم {operation} {model} بنجاح!',
    'delete_success': 'تم {operation} {model} بنجاح!',
    'create_error': 'حدث خطأ أثناء {operation} {model}',
    'update_error': 'حدث خطأ أثناء {operation} {model}',
    'delete_error': 'حدث خطأ أثناء {operation} {model}',
    'not_found': 'لم يتم العثور على {model}',
    'validation_error': 'يرجى تصحيح الأخطاء أدناه',
}


def get_model_arabic_name(model_name, plural=False):
    """Get Arabic name for a model (singular or plural)"""
    if plural:
        return MODEL_TRANSLATIONS_PLURAL.get(model_name, model_name)
    return MODEL_TRANSLATIONS.get(model_name, model_name)


def get_operation_arabic_name(operation):
    """Get Arabic name for an operation"""
    return OPERATION_TRANSLATIONS.get(operation, operation)


def get_message_template(template_key, model_name=None, operation=None):
    """Get a message template with Arabic translations"""
    template = MESSAGE_TEMPLATES.get(template_key, '')
    if model_name:
        model_arabic = get_model_arabic_name(model_name)
        template = template.replace('{model}', model_arabic)
    if operation:
        operation_arabic = get_operation_arabic_name(operation)
        template = template.replace('{operation}', operation_arabic)
    return template


# Maintain backward compatibility
get_verbose_model_translations = lambda: MODEL_TRANSLATIONS_PLURAL
get_contextual_action_label = lambda action, model_name: f"{get_operation_arabic_name(action)} {get_model_arabic_name(model_name)}"
