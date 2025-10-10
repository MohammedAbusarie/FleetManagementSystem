# Fleet Management System

A comprehensive fleet and equipment management system built with Django, featuring bilingual support (Arabic/English) for managing vehicles, equipment, and maintenance records.

## Features

### Core Functionality
- **Vehicle Management (City Fleet)**: Complete management of fleet vehicles with detailed information
- **Equipment Management**: Track and manage equipment with calibration certificates
- **Generic Tables (DDL)**: Manage all dropdown list data including departments, manufacturers, models, locations, etc.
- **Maintenance Tracking**: Record and track maintenance activities for both vehicles and equipment
- **Inspection Alerts**: Dashboard alerts for upcoming/expired inspections
- **Image Upload**: Support for vehicle images, equipment images, and multiple calibration certificates
- **Search & Filter**: Advanced search functionality across all entities
- **Bilingual Support**: Full Arabic and English language support

### Database Schema

#### Cars (City Fleet) Table
- Fleet Number (required)
- Plate Number (English & Arabic, required)
- Department Code
- Driver Name
- Car Class
- Manufacturer
- Model
- Functional Location
- Ownership Type (Owned/Leased)
- Employment Type (Regular, Non-regular, Employee 24hrs)
- Room
- Location Description (required)
- Address Details
- Notification Recipient
- Contract Type (Agencies, Management Purchase)
- Activity
- Vehicle Registration Start/End Dates
- Annual Inspection Start/End Dates
- Vehicle Image
- Visited Regions (multiple regions)

#### Equipment Table
- Door Number (required)
- Manufacturing Year (2000-2030)
- Manufacturer
- Model
- Location
- Sector
- Plate Number (required)
- Equipment Status (Operational, New, Defective) - 3 status colors
- Calibration Certificates (multiple images)
- Equipment Image
- Equipment Registration Start/End Dates
- Annual Inspection Start/End Dates

#### Maintenance Table
- Linked to both Cars and Equipment
- Maintenance Date (nullable)
- Recovery Date (nullable)
- Maintenance Cost (nullable)

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Icons**: Bootstrap Icons
- **Languages**: Python 3.11

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- pip3

### Step 1: Clone or Extract the Project
```bash
cd /path/to/fleet_management
```

### Step 2: Install Dependencies
```bash
pip3 install django psycopg2-binary python-dotenv django-crispy-forms crispy-bootstrap5 pillow
```

### Step 3: Set Up PostgreSQL Database
```bash
# Start PostgreSQL service
sudo service postgresql start

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE fleet_management_db;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fleet_management_db TO postgres;"
sudo -u postgres psql -c "ALTER DATABASE fleet_management_db OWNER TO postgres;"
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root (optional, defaults are provided):
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*
DB_NAME=fleet_management_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
TIME_ZONE=Asia/Riyadh
```

### Step 5: Run Migrations
```bash
python3.11 manage.py makemigrations
python3.11 manage.py migrate
```

### Step 6: Create Admin User and Seed Data
```bash
python3.11 manage.py setup_initial_data
```

This command will:
- Create an admin user (username: `admin`, password: `admin123`)
- Seed all generic tables with sample data
- Create departments, manufacturers, models, locations, etc.

### Step 7: Run the Development Server
```bash
python3.11 manage.py runserver 0.0.0.0:8000
```

Access the application at: `http://localhost:8000`

## Usage

### Login
- **Username**: `admin`
- **Password**: `admin123`

### Dashboard
The dashboard displays:
- Quick statistics for cars and equipment
- Alerts for vehicles with approaching/expired inspections
- Alerts for equipment with approaching/expired inspections
- Configurable alert timeframe (7, 15, 30, 60, 90 days)

### Managing Cars
1. Navigate to **Cars** from the sidebar
2. Click **Add New Car** to create a new vehicle record
3. Fill in all required fields (marked with *)
4. Upload a vehicle image (optional)
5. Select multiple regions the vehicle has visited
6. Click **Save** to create the record

**Search & Filter**:
- Search by Fleet No, Plate No (EN), Plate No (AR), or Manufacturer
- Select the search field using radio buttons
- Click **Search** to filter results

### Managing Equipment
1. Navigate to **Equipment** from the sidebar
2. Click **Add New Equipment** to create a new equipment record
3. Fill in all required fields
4. Upload equipment image and multiple calibration certificates
5. Select equipment status (Operational, New, Defective)
6. Click **Save** to create the record

**Search & Filter**:
- Search by Door No, Plate No, or Manufacturer
- Select the search field using radio buttons
- Click **Search** to filter results

### Managing Generic Tables (DDL)
1. Navigate to **Generic Tables** from the sidebar
2. Select the table you want to manage (Department, Driver, Manufacturer, etc.)
3. Click **Add New** to create a new record
4. Enter Name (English) and Name (Arabic)
5. Click **Save**

