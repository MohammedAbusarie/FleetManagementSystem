"""Application-level constants"""

# Car choices
CAR_STATUS_CHOICES = [
    ('operational', 'عاملة'),
    ('new', 'جديدة'),
    ('defective', 'معطلة'),
    ('under_maintenance', 'تحت الصيانة'),
]

CAR_OWNERSHIP_CHOICES = [
    ('owned', 'Owned'),
    ('leased_regular', 'Leased - Regular'),
    ('leased_non_regular', 'Leased - Non Regular'),
    ('leased_emp_24hrs', 'Leased - Emp 24hrs'),
]

# Equipment choices
EQUIPMENT_STATUS_CHOICES = [
    ('operational', 'عاملة'),
    ('new', 'جديدة'),
    ('defective', 'معطلة'),
    ('under_maintenance', 'تحت الصيانة'),
]

# Pagination
DEFAULT_PAGE_SIZE = 20

# Date formats
ARABIC_DATE_FORMAT = '%Y-%m-%d'
