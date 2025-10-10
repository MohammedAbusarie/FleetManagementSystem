# Database Population Script

This Django management command script (`populate_dummy_data.py`) clears the database and populates it with realistic dummy data based on the Excel files and images in the `dummy_media` folder.

## Features

- **Complete Database Reset**: Clears all existing data without conflicts
- **Excel Data Integration**: Reads data from Arabic Excel files for cars and equipment
- **Random Image Assignment**: Assigns random images from the provided image folders
- **Meaningful Dates**: Generates realistic dates for licenses, inspections, and maintenance records
- **Maintenance Records**: Creates maintenance history for both cars and equipment
- **Calibration Certificates**: Adds calibration certificates for equipment
- **Arabic Language Support**: All data is in Arabic as per project requirements

## Usage

### Full Population (Clear + Populate)
```bash
python manage.py populate_dummy_data
```

### Clear Database Only
```bash
python manage.py populate_dummy_data --clear-only
```

## Data Generated

The script creates:

1. **Lookup Tables**: All DDL tables (departments, manufacturers, models, etc.)
2. **Cars**: 355 cars with complete information from Excel data
3. **Equipment**: 144 equipment items with complete information from Excel data
4. **Maintenance Records**: 1300+ maintenance records with realistic dates and costs
5. **Images**: Random car images from 7 different vehicle types
6. **Calibration Certificates**: Random certificates for equipment

## Data Sources

- **Cars Excel**: `dummy_media/سيارات المدينة.xlsx` (355 records)
- **Equipment Excel**: `dummy_media/نسخة من جدول المعدات.xlsx` (144 records)
- **Car Images**: `dummy_media/cars/` (7 folders with vehicle images)
- **Equipment Images**: `dummy_media/equipments/` (equipment photos)
- **Certificates**: `dummy_media/certificates/` (calibration certificates)

## Generated Data Details

### Cars
- Fleet numbers, plate numbers (Arabic & English)
- Administrative units, departments, drivers
- Car classes, manufacturers, models
- Functional locations, rooms
- License and inspection dates
- Random images from car folders
- Visited regions

### Equipment
- Door numbers, plate numbers
- Manufacturers, models, locations, sectors
- Manufacture years, status
- License and inspection dates
- Random equipment images
- Calibration certificates

### Maintenance Records
- Realistic maintenance dates (2020-2024)
- Restoration dates (1-30 days after maintenance)
- Costs (100-5000 for cars, 500-10000 for equipment)
- Arabic descriptions for maintenance types

## Error Handling

The script handles:
- Duplicate entries in Excel data
- Invalid data types (e.g., non-numeric years)
- Missing images or files
- Unicode encoding issues
- Database constraint violations

## Requirements

- Django project with inventory app
- pandas library for Excel reading
- PIL/Pillow for image handling
- PostgreSQL database (as per project setup)