**Available Generic Tables**:
- Department
- Driver
- CarClass
- Manufacturer
- CarModel
- EquipmentModel
- FunctionalLocation
- Room
- Location
- Sector
- NotificationRecipient
- ContractType
- Activity
- Region

### Image Storage
- Images are stored locally in the `media/` directory
- Vehicle images: `media/cars/`
- Equipment images: `media/equipment/`
- Calibration certificates: `media/calibration_certificates/`

**Note**: As per your requirements, S3 storage is NOT used. All images are stored locally on the server.

## Project Structure

```
fleet_management/
├── fleet_management/          # Project settings
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── inventory/                # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── forms.py             # Django forms
│   ├── urls.py              # App URL configuration
│   ├── admin.py             # Django admin configuration
│   └── management/          # Custom management commands
│       └── commands/
│           └── setup_initial_data.py
├── templates/               # HTML templates
│   ├── base.html           # Base template with sidebar
│   └── inventory/          # App-specific templates
│       ├── login.html
│       ├── dashboard.html
│       ├── car_list.html
│       ├── car_form.html
│       ├── equipment_list.html
│       ├── equipment_form.html
│       └── generic_tables.html
├── static/                  # Static files (CSS, JS, images)
├── media/                   # Uploaded files
├── .env                     # Environment variables
├── manage.py               # Django management script
└── README.md               # This file
```

## Database Schema Details

### DDL Tables (Generic Tables)
All DDL tables follow the same structure:
- `id`: Primary key (auto-increment)
- `name`: English name (required, max 200 characters)
- `name_ar`: Arabic name (optional, max 200 characters)
- `created_at`: Timestamp (auto-generated)
- `updated_at`: Timestamp (auto-updated)

### Car Model
- All fields from the requirements document
- Foreign keys to DDL tables (Department, Driver, Manufacturer, etc.)
- Many-to-many relationship with Region (visited regions)
- Image field for vehicle photo
- Date fields for registration and inspection tracking

### Equipment Model
- All fields from the requirements document
- Foreign keys to DDL tables (Manufacturer, Model, Location, Sector)
- Status field with 3 choices (operational, new, defective)
- Image field for equipment photo
- Separate model for calibration certificates (one-to-many relationship)

### Maintenance Model
- Generic foreign keys to both Car and Equipment
- Nullable date and cost fields as specified
- Tracks maintenance history for both vehicles and equipment

## Security Features

- CSRF protection enabled
- Password hashing for user authentication
- Session security (HTTP-only cookies)
- SQL injection protection (Django ORM)
- XSS protection (template auto-escaping)
- Login required for all pages (except login page)

## Customization

### Changing the Default Language
Edit `fleet_management/settings.py`:
```python
LANGUAGE_CODE = 'ar'  # Change to 'en' for English
```

### Changing the Time Zone
Edit `fleet_management/settings.py`:
```python
TIME_ZONE = 'Asia/Riyadh'  # Change to your timezone
```

### Adding New Fields
1. Update the model in `inventory/models.py`
2. Update the form in `inventory/forms.py`
3. Run migrations:
   ```bash
   python3.11 manage.py makemigrations
   python3.11 manage.py migrate
   ```

## Production Deployment

For production deployment, consider:

1. **Set DEBUG to False**:
   ```python
   DEBUG = False
   ```

2. **Use a Production Database**:
   - Configure PostgreSQL with proper credentials
   - Use environment variables for sensitive data

3. **Use a Production Web Server**:
   - Gunicorn or uWSGI for Django
   - Nginx as reverse proxy

4. **Collect Static Files**:
   ```bash
   python3.11 manage.py collectstatic
   ```

5. **Set Proper ALLOWED_HOSTS**:
   ```python
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   ```

6. **Enable HTTPS**:
   - Use SSL certificates
   - Set `SECURE_SSL_REDIRECT = True`

7. **Regular Backups**:
   - Database backups
   - Media files backups

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running: `sudo service postgresql start`
- Check database credentials in `.env` file
- Verify database exists: `sudo -u postgres psql -l`

### Migration Errors
- Delete migration files (except `__init__.py`) and recreate:
  ```bash
  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
  python3.11 manage.py makemigrations
  python3.11 manage.py migrate
  ```

### Static Files Not Loading
- Run `python3.11 manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` in settings

### Images Not Displaying
- Check `MEDIA_ROOT` and `MEDIA_URL` in settings
- Ensure the `media/` directory has proper permissions
- Verify the URL configuration includes media files

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django documentation: https://docs.djangoproject.com/
3. Check PostgreSQL documentation: https://www.postgresql.org/docs/

## License

This project is proprietary software developed for internal use.

## Credits

Developed using:
- Django Web Framework
- Bootstrap 5
- Bootstrap Icons
- PostgreSQL Database
- Python 3.11

