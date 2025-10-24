# Fleet Management System - Quick Start Guide

> **📚 For detailed architecture and development patterns, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)**

## What You Need
- Python 3.11 or higher
- PostgreSQL database
- Windows, Mac, or Linux computer

## Installation Steps (5 Minutes)

### 1. Extract the Project
Extract the `fleet_management_system.rar` file to your desired location.

### 2. Install Python Dependencies
Open terminal/command prompt in the project folder and run:
```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL Database

**On Windows:**
1. Install PostgreSQL from https://www.postgresql.org/download/windows/
2. Open pgAdmin or SQL Shell
3. Run these commands:
```sql
CREATE DATABASE fleet_management_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE fleet_management_db TO postgres;
```

**On Linux/Mac:**
```bash
sudo service postgresql start
sudo -u postgres psql -c "CREATE DATABASE fleet_management_db;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Create Admin User and Load Sample Data
```bash
python manage.py setup_initial_data
```

This creates:
- Admin username: `admin`
- Admin password: `admin123`
- Sample data for all dropdown lists

### 6. Start the Server
```bash
python manage.py runserver
```

### 7. Open in Browser
Go to: http://localhost:8000

Login with:
- Username: `admin`
- Password: `admin123`

## That's It! 🎉

You now have a fully functional Fleet Management System!

## What's Included

✅ **Vehicle Management** - Track all fleet vehicles with detailed information
✅ **Equipment Management** - Manage equipment with calibration certificates
✅ **Maintenance Tracking** - Record maintenance for vehicles and equipment
✅ **Generic Tables** - Manage all dropdown lists (departments, manufacturers, etc.)
✅ **Dashboard** - View alerts for upcoming inspections
✅ **Search & Filter** - Find vehicles and equipment quickly
✅ **Image Upload** - Store photos of vehicles and equipment
✅ **Bilingual Support** - Arabic and English interface

## Quick Tips

### Change Admin Password
1. Login as admin
2. Go to: http://localhost:8000/admin/
3. Click on "Users" → "admin" → Change password

### Add a New Car
1. Click "Cars" in the sidebar
2. Click "Add New Car"
3. Fill in the required fields (marked with *)
4. Upload a car image (optional)
5. Click "Save"

### Add New Equipment
1. Click "Equipment" in the sidebar
2. Click "Add New Equipment"
3. Fill in the required fields
4. Upload equipment image and calibration certificates
5. Click "Save"

### Manage Dropdown Lists
1. Click "Generic Tables" in the sidebar
2. Select the table you want to manage (e.g., Manufacturer)
3. Add, edit, or delete records as needed

## Troubleshooting

**Problem: Can't connect to database**
- Make sure PostgreSQL is running
- Check database credentials in `.env` file
- Verify database exists: `psql -l` (Linux/Mac) or use pgAdmin (Windows)

**Problem: Static files not loading**
- Run: `python manage.py collectstatic`

**Problem: Images not displaying**
- Check that `media/` folder exists
- Verify file permissions

**Problem: Migration errors**
- Delete all migration files except `__init__.py` in `inventory/migrations/`
- Run: `python manage.py makemigrations`
- Run: `python manage.py migrate`

## Need Help?

1. Check the full `README.md` for detailed documentation
2. Check `DEPLOYMENT.md` for production deployment guide
3. Continue the chat for modifications and support

## Default Credentials

**Admin User:**
- Username: `admin`
- Password: `admin123`

**Database:**
- Database: `fleet_management_db`
- User: `postgres`
- Password: `postgres`

⚠️ **Important:** Change these default credentials in production!

## File Structure

```
fleet_management/
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── README.md             # Full documentation
├── QUICKSTART.md         # This file
├── DEPLOYMENT.md         # Production deployment guide
├── .env                  # Environment variables
├── fleet_management/     # Project settings
├── inventory/            # Main application
├── templates/            # HTML templates
├── static/              # CSS, JS, images
└── media/               # Uploaded files
```

## Next Steps

1. **Customize the system** - Add your own departments, manufacturers, locations
2. **Add real data** - Start adding your actual vehicles and equipment
3. **Configure settings** - Update `.env` file with your preferences
4. **Deploy to production** - Follow `DEPLOYMENT.md` when ready

## Support

For modifications or questions, continue the chat and I'll help you with:
- Adding new features
- Customizing the interface
- Fixing issues
- Database modifications
- Any other changes you need

Enjoy your Fleet Management System! 🚗🔧

